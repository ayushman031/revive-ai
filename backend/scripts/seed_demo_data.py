import sys
import uuid
from datetime import datetime, timezone, timedelta
from pathlib import Path

# Add backend directory to Python path
sys.path.append(str(Path(__file__).parent.parent))

from app.core.database import get_session_factory
from app.models.merchant import Merchant
from app.models.payment import Payment
from app.models.payment_attempt import PaymentAttempt
from app.models.recovery_case import RecoveryCase
from app.models.diagnosis import Diagnosis
from app.models.prediction import Prediction
from app.models.policy_decision import PolicyDecision
from app.models.recovery_action import RecoveryAction
from app.models.recovery_measurement import RecoveryMeasurement
from app.models.recommendation import Recommendation

DEMO_MERCHANT_ID = uuid.UUID("99999999-9999-9999-9999-999999999999")

def clean_demo_data(db):
    """Clean ONLY demo data"""
    db.query(RecoveryMeasurement).filter(RecoveryMeasurement.recovery_case_id.in_(
        db.query(RecoveryCase.id).filter(RecoveryCase.merchant_id == DEMO_MERCHANT_ID)
    )).delete(synchronize_session=False)
    db.query(RecoveryAction).filter(RecoveryAction.recovery_case_id.in_(
        db.query(RecoveryCase.id).filter(RecoveryCase.merchant_id == DEMO_MERCHANT_ID)
    )).delete(synchronize_session=False)
    db.query(PolicyDecision).filter(PolicyDecision.recovery_case_id.in_(
        db.query(RecoveryCase.id).filter(RecoveryCase.merchant_id == DEMO_MERCHANT_ID)
    )).delete(synchronize_session=False)
    db.query(Recommendation).filter(Recommendation.recovery_case_id.in_(
        db.query(RecoveryCase.id).filter(RecoveryCase.merchant_id == DEMO_MERCHANT_ID)
    )).delete(synchronize_session=False)
    db.query(Prediction).filter(Prediction.recovery_case_id.in_(
        db.query(RecoveryCase.id).filter(RecoveryCase.merchant_id == DEMO_MERCHANT_ID)
    )).delete(synchronize_session=False)
    db.query(Diagnosis).filter(Diagnosis.recovery_case_id.in_(
        db.query(RecoveryCase.id).filter(RecoveryCase.merchant_id == DEMO_MERCHANT_ID)
    )).delete(synchronize_session=False)
    db.query(RecoveryCase).filter(RecoveryCase.merchant_id == DEMO_MERCHANT_ID).delete(synchronize_session=False)
    db.query(PaymentAttempt).filter(PaymentAttempt.payment_id.in_(
        db.query(Payment.id).filter(Payment.merchant_id == DEMO_MERCHANT_ID)
    )).delete(synchronize_session=False)
    db.query(Payment).filter(Payment.merchant_id == DEMO_MERCHANT_ID).delete(synchronize_session=False)
    db.commit()

