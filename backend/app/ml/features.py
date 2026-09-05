from typing import Any

from app.models.diagnosis import Diagnosis
from app.models.payment_attempt import PaymentAttempt
from app.models.recovery_case import RecoveryCase


def extract_features_raw(
    recovery_case: RecoveryCase,
    payment_attempt: PaymentAttempt,
    diagnosis: Diagnosis,
) -> dict[str, Any]:
    """
    Extract deterministic features for ML inference and training.
    
    This function defines the authoritative feature contract. Both the
    backend inference service and the synthetic data generator must
    use these identical definitions.
    """
    return {
        "amount": recovery_case.revenue_at_risk,
        "attempt_number": payment_attempt.attempt_number,
        "method": payment_attempt.method,
        "failure_category": diagnosis.failure_category,
        "is_retryable": int(diagnosis.is_retryable),
    }

FEATURE_VERSION = "1.0.0"
