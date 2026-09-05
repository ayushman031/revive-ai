import uuid
from typing import Any
from sqlalchemy import select, func, text, case
from sqlalchemy.orm import Session

from app.models.payment import Payment
from app.models.payment_attempt import PaymentAttempt
from app.models.recovery_case import RecoveryCase
from app.models.recovery_measurement import RecoveryMeasurement
from app.models.recovery_action import RecoveryAction
from app.models.policy_decision import PolicyDecision

class DashboardMetricsService:
    @staticmethod
    def get_merchant_metrics(session: Session, merchant_id: uuid.UUID) -> dict[str, Any]:
        # 1. Total failed payment attempts (linked to merchant via payment)
        total_failed_attempts = session.scalar(
            select(func.count(PaymentAttempt.id))
            .join(Payment)
            .where(Payment.merchant_id == merchant_id, PaymentAttempt.status == "FAILED")
        ) or 0

        # 2. Case stats
        case_stats = session.execute(
            select(
                func.count(RecoveryCase.id).label("total_cases"),
                func.sum(case((RecoveryCase.status == "OPEN", 1), else_=0)).label("open_cases"),
                func.sum(case((RecoveryCase.status == "RECOVERED", 1), else_=0)).label("recovered_cases"),
                func.sum(RecoveryCase.revenue_at_risk).label("revenue_at_risk"),
            ).where(RecoveryCase.merchant_id == merchant_id)
        ).first()

        total_cases = case_stats.total_cases or 0
        open_cases = case_stats.open_cases or 0
        recovered_cases = case_stats.recovered_cases or 0
        revenue_at_risk = case_stats.revenue_at_risk or 0

        recovery_rate = (recovered_cases / total_cases * 100) if total_cases > 0 else 0.0

        # 3. Measurement stats
        measurement_stats = session.execute(
            select(
                func.sum(RecoveryMeasurement.verified_recovered_amount).label("recovered_revenue"),
                func.sum(case((RecoveryMeasurement.attribution_status == "ATTRIBUTED", RecoveryMeasurement.verified_recovered_amount), else_=0)).label("attributed_revenue"),
                func.sum(case((RecoveryMeasurement.attribution_status == "UNATTRIBUTED_SUCCESS", RecoveryMeasurement.verified_recovered_amount), else_=0)).label("unattributed_revenue"),
            )
            .join(RecoveryCase)
            .where(RecoveryCase.merchant_id == merchant_id)
        ).first()

        recovered_revenue = measurement_stats.recovered_revenue or 0
        attributed_revenue = measurement_stats.attributed_revenue or 0
        unattributed_revenue = measurement_stats.unattributed_revenue or 0

        # 4. Action counts
        action_stats = session.execute(
            select(
                func.count(RecoveryAction.id).label("total_actions"),
                func.sum(case((RecoveryAction.status == "EXECUTED", 1), else_=0)).label("successful_actions"),
                func.sum(case((RecoveryAction.status == "FAILED", 1), else_=0)).label("failed_actions"),
                func.sum(case((RecoveryAction.status.in_(["SCHEDULED", "EXECUTING"]), 1), else_=0)).label("pending_actions"),
            )
            .join(RecoveryCase)
            .where(RecoveryCase.merchant_id == merchant_id)
        ).first()

        # 5. Policy Decision counts
        policy_stats = session.execute(
            select(
                PolicyDecision.decision,
                func.count(PolicyDecision.id)
            )
            .join(RecoveryCase)
            .where(RecoveryCase.merchant_id == merchant_id)
            .group_by(PolicyDecision.decision)
        ).all()
        policy_counts = {row[0]: row[1] for row in policy_stats}

        # 6. Interventions (using JSONB attribution basis correctly per merchant)
        attributed_by_type = session.execute(
            text("""
                SELECT
                    a.action_type,
                    count(m.id) as recoveries,
                    sum(m.verified_recovered_amount) as revenue
                FROM recovery_measurements m
                JOIN recovery_cases c ON m.recovery_case_id = c.id
                JOIN recovery_actions a ON (m.attribution_basis->>'action_id')::uuid = a.id
                WHERE m.attribution_status = 'ATTRIBUTED' AND c.merchant_id = :merchant_id
                GROUP BY a.action_type
            """),
            {"merchant_id": merchant_id}
        ).all()

        intervention_metrics = {}
        for row in attributed_by_type:
            intervention_metrics[row[0]] = {
                "recoveries": row[1],
                "recovered_revenue": row[2]
            }

        # 7. Recovery by diagnosis category
        diagnosis_recovery = session.execute(
            text("""
                SELECT
                    d.failure_category,
                    count(m.id) as recoveries,
                    sum(m.verified_recovered_amount) as revenue
                FROM recovery_measurements m
                JOIN recovery_cases c ON m.recovery_case_id = c.id
                JOIN diagnoses d ON d.recovery_case_id = c.id
                WHERE c.merchant_id = :merchant_id
                GROUP BY d.failure_category
            """),
            {"merchant_id": merchant_id}
        ).all()
        diagnosis_metrics = {row[0]: {"recoveries": row[1], "recovered_revenue": row[2]} for row in diagnosis_recovery}

        # 8. Recovery by payment method
        method_recovery = session.execute(
            text("""
                SELECT
                    pa.method,
                    count(m.id) as recoveries,
                    sum(m.verified_recovered_amount) as revenue
                FROM recovery_measurements m
                JOIN recovery_cases c ON m.recovery_case_id = c.id
                JOIN payment_attempts pa ON c.trigger_attempt_id = pa.id
                WHERE c.merchant_id = :merchant_id
                GROUP BY pa.method
            """),
            {"merchant_id": merchant_id}
        ).all()
        method_metrics = {row[0]: {"recoveries": row[1], "recovered_revenue": row[2]} for row in method_recovery}

        return {
            "total_failed_attempts": total_failed_attempts,
            "total_cases": total_cases,
            "open_cases": open_cases,
            "recovered_cases": recovered_cases,
            "recovery_rate": round(recovery_rate, 2),
            "revenue_at_risk": revenue_at_risk,
            "recovered_revenue": recovered_revenue,
            "attributed_revenue": attributed_revenue,
            "unattributed_revenue": unattributed_revenue,
            "actions": {
                "total": action_stats.total_actions or 0,
                "successful": action_stats.successful_actions or 0,
                "failed": action_stats.failed_actions or 0,
                "pending": action_stats.pending_actions or 0,
            },
            "policy_decisions": policy_counts,
            "intervention_metrics": intervention_metrics,
            "diagnosis_metrics": diagnosis_metrics,
            "method_metrics": method_metrics
        }