def seed():
    SessionFactory = get_session_factory()
    db = SessionFactory()

    try:
        m = db.query(Merchant).filter(Merchant.id == DEMO_MERCHANT_ID).first()
        if not m:
            m = Merchant(id=DEMO_MERCHANT_ID, razorpay_account_id="acc_demo_test", name="REVIVE Demo Merchant")
            db.add(m)
            db.commit()

        print("Cleaning old demo data...")
        clean_demo_data(db)

        now = datetime.now(timezone.utc)
        print("Seeding new demo data...")

        # Scenarios to generate:
        scenarios = [
            # 1. recovered + attributed
            {"status": "RECOVERED", "action_status": "EXECUTED", "attributed": True, "amount": 100000, "diag": "INSUFFICIENT_FUNDS", "intervention": "SMART_RETRY", "policy": "ALLOW"},
            # 2. successful payment + unattributed
            {"status": "RECOVERED", "action_status": "PENDING", "attributed": False, "amount": 50000, "diag": "TEMPORARY_ERROR", "intervention": "PAYMENT_LINK", "policy": "ALLOW"},
            # 3. open recovery case
            {"status": "OPEN", "action_status": "PENDING", "attributed": False, "amount": 25000, "diag": "ABANDONED", "intervention": "NUDGE", "policy": "ALLOW"},
            # 4. denied policy decision
            {"status": "OPEN", "action_status": None, "attributed": False, "amount": 75000, "diag": "HIGH_RISK", "intervention": "PAYMENT_LINK", "policy": "DENY"},
            # 5. executed action + unsuccessful recovery (failed attempt)
            {"status": "OPEN", "action_status": "FAILED", "attributed": False, "amount": 40000, "diag": "INSUFFICIENT_FUNDS", "intervention": "SMART_RETRY", "policy": "ALLOW"},
            # 6. Escalate case
            {"status": "OPEN", "action_status": None, "attributed": False, "amount": 150000, "diag": "SUSPICIOUS", "intervention": "HUMAN_ESCALATION", "policy": "ESCALATE"},
            # 7. Another recovered + attributed (different intervention)
            {"status": "RECOVERED", "action_status": "EXECUTED", "attributed": True, "amount": 60000, "diag": "ABANDONED", "intervention": "PAYMENT_LINK", "policy": "ALLOW"},
        ]

        for i, s in enumerate(scenarios):
            # Base timestamps
            base_time = now - timedelta(days=len(scenarios) - i)

            p = Payment(id=uuid.uuid4(), merchant_id=DEMO_MERCHANT_ID, amount=s["amount"], status="FAILED", payment_context="CHECKOUT")
            pa = PaymentAttempt(id=uuid.uuid4(), payment_id=p.id, razorpay_payment_id=f"pay_demo_test_{i}", attempt_number=1, method="card", status="FAILED", attempted_at=base_time)

            rc = RecoveryCase(
                id=uuid.uuid4(),
                merchant_id=DEMO_MERCHANT_ID,
                payment_id=p.id,
                trigger_attempt_id=pa.id,
                scenario="FAILED_PAYMENT",
                status=s["status"],
                revenue_at_risk=s["amount"],
                created_at=base_time + timedelta(seconds=10)
            )
            db.add_all([p, pa, rc])
            db.flush()

            diag = Diagnosis(
                id=uuid.uuid4(), recovery_case_id=rc.id, payment_attempt_id=pa.id, failure_category=s["diag"], is_retryable=True,
                root_cause_summary="Generated by demo seed", rule_version="1.0", diagnosed_at=base_time + timedelta(seconds=20)
            )
            db.add(diag)

            pred = Prediction(
                id=uuid.uuid4(), recovery_case_id=rc.id, model_id="baseline_v1", model_version="1.0", feature_version="1.0", features_snapshot={}, risk_score=0.5,
                recovery_probability_retry=0.6, recovery_probability_link=0.5, recovery_probability_nudge=0.4,
                predicted_at=base_time + timedelta(seconds=30)
            )
            db.add(pred)
            db.flush()

            rec = Recommendation(
                id=uuid.uuid4(), recovery_case_id=rc.id, prediction_id=pred.id,
                recommended_intervention=s["intervention"], expected_recoverable_amount=s["amount"],
                ranking_rationale={"reason": "Demo"}, recommended_execution_delay_seconds=0, recommended_at=base_time + timedelta(seconds=40)
            )
            db.add(rec)
            db.flush()

            pol = PolicyDecision(
                id=uuid.uuid4(), recovery_case_id=rc.id, decision=s["policy"],
                evaluated_intervention=s["intervention"], rejection_reasons={"reason": "high risk"} if s["policy"] == "DENY" else {},
                policy_version="1.0", diagnosis_id=diag.id, recommendation_id=rec.id, rules_evaluated=[],
                evaluated_at=base_time + timedelta(seconds=50)
            )
            db.add(pol)

            act = None
            if s["action_status"]:
                act = RecoveryAction(
                    id=uuid.uuid4(), recovery_case_id=rc.id, policy_decision_id=pol.id, action_type=s["intervention"],
                    status=s["action_status"], idempotency_key=str(uuid.uuid4()), scheduled_for=base_time + timedelta(seconds=60),
                    executed_at=base_time + timedelta(seconds=60) if s["action_status"] in ["EXECUTED", "FAILED"] else None
                )
                db.add(act)

            db.flush()

            if s["status"] == "RECOVERED":
                meas = RecoveryMeasurement(
                    id=uuid.uuid4(), recovery_case_id=rc.id, resolution_attempt_id=pa.id,
                    attribution_status="ATTRIBUTED" if s["attributed"] else "UNATTRIBUTED",
                    verified_recovered_amount=s["amount"], currency="INR", time_to_recovery_seconds=3600,
                    attribution_basis={"action_id": str(act.id)} if s["attributed"] and act else {},
                    measured_at=base_time + timedelta(minutes=30)
                )
                db.add(meas)

        # Scenario 8: Multiple interventions where the most recent receives attribution
        base_time = now - timedelta(hours=1)
        p = Payment(id=uuid.uuid4(), merchant_id=DEMO_MERCHANT_ID, amount=80000, status="FAILED", payment_context="CHECKOUT")
        pa = PaymentAttempt(id=uuid.uuid4(), payment_id=p.id, razorpay_payment_id="pay_demo_test_multi", attempt_number=1, method="card", status="FAILED", attempted_at=base_time)
        rc = RecoveryCase(
            id=uuid.uuid4(), merchant_id=DEMO_MERCHANT_ID, payment_id=p.id, trigger_attempt_id=pa.id, scenario="FAILED_PAYMENT", status="RECOVERED", revenue_at_risk=80000, created_at=base_time + timedelta(seconds=10)
        )
        db.add_all([p, pa, rc])
        db.flush()

        diag = Diagnosis(id=uuid.uuid4(), recovery_case_id=rc.id, payment_attempt_id=pa.id, failure_category="TEMPORARY_ERROR", is_retryable=True, root_cause_summary="Generated by demo seed", rule_version="1.0", diagnosed_at=base_time + timedelta(seconds=20))
        db.add(diag)

        pred = Prediction(id=uuid.uuid4(), recovery_case_id=rc.id, model_id="baseline_v1", model_version="1.0", feature_version="1.0", features_snapshot={}, risk_score=0.2, recovery_probability_retry=0.8, recovery_probability_link=0.6, recovery_probability_nudge=0.4, predicted_at=base_time + timedelta(seconds=30))
        db.add(pred)
        db.flush()

        rec = Recommendation(id=uuid.uuid4(), recovery_case_id=rc.id, prediction_id=pred.id, recommended_intervention="SMART_RETRY", expected_recoverable_amount=80000, ranking_rationale={"reason": "Demo"}, recommended_execution_delay_seconds=0, recommended_at=base_time + timedelta(seconds=40))
        db.add(rec)
        db.flush()

        pol1 = PolicyDecision(id=uuid.uuid4(), recovery_case_id=rc.id, decision="ALLOW", evaluated_intervention="SMART_RETRY", rejection_reasons={}, policy_version="1.0", diagnosis_id=diag.id, recommendation_id=rec.id, rules_evaluated=[], evaluated_at=base_time + timedelta(seconds=50))
        db.add(pol1)

        act1 = RecoveryAction(id=uuid.uuid4(), recovery_case_id=rc.id, policy_decision_id=pol1.id, action_type="SMART_RETRY", status="FAILED", idempotency_key=str(uuid.uuid4()), scheduled_for=base_time + timedelta(seconds=60), executed_at=base_time + timedelta(seconds=60))
        db.add(act1)
        db.flush()

        # Second intervention for the same case
        rec2 = Recommendation(id=uuid.uuid4(), recovery_case_id=rc.id, prediction_id=pred.id, recommended_intervention="PAYMENT_LINK", expected_recoverable_amount=80000, ranking_rationale={"reason": "Demo"}, recommended_execution_delay_seconds=0, recommended_at=base_time + timedelta(minutes=5))
        db.add(rec2)
        db.flush()

        pol2 = PolicyDecision(id=uuid.uuid4(), recovery_case_id=rc.id, decision="ALLOW", evaluated_intervention="PAYMENT_LINK", rejection_reasons={}, policy_version="1.0", diagnosis_id=diag.id, recommendation_id=rec2.id, rules_evaluated=[], evaluated_at=base_time + timedelta(minutes=6))
        db.add(pol2)

        act2 = RecoveryAction(id=uuid.uuid4(), recovery_case_id=rc.id, policy_decision_id=pol2.id, action_type="PAYMENT_LINK", status="EXECUTED", idempotency_key=str(uuid.uuid4()), scheduled_for=base_time + timedelta(minutes=7), executed_at=base_time + timedelta(minutes=7))
        db.add(act2)
        db.flush()

        meas = RecoveryMeasurement(
            id=uuid.uuid4(), recovery_case_id=rc.id, resolution_attempt_id=pa.id,
            attribution_status="ATTRIBUTED", verified_recovered_amount=80000, currency="INR", time_to_recovery_seconds=3600,
            attribution_basis={"action_id": str(act2.id)}, measured_at=base_time + timedelta(minutes=30)
        )
        db.add(meas)

        db.commit()
        print("Seeded successfully")
    except Exception as e:
        db.rollback()
        print(f"Failed to seed: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed()
