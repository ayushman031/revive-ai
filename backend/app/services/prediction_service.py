from sqlalchemy.orm import Session

from app.ml.features import extract_features_raw
from app.ml.inference import get_inference_engine
from app.models.diagnosis import Diagnosis
from app.models.payment_attempt import PaymentAttempt
from app.models.prediction import Prediction
from app.models.recommendation import Recommendation
from app.models.recovery_case import RecoveryCase


class PredictionService:
    def __init__(self, db: Session):
        self.db = db
        self.inference_engine = get_inference_engine()

    def generate_prediction(
        self,
        recovery_case: RecoveryCase,
        payment_attempt: PaymentAttempt,
        diagnosis: Diagnosis,
    ) -> tuple[Prediction, Recommendation]:
        """
        Extract features, run inference, and persist Prediction and Recommendation.
        This service is strictly advisory. It does not execute actions.
        """
        # 1. Extract features using the shared contract
        features = extract_features_raw(recovery_case, payment_attempt, diagnosis)
        
        # 2. Get predictions from ML models
        results = self.inference_engine.predict(features)
        probs = results["probabilities"]
        model_versions = results["model_versions"]
        feature_versions = results["feature_versions"]
        
        # Fallback values if models are missing
        prob_retry = probs.get("recovery_probability_retry") or 0.0
        prob_link = probs.get("recovery_probability_link") or 0.0
        prob_nudge = probs.get("recovery_probability_nudge") or 0.0
        
        # 3. Create Prediction record
        prediction = Prediction(
            recovery_case_id=recovery_case.id,
            model_id="baseline_logistic_regression",
            # We can store the retry model's version as representative, or combine them
            model_version=model_versions.get("retry", "unknown"),
            feature_version=feature_versions.get("retry", "unknown"),
            features_snapshot=features,
            risk_score=0.5, # Dummy risk score for now
            recovery_probability_retry=prob_retry,
            recovery_probability_link=prob_link,
            recovery_probability_nudge=prob_nudge,
        )
        self.db.add(prediction)
        self.db.flush() # flush to get prediction.id
        
        # 4. Create Recommendation record
        # A simple heuristic to choose the highest probability
        candidates = [
            ("retry", prob_retry),
            ("link", prob_link),
            ("nudge", prob_nudge),
        ]
        best_intervention, best_prob = max(candidates, key=lambda x: x[1])
        
        expected_recoverable = int(recovery_case.revenue_at_risk * best_prob)
        
        recommendation = Recommendation(
            recovery_case_id=recovery_case.id,
            prediction_id=prediction.id,
            recommended_intervention=best_intervention,
            ranking_rationale={
                "probabilities": {k: float(v) for k, v in candidates},
                "selection": "highest_probability"
            },
            expected_recoverable_amount=expected_recoverable,
            recommended_execution_delay_seconds=0 # Immediate execution recommendation
        )
        self.db.add(recommendation)
        self.db.flush()
        
        return prediction, recommendation
