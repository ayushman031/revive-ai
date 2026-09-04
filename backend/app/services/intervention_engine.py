"""Deterministic Intervention Engine for Phase 5."""

import logging
from dataclasses import dataclass
from app.models.recovery_case import RecoveryCase
from app.models.diagnosis import Diagnosis

logger = logging.getLogger(__name__)


class InterventionType:
    SMART_RETRY = "SMART_RETRY"
    PAYMENT_LINK = "PAYMENT_LINK"
    EMAIL_NUDGE = "EMAIL_NUDGE"
    HUMAN_ESCALATION = "HUMAN_ESCALATION"


@dataclass(frozen=True)
class InterventionSelectionResult:
    action_type: str
    priority: int


class InterventionEngine:
    """
    Deterministic Intervention Selection.
    
    Called ONLY AFTER a PolicyDecision evaluates to ALLOW or ESCALATE.
    
    Priority Rules (Highest priority returned first):
    1. If Policy is ESCALATE -> HUMAN_ESCALATION
    2. If Diagnosis == INSUFFICIENT_FUNDS -> SMART_RETRY
    3. If Diagnosis == NETWORK_ERROR or GATEWAY_ERROR -> SMART_RETRY
    4. If Diagnosis == ABANDONED_CHECKOUT -> PAYMENT_LINK
    5. Fallback -> EMAIL_NUDGE
    """

    @classmethod
    def select(cls, case: RecoveryCase, diagnosis: Diagnosis, policy_decision_result: str) -> InterventionSelectionResult | None:
        if policy_decision_result == "DENY":
            return None

        if policy_decision_result == "ESCALATE":
            # Escalation doesn't trigger automated provider execution, but creates an escalation action state.
            return InterventionSelectionResult(InterventionType.HUMAN_ESCALATION, priority=1)

        # Allow: Deterministically select intervention
        if diagnosis.failure_category in ("INSUFFICIENT_FUNDS", "NETWORK_ERROR", "GATEWAY_ERROR"):
            return InterventionSelectionResult(InterventionType.SMART_RETRY, priority=10)
            
        if diagnosis.failure_category == "ABANDONED_CHECKOUT":
            return InterventionSelectionResult(InterventionType.PAYMENT_LINK, priority=5)

        return InterventionSelectionResult(InterventionType.EMAIL_NUDGE, priority=2)
