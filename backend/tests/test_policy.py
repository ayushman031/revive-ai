import pytest
from app.services.policy_engine import PolicyEngine, PolicyDecisionResult
from app.services.intervention_engine import InterventionEngine, InterventionType
from app.models.recovery_case import RecoveryCase
from app.models.diagnosis import Diagnosis
from app.models.constants import FailureCategory


def test_policy_engine_stop_rule():
    case = RecoveryCase(status="CLOSED")
    diagnosis = Diagnosis(failure_category=FailureCategory.INSUFFICIENT_FUNDS, is_retryable=True)
    result = PolicyEngine.evaluate(case, diagnosis, 0)
    assert result.decision == PolicyDecisionResult.DENY
    assert "stop_rule" in result.rejection_reasons


def test_policy_engine_hard_restriction():
    case = RecoveryCase(status="DIAGNOSED")
    diagnosis = Diagnosis(failure_category=FailureCategory.AUTH_FAILED, is_retryable=False)
    result = PolicyEngine.evaluate(case, diagnosis, 0)
    assert result.decision == PolicyDecisionResult.DENY
    assert "hard_restrictions" in result.rejection_reasons


def test_policy_engine_retry_limit():
    case = RecoveryCase(status="DIAGNOSED")
    diagnosis = Diagnosis(failure_category=FailureCategory.INSUFFICIENT_FUNDS, is_retryable=True)
    result = PolicyEngine.evaluate(case, diagnosis, 3)
    assert result.decision == PolicyDecisionResult.DENY
    assert "retry_limit" in result.rejection_reasons


def test_policy_engine_escalate():
    case = RecoveryCase(status="DIAGNOSED")
    diagnosis = Diagnosis(failure_category=FailureCategory.BANK_DECLINE, is_retryable=False)
    result = PolicyEngine.evaluate(case, diagnosis, 0)
    assert result.decision == PolicyDecisionResult.ESCALATE


def test_policy_engine_allow():
    case = RecoveryCase(status="DIAGNOSED")
    diagnosis = Diagnosis(failure_category=FailureCategory.INSUFFICIENT_FUNDS, is_retryable=True)
    result = PolicyEngine.evaluate(case, diagnosis, 0)
    assert result.decision == PolicyDecisionResult.ALLOW


def test_intervention_engine_escalate():
    case = RecoveryCase(status="DIAGNOSED")
    diagnosis = Diagnosis(failure_category=FailureCategory.BANK_DECLINE, is_retryable=False)
    result = InterventionEngine.select(case, diagnosis, PolicyDecisionResult.ESCALATE)
    assert result.action_type == InterventionType.HUMAN_ESCALATION


def test_intervention_engine_allow_retry():
    case = RecoveryCase(status="DIAGNOSED")
    diagnosis = Diagnosis(failure_category=FailureCategory.INSUFFICIENT_FUNDS, is_retryable=True)
    result = InterventionEngine.select(case, diagnosis, PolicyDecisionResult.ALLOW)
    assert result.action_type == InterventionType.SMART_RETRY

def test_intervention_engine_deny():
    case = RecoveryCase(status="CLOSED")
    diagnosis = Diagnosis(failure_category=FailureCategory.INSUFFICIENT_FUNDS, is_retryable=True)
    result = InterventionEngine.select(case, diagnosis, PolicyDecisionResult.DENY)
    assert result is None
