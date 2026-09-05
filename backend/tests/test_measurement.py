import pytest
import uuid
from datetime import datetime, timedelta, timezone
from sqlalchemy import select

from app.models.payment import Payment
from app.models.payment_attempt import PaymentAttempt
from app.models.recovery_case import RecoveryCase
from app.models.recovery_action import RecoveryAction
from app.models.webhook_event import WebhookEvent
from app.models.recovery_measurement import RecoveryMeasurement
from app.services.measurement_service import MeasurementService, MetricsService
from app.services.webhook_handlers import handle_payment_captured

@pytest.fixture
def base_scenario(db_session):
    # Create merchant and customer if needed? Wait, the models allow us to just set up directly or use fixtures.
    # Actually, let's create just the raw models needed.
    from app.models.merchant import Merchant
    merchant = Merchant(name="Test Merch", razorpay_account_id=f"acc_{uuid.uuid4().hex[:8]}")
    db_session.add(merchant)
    db_session.flush()

    payment = Payment(
        merchant_id=merchant.id,
        razorpay_order_id=f"order_{uuid.uuid4().hex[:8]}",
        currency="INR",
        amount=10000,
        status="FAILED",
        payment_context="checkout",
    )
    db_session.add(payment)
    db_session.flush()

    attempt = PaymentAttempt(
        payment_id=payment.id,
        razorpay_payment_id=f"pay_{uuid.uuid4().hex[:8]}",
        attempt_number=1,
        method="card",
        status="FAILED",
        attempted_at=datetime.now(timezone.utc) - timedelta(days=2)
    )
    db_session.add(attempt)
    db_session.flush()

    case = RecoveryCase(
        merchant_id=merchant.id,
        payment_id=payment.id,
        trigger_attempt_id=attempt.id,
        scenario="FAILED_PAYMENT",
        status="OPEN",
        revenue_at_risk=10000
    )
    db_session.add(case)
    db_session.flush()

    return {
        "merchant": merchant,
        "payment": payment,
        "attempt": attempt,
        "case": case
    }

def test_measurement_attributed(db_session, base_scenario):
    case = base_scenario["case"]
    payment = base_scenario["payment"]
    
    # 1. Setup Action 12 hours ago
    action_time = datetime.now(timezone.utc) - timedelta(hours=12)
    action = RecoveryAction(
        recovery_case_id=case.id,
        policy_decision_id=uuid.uuid4(),  # We skip fk checks if not enforced, or need policy
        action_type="payment_link",
        status="EXECUTED",
        idempotency_key=f"key_{uuid.uuid4().hex}",
        scheduled_for=action_time,
        executed_at=action_time
    )
    # wait, policy_decision_id is a foreign key. We need to create a PolicyDecision
    from app.models.policy_decision import PolicyDecision
    from app.models.diagnosis import Diagnosis
    
    diag = Diagnosis(recovery_case_id=case.id, payment_attempt_id=base_scenario["attempt"].id, failure_category="test", is_retryable=True, root_cause_summary="test", rule_version="1.0")
    db_session.add(diag)
    db_session.flush()
    
    pol = PolicyDecision(recovery_case_id=case.id, diagnosis_id=diag.id, policy_version="1", decision="ALLOW", rules_evaluated=[], rejection_reasons=[], evaluated_intervention="payment_link")
    db_session.add(pol)
    db_session.flush()
    
    action.policy_decision_id = pol.id
    db_session.add(action)
    db_session.flush()
    
    # 2. Webhook Event now
    occurred_at = int(datetime.now(timezone.utc).timestamp())
    event = WebhookEvent(
        event_id=f"evt_{uuid.uuid4().hex}",
        event_type="payment.captured",
        payload={"payload": {"payment": {"entity": {"order_id": payment.razorpay_order_id, "amount": 10000, "created_at": occurred_at}}}},
        signature="sig",
        processing_status="RECEIVED"
    )
    db_session.add(event)
    db_session.flush()
    
    # 3. Process
    measurement = MeasurementService.process_success_event(db_session, event)
    
    assert measurement is not None
    assert measurement.attribution_status == "ATTRIBUTED"
    assert measurement.verified_recovered_amount == 10000
    assert measurement.attribution_basis["action_id"] == str(action.id)
    
    # Case closed
    db_session.refresh(case)
    assert case.status == "RECOVERED"
    assert case.closed_at is not None

