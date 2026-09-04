"""Deterministic Policy Engine for Phase 5."""

import logging
from dataclasses import dataclass
from typing import Any
from datetime import datetime, timezone

from app.models.recovery_case import RecoveryCase
from app.models.diagnosis import Diagnosis
from app.models.policy_decision import PolicyDecision

logger = logging.getLogger(__name__)

POLICY_VERSION = "2026.05.1"


class PolicyDecisionResult:
    ALLOW = "ALLOW"
    DENY = "DENY"
    ESCALATE = "ESCALATE"


@dataclass(frozen=True)
class PolicyEvaluationResult:
    decision: str
    rejection_reasons: dict[str, Any]
    rules_evaluated: dict[str, Any]
    policy_version: str = POLICY_VERSION


class PolicyEngine:
    """
    Deterministic Policy Engine.
    
    Precedence Order:
    1. STOP RULE (e.g. Case Closed, Payment Succeeded) -> DENY
    2. DO-NOT-CONTACT / HARD RESTRICTION -> DENY
    3. RETRY LIMIT / FREQUENCY LIMIT -> DENY
    4. COOLDOWN / RISK LIMIT -> DENY
    5. ESCALATION CONDITION (e.g. Unknown/Bank Decline) -> ESCALATE
    6. ALLOW
    """

    @classmethod
    def evaluate(
        cls, case: RecoveryCase, diagnosis: Diagnosis, existing_actions_count: int = 0
    ) -> PolicyEvaluationResult:
        rules_evaluated = {}
        rejection_reasons = {}

        # 1. Stop Rules
        rules_evaluated["stop_rule"] = True
        if case.status in ("CLOSED", "RECOVERED", "FAILED"):
            rejection_reasons["stop_rule"] = f"RecoveryCase status is {case.status}"
            return PolicyEvaluationResult(PolicyDecisionResult.DENY, rejection_reasons, rules_evaluated)

        # 2. Do Not Contact / Hard Restrictions
        rules_evaluated["hard_restrictions"] = True
        if not diagnosis.is_retryable and diagnosis.failure_category not in ("UNKNOWN", "BANK_DECLINE"):
            # e.g., CARD_EXPIRED, AUTH_FAILED
            rejection_reasons["hard_restrictions"] = f"Diagnosis category {diagnosis.failure_category} is non-retryable."
            return PolicyEvaluationResult(PolicyDecisionResult.DENY, rejection_reasons, rules_evaluated)

        # 3. Retry Limit / Frequency Limit
        rules_evaluated["retry_limit"] = True
        MAX_RETRIES = 3
        if existing_actions_count >= MAX_RETRIES:
            rejection_reasons["retry_limit"] = f"Exceeded maximum retry limit of {MAX_RETRIES} interventions."
            return PolicyEvaluationResult(PolicyDecisionResult.DENY, rejection_reasons, rules_evaluated)

        # 4. Escalation Conditions
        rules_evaluated["escalation_condition"] = True
        if diagnosis.failure_category in ("UNKNOWN", "BANK_DECLINE", "INVALID_PAYMENT_METHOD"):
            rejection_reasons["escalation_condition"] = f"Diagnosis category {diagnosis.failure_category} requires human escalation."
            return PolicyEvaluationResult(PolicyDecisionResult.ESCALATE, rejection_reasons, rules_evaluated)

        # 5. Allow
        return PolicyEvaluationResult(PolicyDecisionResult.ALLOW, rejection_reasons, rules_evaluated)

