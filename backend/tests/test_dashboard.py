import uuid
from datetime import datetime, timezone
import pytest
from sqlalchemy.orm import Session
from fastapi.testclient import TestClient

from app.main import app
from app.models.merchant import Merchant
from app.models.payment import Payment
from app.models.recovery_case import RecoveryCase
from app.models.payment_attempt import PaymentAttempt
from app.models.recovery_action import RecoveryAction
from app.models.policy_decision import PolicyDecision

client = TestClient(app)

def test_dashboard_metrics_empty(db_session: Session):
    m_id = str(uuid.uuid4())
    response = client.get(f"/api/v1/dashboard/metrics?merchant_id={m_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["total_cases"] == 0
    assert data["revenue_at_risk"] == 0

def test_merchant_isolation_metrics(db_session: Session):
    # Create two merchants
    m1 = Merchant(id=uuid.uuid4(), razorpay_account_id=f"acc_{uuid.uuid4()}", name="M1")
    m2 = Merchant(id=uuid.uuid4(), razorpay_account_id=f"acc_{uuid.uuid4()}", name="M2")
    db_session.add_all([m1, m2])
    db_session.flush()

    p1 = Payment(id=uuid.uuid4(), merchant_id=m1.id, amount=1000, status="FAILED", payment_context="CHECKOUT")
    pa1 = PaymentAttempt(id=uuid.uuid4(), payment_id=p1.id, razorpay_payment_id=f"pay_{uuid.uuid4()}", attempt_number=1, method="card", status="FAILED", attempted_at=datetime.now(timezone.utc))
    rc1 = RecoveryCase(id=uuid.uuid4(), merchant_id=m1.id, payment_id=p1.id, trigger_attempt_id=pa1.id, scenario="FAILED_PAYMENT", status="OPEN", revenue_at_risk=1000)

    p2 = Payment(id=uuid.uuid4(), merchant_id=m2.id, amount=2000, status="FAILED", payment_context="CHECKOUT")
    pa2 = PaymentAttempt(id=uuid.uuid4(), payment_id=p2.id, razorpay_payment_id=f"pay_{uuid.uuid4()}", attempt_number=1, method="upi", status="FAILED", attempted_at=datetime.now(timezone.utc))
    rc2 = RecoveryCase(id=uuid.uuid4(), merchant_id=m2.id, payment_id=p2.id, trigger_attempt_id=pa2.id, scenario="FAILED_PAYMENT", status="OPEN", revenue_at_risk=2000)

    db_session.add_all([p1, pa1, rc1, p2, pa2, rc2])
    db_session.commit()

    # Test M1
    resp1 = client.get(f"/api/v1/dashboard/metrics?merchant_id={m1.id}")
    assert resp1.status_code == 200
    assert resp1.json()["total_cases"] == 1
    assert resp1.json()["revenue_at_risk"] == 1000

    # Test M2
    resp2 = client.get(f"/api/v1/dashboard/metrics?merchant_id={m2.id}")
    assert resp2.status_code == 200
    assert resp2.json()["total_cases"] == 1
    assert resp2.json()["revenue_at_risk"] == 2000

def test_cases_listing_pagination_and_status(db_session: Session):
    m_id = uuid.uuid4()
    m = Merchant(id=m_id, razorpay_account_id=f"acc_{uuid.uuid4()}", name="M_List")
    db_session.add(m)
    db_session.flush()

    for i in range(15):
        p = Payment(id=uuid.uuid4(), merchant_id=m_id, amount=100*i, status="FAILED", payment_context="CHECKOUT")
        pa = PaymentAttempt(id=uuid.uuid4(), payment_id=p.id, razorpay_payment_id=f"pay_{uuid.uuid4()}", attempt_number=1, method="card", status="FAILED", attempted_at=datetime.now(timezone.utc))
        rc = RecoveryCase(id=uuid.uuid4(), merchant_id=m_id, payment_id=p.id, trigger_attempt_id=pa.id, scenario="FAILED_PAYMENT", status="OPEN" if i < 10 else "RECOVERED", revenue_at_risk=100*i)
        db_session.add_all([p, pa, rc])
    db_session.commit()

    # Pagination test
    resp = client.get(f"/api/v1/cases?merchant_id={m_id}&limit=10&offset=0")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 15
    assert len(data["items"]) == 10

    resp = client.get(f"/api/v1/cases?merchant_id={m_id}&limit=10&offset=10")
    assert resp.json()["total"] == 15
    assert len(resp.json()["items"]) == 5

    # Status test
    resp = client.get(f"/api/v1/cases?merchant_id={m_id}&status=RECOVERED")
    assert resp.json()["total"] == 5

def test_case_detail_isolation(db_session: Session):
    m1_id = uuid.uuid4()
    m2_id = uuid.uuid4()
    m1 = Merchant(id=m1_id, razorpay_account_id=f"acc_{uuid.uuid4()}", name="M1")
    m2 = Merchant(id=m2_id, razorpay_account_id=f"acc_{uuid.uuid4()}", name="M2")
    db_session.add_all([m1, m2])
    db_session.flush()

    p = Payment(id=uuid.uuid4(), merchant_id=m1_id, amount=100, status="FAILED", payment_context="CHECKOUT")
    pa = PaymentAttempt(id=uuid.uuid4(), payment_id=p.id, razorpay_payment_id=f"pay_{uuid.uuid4()}", attempt_number=1, method="card", status="FAILED", attempted_at=datetime.now(timezone.utc))
    rc_id = uuid.uuid4()
    rc = RecoveryCase(id=rc_id, merchant_id=m1_id, payment_id=p.id, trigger_attempt_id=pa.id, scenario="FAILED_PAYMENT", status="OPEN", revenue_at_risk=100)
    db_session.add_all([p, pa, rc])
    db_session.commit()

    # Valid access
    resp = client.get(f"/api/v1/cases/{rc_id}?merchant_id={m1_id}")
    assert resp.status_code == 200
    assert resp.json()["id"] == str(rc_id)

    # Cross merchant access
    resp = client.get(f"/api/v1/cases/{rc_id}?merchant_id={m2_id}")
    assert resp.status_code == 404

    # Non-existent
    resp = client.get(f"/api/v1/cases/{uuid.uuid4()}?merchant_id={m1_id}")
    assert resp.status_code == 404