def test_measurement_unattributed_late_success(db_session, base_scenario):
    case = base_scenario["case"]
    payment = base_scenario["payment"]
    
    # Setup Action 48 hours ago (outside 24h window)
    action_time = datetime.now(timezone.utc) - timedelta(hours=48)
    
    from app.models.policy_decision import PolicyDecision
    from app.models.diagnosis import Diagnosis
    diag = Diagnosis(recovery_case_id=case.id, payment_attempt_id=base_scenario["attempt"].id, failure_category="test", is_retryable=True, root_cause_summary="test", rule_version="1.0")
    db_session.add(diag)
    db_session.flush()
    pol = PolicyDecision(recovery_case_id=case.id, diagnosis_id=diag.id, policy_version="1", decision="ALLOW", rules_evaluated=[], rejection_reasons=[], evaluated_intervention="payment_link")
    db_session.add(pol)
    db_session.flush()
    
    action = RecoveryAction(
        recovery_case_id=case.id,
        policy_decision_id=pol.id,
        action_type="payment_link",
        status="EXECUTED",
        idempotency_key=f"key_{uuid.uuid4().hex}",
        scheduled_for=action_time,
        executed_at=action_time
    )
    db_session.add(action)
    db_session.flush()
    
    occurred_at = int(datetime.now(timezone.utc).timestamp())
    event = WebhookEvent(
        event_id=f"evt_{uuid.uuid4().hex}",
        event_type="payment.captured",
        payload={"payload": {"payment": {"entity": {"order_id": payment.razorpay_order_id, "amount": 10000, "created_at": occurred_at}}}},
        signature="sig",
        processing_status="RECEIVED"
    )
    db_session.add(event)
    db_session.flush()
    
    measurement = MeasurementService.process_success_event(db_session, event)
    
    assert measurement is not None
    assert measurement.attribution_status == "UNATTRIBUTED_SUCCESS"
    assert measurement.attribution_basis == {}
    
def test_measurement_unattributed_no_action(db_session, base_scenario):
    case = base_scenario["case"]
    payment = base_scenario["payment"]
    
    # No RecoveryAction
    occurred_at = int(datetime.now(timezone.utc).timestamp())
    event = WebhookEvent(
        event_id=f"evt_{uuid.uuid4().hex}",
        event_type="payment.captured",
        payload={"payload": {"payment": {"entity": {"order_id": payment.razorpay_order_id, "amount": 10000, "created_at": occurred_at}}}},
        signature="sig",
        processing_status="RECEIVED"
    )
    db_session.add(event)
    db_session.flush()
    
    measurement = MeasurementService.process_success_event(db_session, event)
    
    assert measurement is not None
    assert measurement.attribution_status == "UNATTRIBUTED_SUCCESS"

def test_attribution_window_boundaries(db_session, base_scenario):
    from app.models.policy_decision import PolicyDecision
    from app.models.diagnosis import Diagnosis
    
    def run_boundary_test(time_delta, expected_status):
        case = base_scenario["case"]
        payment = base_scenario["payment"]
        case.status = "OPEN"
        
        diag = Diagnosis(recovery_case_id=case.id, payment_attempt_id=base_scenario["attempt"].id, failure_category="test", is_retryable=True, root_cause_summary="test", rule_version="1.0")
        db_session.add(diag)
        db_session.flush()
        pol = PolicyDecision(recovery_case_id=case.id, diagnosis_id=diag.id, policy_version="1", decision="ALLOW", rules_evaluated=[], rejection_reasons=[], evaluated_intervention="payment_link")
        db_session.add(pol)
        db_session.flush()

        action_time = datetime.now(timezone.utc).replace(microsecond=0)
        action = RecoveryAction(
            recovery_case_id=case.id,
            policy_decision_id=pol.id,
            action_type="payment_link",
            status="EXECUTED",
            idempotency_key=f"key_{uuid.uuid4().hex}",
            scheduled_for=action_time,
            executed_at=action_time
        )
        db_session.add(action)
        db_session.flush()

        occurred_time = action_time + time_delta
        occurred_at_epoch = int(occurred_time.timestamp())
        
        event = WebhookEvent(
            event_id=f"evt_{uuid.uuid4().hex}",
            event_type="payment.captured",
            payload={"payload": {"payment": {"entity": {"order_id": payment.razorpay_order_id, "amount": 10000, "created_at": occurred_at_epoch}}}},
            signature="sig",
            processing_status="RECEIVED",
            received_at=occurred_time
        )
        db_session.add(event)
        db_session.flush()

        measurement = MeasurementService.process_success_event(db_session, event)
        assert measurement.attribution_status == expected_status
        
        # Cleanup for next boundary
        db_session.delete(measurement)
        db_session.delete(action)
        db_session.delete(event)
        db_session.delete(pol)
        db_session.delete(diag)
        db_session.flush()

    run_boundary_test(timedelta(seconds=0), "ATTRIBUTED")
    run_boundary_test(timedelta(hours=24), "ATTRIBUTED")
    run_boundary_test(timedelta(hours=24, seconds=1), "UNATTRIBUTED_SUCCESS")
    run_boundary_test(timedelta(seconds=-1), "UNATTRIBUTED_SUCCESS")
    
