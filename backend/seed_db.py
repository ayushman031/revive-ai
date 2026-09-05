import sys
sys.path.append('c:/revive/revive-ai/backend')
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
import uuid
from datetime import datetime, timezone, timedelta

SessionFactory = get_session_factory()
db = SessionFactory()

MERCHANT_ID = uuid.UUID("00000000-0000-0000-0000-000000000000")

m = db.query(Merchant).filter(Merchant.id == MERCHANT_ID).first()
if not m:
    m = Merchant(id=MERCHANT_ID, razorpay_account_id="acc_demo", name="Demo Merchant")
    db.add(m)
    db.commit()

# Delete existing to prevent duplication
db.query(RecoveryCase).filter(RecoveryCase.merchant_id == MERCHANT_ID).delete()
db.commit()

now = datetime.now(timezone.utc)

for i in range(10):
    p = Payment(id=uuid.uuid4(), merchant_id=MERCHANT_ID, amount=1500 * (i+1), status="FAILED", payment_context="CHECKOUT")
    pa = PaymentAttempt(id=uuid.uuid4(), payment_id=p.id, razorpay_payment_id=f"pay_demo_{i}", attempt_number=1, method="card", status="FAILED", attempted_at=now - timedelta(days=i))

    status = "RECOVERED" if i < 4 else ("OPEN" if i < 8 else "CLOSED")

    rc = RecoveryCase(
        id=uuid.uuid4(),
        merchant_id=MERCHANT_ID,
        payment_id=p.id,
        trigger_attempt_id=pa.id,
        scenario="FAILED_PAYMENT",
        status=status,
        revenue_at_risk=1500 * (i+1),
        created_at=now - timedelta(days=i)
    )
    db.add_all([p, pa, rc])
    db.flush()

    # Add Diagnosis
    diag = Diagnosis(id=uuid.uuid4(), recovery_case_id=rc.id, failure_category="INSUFFICIENT_FUNDS", is_retryable=True, root_cause_summary="Card declined", diagnosed_at=now - timedelta(days=i, hours=-1))
    db.add(diag)

    # Add Prediction
    pred = Prediction(id=uuid.uuid4(), recovery_case_id=rc.id, model_version="1.0", risk_score=0.8, recovery_probability_retry=0.7, recovery_probability_link=0.4, recovery_probability_nudge=0.2, predicted_at=now - timedelta(days=i, hours=-1, minutes=-10))
    db.add(pred)
    db.flush()

    # Add Recommendation
    rec = Recommendation(id=uuid.uuid4(), recovery_case_id=rc.id, prediction_id=pred.id, recommended_intervention="SMART_RETRY", expected_recoverable_amount=1500*(i+1), recommended_at=now - timedelta(days=i, hours=-1, minutes=-20))
    db.add(rec)

    # Add Policy
    pol = PolicyDecision(id=uuid.uuid4(), recovery_case_id=rc.id, decision="ALLOW", evaluated_intervention="SMART_RETRY", rejection_reasons={}, evaluated_at=now - timedelta(days=i, hours=-1, minutes=-30))
    db.add(pol)

    # Add Action
    act = RecoveryAction(id=uuid.uuid4(), recovery_case_id=rc.id, action_type="SMART_RETRY", status="EXECUTED" if status == "RECOVERED" else "PENDING", scheduled_for=now - timedelta(days=i, hours=-2), executed_at=now - timedelta(days=i, hours=-2) if status == "RECOVERED" else None)
    db.add(act)
    db.flush()

    if status == "RECOVERED":
        meas = RecoveryMeasurement(id=uuid.uuid4(), recovery_case_id=rc.id, resolution_event_id=None, attribution_status="ATTRIBUTED", verified_recovered_amount=1500*(i+1), attribution_basis={"action_id": str(act.id)}, measured_at=now - timedelta(days=i, hours=-3))
        db.add(meas)

db.commit()
print("Seeded successfully")
