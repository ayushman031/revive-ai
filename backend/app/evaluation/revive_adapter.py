import uuid
from dataclasses import dataclass
from typing import Any

from app.evaluation.models import EvalTransaction
from app.ml.features import extract_features_raw
from app.ml.inference import get_inference_engine
from app.services.policy_engine import PolicyEngine, PolicyEvaluationResult

@dataclass
class MockRecoveryCase:
    id: uuid.UUID
    revenue_at_risk: int
    status: str

@dataclass
class MockPaymentAttempt:
    id: uuid.UUID
    attempt_number: int
    method: str

@dataclass
class MockDiagnosis:
    id: uuid.UUID
    failure_category: str
    is_retryable: bool

class ReviveStrategyAdapter:
    """
    Adapter to run the existing REVIVE ML inference and Policy Engine
    without interacting with operational database tables.
    """
    def __init__(self):
        self.inference_engine = get_inference_engine()

    def name(self) -> str:
        return "REVIVE Strategy"

    def _create_mocks(self, transaction: EvalTransaction) -> tuple[MockRecoveryCase, MockPaymentAttempt, MockDiagnosis]:
        case_id = uuid.uuid4()
        case = MockRecoveryCase(
            id=case_id,
            revenue_at_risk=transaction.amount,
            status="OPEN"
        )
        attempt = MockPaymentAttempt(
            id=uuid.uuid4(),
            attempt_number=transaction.attempt_number,
            method=transaction.method
        )
        diagnosis = MockDiagnosis(
            id=uuid.uuid4(),
            failure_category=transaction.failure_category,
            is_retryable=bool(transaction.is_retryable)
        )
        return case, attempt, diagnosis

    def evaluate(self, transaction: EvalTransaction) -> str:
        """
        Runs ML prediction to select the best intervention.
        """
        case, attempt, diagnosis = self._create_mocks(transaction)
        
        # 1. Extract features using the shared deterministic contract
        features = extract_features_raw(case, attempt, diagnosis)
        
        # 2. Get predictions
        results = self.inference_engine.predict(features)
        probs = results.get("probabilities", {})
        
        # 3. Select best intervention
        prob_retry = probs.get("recovery_probability_retry") or 0.0
        prob_link = probs.get("recovery_probability_link") or 0.0
        prob_nudge = probs.get("recovery_probability_nudge") or 0.0
        
        candidates = [
            ("retry", prob_retry),
            ("link", prob_link),
            ("nudge", prob_nudge),
        ]
        best_intervention, _ = max(candidates, key=lambda x: x[1])
        
        return best_intervention

    def evaluate_policy(self, transaction: EvalTransaction) -> PolicyEvaluationResult:
        """
        Runs the exact Phase 5 deterministic policy rules against the transaction.
        """
        case, _, diagnosis = self._create_mocks(transaction)
        # Using existing_actions_count = transaction.attempt_number - 1
        return PolicyEngine.evaluate(case, diagnosis, existing_actions_count=(transaction.attempt_number - 1))