def test_duplicate_webhook_safely_ignored(db_session, base_scenario):
    # Mark case RECOVERED
    case = base_scenario["case"]
    case.status = "RECOVERED"
    db_session.flush()
    
    event = WebhookEvent(
        event_id=f"evt_{uuid.uuid4().hex}",
        event_type="payment.captured",
        payload={"payload": {"payment": {"entity": {"order_id": base_scenario["payment"].razorpay_order_id, "amount": 10000, "created_at": int(datetime.now().timestamp())}}}},
        signature="sig",
        processing_status="RECEIVED"
    )
    db_session.add(event)
    db_session.flush()
    
    measurement = MeasurementService.process_success_event(db_session, event)
    assert measurement is None  # Ignored

def test_multiple_actions_most_recent_eligible(db_session, base_scenario):
    case = base_scenario["case"]
    payment = base_scenario["payment"]
    
    from app.models.policy_decision import PolicyDecision
    from app.models.diagnosis import Diagnosis
    diag = Diagnosis(recovery_case_id=case.id, payment_attempt_id=base_scenario["attempt"].id, failure_category="test", is_retryable=True, root_cause_summary="test", rule_version="1.0")
    db_session.add(diag)
    db_session.flush()
    pol = PolicyDecision(recovery_case_id=case.id, diagnosis_id=diag.id, policy_version="1", decision="ALLOW", rules_evaluated=[], rejection_reasons=[], evaluated_intervention="payment_link")
    db_session.add(pol)
    db_session.flush()

    # Action 1: 48h ago
    time1 = datetime.now(timezone.utc) - timedelta(hours=48)
    a1 = RecoveryAction(
        recovery_case_id=case.id, policy_decision_id=pol.id, action_type="nudge", status="EXECUTED", idempotency_key=f"k1", scheduled_for=time1, executed_at=time1
    )
    # Action 2: 2h ago
    time2 = datetime.now(timezone.utc) - timedelta(hours=2)
    a2 = RecoveryAction(
        recovery_case_id=case.id, policy_decision_id=pol.id, action_type="payment_link", status="EXECUTED", idempotency_key=f"k2", scheduled_for=time2, executed_at=time2
    )
    # Action 3: In future (should not happen, but just to test executed_at <= occurred_at rule)
    time3 = datetime.now(timezone.utc) + timedelta(hours=2)
    a3 = RecoveryAction(
        recovery_case_id=case.id, policy_decision_id=pol.id, action_type="retry", status="EXECUTED", idempotency_key=f"k3", scheduled_for=time3, executed_at=time3
    )
    db_session.add_all([a1, a2, a3])
    db_session.flush()
    
    occurred_at = int(datetime.now(timezone.utc).timestamp())
    event = WebhookEvent(
        event_id=f"evt_{uuid.uuid4().hex}",
        event_type="payment.captured",
        payload={"payload": {"payment": {"entity": {"order_id": payment.razorpay_order_id, "amount": 10000, "created_at": occurred_at}}}},
        signature="sig",
        processing_status="RECEIVED"
    )
    db_session.add(event)
    db_session.flush()
    
    measurement = MeasurementService.process_success_event(db_session, event)
    assert measurement is not None
    assert measurement.attribution_status == "ATTRIBUTED"
    # Should be attributed to a2
    assert measurement.attribution_basis["action_id"] == str(a2.id)

def test_metrics_service(db_session, base_scenario):
    # Set up some data for metrics
    from app.models.policy_decision import PolicyDecision
    from app.models.diagnosis import Diagnosis
    case = base_scenario["case"]
    diag = Diagnosis(recovery_case_id=case.id, payment_attempt_id=base_scenario["attempt"].id, failure_category="test", is_retryable=True, root_cause_summary="test", rule_version="1.0")
    db_session.add(diag)
    db_session.flush()
    pol = PolicyDecision(recovery_case_id=case.id, diagnosis_id=diag.id, policy_version="1", decision="ALLOW", rules_evaluated=[], rejection_reasons=[], evaluated_intervention="payment_link")
    db_session.add(pol)
    db_session.flush()
    
    a1 = RecoveryAction(
        recovery_case_id=case.id, policy_decision_id=pol.id, action_type="nudge", status="EXECUTED", idempotency_key=f"k4", scheduled_for=datetime.now(), executed_at=datetime.now()
    )
    db_session.add(a1)
    db_session.flush()
    
    # Just insert a measurement
    m = RecoveryMeasurement(
        recovery_case_id=case.id,
        attribution_status="ATTRIBUTED",
        verified_recovered_amount=5000,
        currency="INR",
        attribution_basis={"action_id": str(a1.id)},
        time_to_recovery_seconds=100
    )
    db_session.add(m)
    case.status = "RECOVERED"
    db_session.flush()
    
    metrics = MetricsService.get_aggregate_metrics(db_session)
    assert metrics["total_cases"] >= 1
    assert metrics["recovered_revenue"] >= 5000
    assert "nudge" in metrics["intervention_metrics"]
    assert metrics["intervention_metrics"]["nudge"]["recoveries"] >= 1
