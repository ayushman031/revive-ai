"""Webhook event handlers for Phase 3."""

import logging
from typing import Any

from app.models.webhook_event import WebhookEvent
from app.services.diagnosis_service import process_payment_failed_diagnosis

logger = logging.getLogger(__name__)


from app.services.policy_engine import PolicyEngine
from app.services.intervention_engine import InterventionEngine
from app.models.policy_decision import PolicyDecision
from app.models.recovery_action import RecoveryAction
import uuid
from datetime import datetime, timezone

def handle_payment_failed(event: WebhookEvent, session: Any = None) -> uuid.UUID | None:
    """Handle payment.failed events by running the deterministic diagnosis pipeline, policy, and intervention."""
    logger.info(f"Processing payment.failed event: {event.event_id}")
    if not session or not event.payload:
        return None

    diagnosis = process_payment_failed_diagnosis(session, event.payload)
    if not diagnosis:
        return None

    case = diagnosis.recovery_case
    
    # Policy Gate
    policy_result = PolicyEngine.evaluate(case, diagnosis)
    
    policy_decision = PolicyDecision(
        recovery_case_id=case.id,
        diagnosis_id=diagnosis.id,
        policy_version=policy_result.policy_version,
        decision=policy_result.decision,
        rules_evaluated=policy_result.rules_evaluated,
        rejection_reasons=policy_result.rejection_reasons,
        evaluated_intervention="TBD", # Updated below if allowed
    )
    session.add(policy_decision)
    session.flush()

    if policy_result.decision in ("ALLOW", "ESCALATE"):
        intervention = InterventionEngine.select(case, diagnosis, policy_result.decision)
        if intervention:
            policy_decision.evaluated_intervention = intervention.action_type
            
            idempotency_key = f"case_{case.id}_{intervention.action_type}_1"
            action = RecoveryAction(
                recovery_case_id=case.id,
                policy_decision_id=policy_decision.id,
                action_type=intervention.action_type,
                status="APPROVED" if policy_result.decision == "ALLOW" else "ESCALATED",
                idempotency_key=idempotency_key,
                scheduled_for=datetime.now(timezone.utc),
            )
            session.add(action)
            session.flush()
            
            if policy_result.decision == "ALLOW":
                return action.id
                
    return None


def handle_payment_captured(event: WebhookEvent, session: Any = None) -> None:
    """Handle payment.captured events."""
    logger.info(f"Safely processed payment.captured event: {event.event_id}")
    if session:
        from app.services.measurement_service import MeasurementService
        MeasurementService.process_success_event(session, event)

def handle_order_paid(event: WebhookEvent, session: Any = None) -> None:
    """Handle order.paid events."""
    logger.info(f"Safely processed order.paid event: {event.event_id}")
    if session:
        from app.services.measurement_service import MeasurementService
        MeasurementService.process_success_event(session, event)



# Dispatch map for supported events
WEBHOOK_HANDLERS = {
    "payment.failed": handle_payment_failed,
    "payment.captured": handle_payment_captured,
    "order.paid": handle_order_paid,
}
