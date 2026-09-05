import logging
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import select, func, text
from sqlalchemy.orm import Session

from app.models.payment import Payment
from app.models.payment_attempt import PaymentAttempt
from app.models.recovery_case import RecoveryCase
from app.models.recovery_action import RecoveryAction
from app.models.recovery_measurement import RecoveryMeasurement
from app.models.webhook_event import WebhookEvent

logger = logging.getLogger(__name__)

class MeasurementService:
    @staticmethod
    def process_success_event(session: Session, event: WebhookEvent) -> RecoveryMeasurement | None:
        """
        Process a payment success event and attribute it to a recovery action if eligible.
        """
        payload = event.payload or {}
        
        # 1. Resolve Identity
        # Different events might have different paths to entity ID
        payment_entity = payload.get("payload", {}).get("payment", {}).get("entity", {})
        order_entity = payload.get("payload", {}).get("order", {}).get("entity", {})
        
        razorpay_order_id = payment_entity.get("order_id") or order_entity.get("id")
        razorpay_payment_id = payment_entity.get("id")
        
        if not razorpay_order_id and not razorpay_payment_id:
            logger.debug(f"Webhook {event.id} missing order_id and payment_id in payload.")
            return None
            
        # 2. Find Payment
        payment = None
        if razorpay_order_id:
            payment = session.execute(
                select(Payment).where(Payment.razorpay_order_id == razorpay_order_id)
            ).scalar_one_or_none()
            
        if not payment and razorpay_payment_id:
            attempt = session.execute(
                select(PaymentAttempt).where(PaymentAttempt.razorpay_payment_id == razorpay_payment_id)
            ).scalar_one_or_none()
            if attempt:
                payment = attempt.payment
                
        if not payment:
            logger.debug(f"No corresponding Payment found for webhook {event.id}")
            return None
            
        # 3. Find Active Recovery Case
        case = session.execute(
            select(RecoveryCase).where(
                RecoveryCase.payment_id == payment.id,
            )
        ).scalar_one_or_none()
        
        if not case:
            logger.debug(f"No RecoveryCase found for payment {payment.id}")
            return None
            
        # Check idempotency
        if case.status == "RECOVERED":
            logger.info(f"RecoveryCase {case.id} already marked RECOVERED. Ignoring duplicate success.")
            return None
            
        # 4. Extract Event Timestamp & Revenue
        # Razorpay created_at is an epoch timestamp
        created_at_epoch = payment_entity.get("created_at") or order_entity.get("created_at")
        if created_at_epoch:
            occurred_at = datetime.fromtimestamp(created_at_epoch, tz=timezone.utc)
        else:
            occurred_at = event.received_at
            if not occurred_at.tzinfo:
                occurred_at = occurred_at.replace(tzinfo=timezone.utc)
                
        # Recovered revenue
        # Prefer payment_entity amount if available, else order amount_paid
        if "amount" in payment_entity:
            recovered_revenue = payment_entity["amount"]
        elif "amount_paid" in order_entity:
            recovered_revenue = order_entity["amount_paid"]
        else:
            recovered_revenue = payment.amount # Fallback to original payment amount if verified cannot be found
            
        # 5. Find eligible RecoveryAction
        action = session.execute(
            select(RecoveryAction).where(
                RecoveryAction.recovery_case_id == case.id,
                RecoveryAction.status == "EXECUTED",
                RecoveryAction.executed_at <= occurred_at
            ).order_by(RecoveryAction.executed_at.desc())
        ).scalars().first()
        
        attribution_status = "UNATTRIBUTED_SUCCESS"
        attribution_basis = {}
        
        if action and action.executed_at:
            action_tz = action.executed_at
            if not action_tz.tzinfo:
                action_tz = action_tz.replace(tzinfo=timezone.utc)
                
            time_diff = occurred_at - action_tz
            
            # 24 hour attribution window rule
            if timedelta(0) <= time_diff <= timedelta(hours=24):
                attribution_status = "ATTRIBUTED"
                attribution_basis = {
                    "action_id": str(action.id),
                    "action_type": action.action_type
                }
                
        # 6. Time to recovery
        case_created_tz = case.created_at
        if not case_created_tz.tzinfo:
            case_created_tz = case_created_tz.replace(tzinfo=timezone.utc)
        time_to_recovery_seconds = int((occurred_at - case_created_tz).total_seconds())
        if time_to_recovery_seconds < 0:
            time_to_recovery_seconds = 0
            
        # 7. Persist Measurement
        measurement = RecoveryMeasurement(
            recovery_case_id=case.id,
            attribution_status=attribution_status,
            verified_recovered_amount=recovered_revenue,
            currency=payment.currency,
            resolution_webhook_event_id=event.id,
            time_to_recovery_seconds=time_to_recovery_seconds,
            attribution_basis=attribution_basis,
            measured_at=datetime.now(timezone.utc)
        )
        
        session.add(measurement)
        
        # 8. Update Case
        case.status = "RECOVERED"
        case.closed_at = occurred_at
        
        session.flush()
        
        logger.info(f"Measured recovery for case {case.id} with status {attribution_status}")
        return measurement

class MetricsService:
    @staticmethod
    def get_aggregate_metrics(session: Session):
        total_failed_attempts = session.scalar(select(func.count(PaymentAttempt.id)).where(PaymentAttempt.status == "FAILED")) or 0
        total_cases = session.scalar(select(func.count(RecoveryCase.id))) or 0
        
        recovered_cases = session.scalar(
            select(func.count(RecoveryCase.id)).where(RecoveryCase.status == "RECOVERED")
        ) or 0
        
        recovery_rate = (recovered_cases / total_cases * 100) if total_cases > 0 else 0.0
        
        revenue_at_risk = session.scalar(
            select(func.sum(RecoveryCase.revenue_at_risk))
        ) or 0
        
        recovered_revenue = session.scalar(
            select(func.sum(RecoveryMeasurement.verified_recovered_amount))
        ) or 0
        
        # By intervention
        attributed_by_type = session.execute(
            text("""
                SELECT 
                    a.action_type, 
                    count(m.id) as recoveries, 
                    sum(m.verified_recovered_amount) as revenue 
                FROM recovery_measurements m
                JOIN recovery_actions a ON (m.attribution_basis->>'action_id')::uuid = a.id
                WHERE m.attribution_status = 'ATTRIBUTED'
                GROUP BY a.action_type
            """)
        ).all()
        
        intervention_metrics = {}
        for row in attributed_by_type:
            intervention_metrics[row[0]] = {
                "recoveries": row[1],
                "recovered_revenue": row[2]
            }
            
        return {
            "total_failed_attempts": total_failed_attempts,
            "total_cases": total_cases,
            "recovered_cases": recovered_cases,
            "recovery_rate": round(recovery_rate, 2),
            "revenue_at_risk": revenue_at_risk,
            "recovered_revenue": recovered_revenue,
            "intervention_metrics": intervention_metrics
        }
