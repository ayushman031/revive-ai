import json
import os
import tempfile
import uuid
from datetime import datetime, timezone
import pytest
from unittest.mock import patch, MagicMock

from app.ml.features import extract_features_raw
from app.ml.inference import InferenceEngine
from app.services.prediction_service import PredictionService
from app.services.policy_engine import PolicyEngine, PolicyDecisionResult
from app.models.diagnosis import Diagnosis
from app.models.payment_attempt import PaymentAttempt
from app.models.recovery_case import RecoveryCase


def test_feature_extraction():
    case = RecoveryCase(id=uuid.uuid4(), revenue_at_risk=50000)
    attempt = PaymentAttempt(id=uuid.uuid4(), attempt_number=2, method="card")
    diagnosis = Diagnosis(id=uuid.uuid4(), failure_category="insufficient_funds", is_retryable=True)
    
    features = extract_features_raw(case, attempt, diagnosis)
    
    assert features["amount"] == 50000
    assert features["attempt_number"] == 2
    assert features["method"] == "card"
    assert features["failure_category"] == "insufficient_funds"
    assert features["is_retryable"] == 1


def test_inference_engine_missing_models():
    with tempfile.TemporaryDirectory() as tmpdir:
        engine = InferenceEngine(tmpdir)
        features = {
            "amount": 50000,
            "attempt_number": 1,
            "method": "upi",
            "failure_category": "gateway_timeout",
            "is_retryable": 1
        }
        result = engine.predict(features)
        assert result["probabilities"]["recovery_probability_retry"] is None
        assert result["model_versions"]["retry"] is None


def test_safety_boundary_ml_predicts_but_policy_denies():
    # ML recommends retry, but policy denies (e.g., non-retryable)
    case = RecoveryCase(id=uuid.uuid4(), status="OPEN", revenue_at_risk=10000)
    diagnosis = Diagnosis(failure_category="CARD_EXPIRED", is_retryable=False) # Will trigger hard restriction DENY
    
    # Simulate ML recommendation (this would be output of PredictionService)
    # ML might still predict high retry probability due to model quirks, but policy MUST deny
    ml_recommended_intervention = "retry"
    
    policy_result = PolicyEngine.evaluate(case, diagnosis)
    
    assert policy_result.decision == PolicyDecisionResult.DENY
    # Thus, no execution can occur regardless of ml_recommended_intervention


def test_safety_boundary_ml_predicts_but_policy_escalates():
    case = RecoveryCase(id=uuid.uuid4(), status="OPEN", revenue_at_risk=10000)
    diagnosis = Diagnosis(failure_category="UNKNOWN", is_retryable=True) # Triggers ESCALATE
    
    ml_recommended_intervention = "link"
    
    policy_result = PolicyEngine.evaluate(case, diagnosis)
    
    assert policy_result.decision == PolicyDecisionResult.ESCALATE
    # Thus, no automated execution can occur (escalation handles it)


def test_prediction_service_creates_records():
    case = RecoveryCase(id=uuid.uuid4(), revenue_at_risk=50000)
    attempt = PaymentAttempt(id=uuid.uuid4(), attempt_number=1, method="upi")
    diagnosis = Diagnosis(id=uuid.uuid4(), failure_category="gateway_timeout", is_retryable=True)
    
    db_session = MagicMock()
    
    # Mock inference engine to return high retry probability
    service = PredictionService(db_session)
    service.inference_engine.predict = MagicMock(return_value={
        "probabilities": {
            "recovery_probability_retry": 0.85,
            "recovery_probability_link": 0.2,
            "recovery_probability_nudge": 0.1
        },
        "model_versions": {"retry": "1.0", "link": "1.0", "nudge": "1.0"},
        "feature_versions": {"retry": "1.0", "link": "1.0", "nudge": "1.0"},
    })
    
    prediction, recommendation = service.generate_prediction(case, attempt, diagnosis)
    
    assert prediction.recovery_probability_retry == 0.85
    assert recommendation.recommended_intervention == "retry"
    assert recommendation.expected_recoverable_amount == int(50000 * 0.85)
    
    # Ensure added to DB session
    assert db_session.add.call_count == 2
