"""Comprehensive test suite for Phase 4: Deterministic Diagnosis."""

import uuid
import pytest
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models.constants import FailureCategory
from app.models.merchant import Merchant
from app.models.payment import Payment
from app.models.payment_attempt import PaymentAttempt
from app.models.recovery_case import RecoveryCase
from app.models.diagnosis import Diagnosis
from app.services.diagnosis_engine import DiagnosisEngine, redact_sensitive_text, sanitize_evidence_dict
from app.repositories.diagnosis import DiagnosisRepository
from app.services.diagnosis_service import process_payment_failed_diagnosis


class TestDiagnosisEngineTaxonomy:
    """Verify that every canonical diagnosis category is correctly identified."""

    def test_network_error_category(self):
        res = DiagnosisEngine.diagnose(
            error_code="GATEWAY_TIMEOUT",
            error_description="Connection timed out after 30000ms",
            error_source="gateway",
            error_step="payment_authorization",
            error_reason="gateway_timeout",
        )
        assert res.failure_category == FailureCategory.NETWORK_ERROR
        assert res.is_retryable is True
        assert res.confidence == 1.0
        assert res.evidence["matched_rule"] == "RULE_1_NETWORK_TIMEOUT"

    def test_gateway_error_category(self):
        res = DiagnosisEngine.diagnose(
            error_code="GATEWAY_ERROR",
            error_description="Acquirer system is temporarily down for maintenance",
            error_source="gateway",
            error_reason="service_unavailable",
        )
        assert res.failure_category == FailureCategory.GATEWAY_ERROR
        assert res.is_retryable is True
        assert res.confidence == 0.95
        assert res.evidence["matched_rule"] == "RULE_2_GATEWAY_INTERNAL_ERROR"

    def test_auth_failed_category(self):
        res = DiagnosisEngine.diagnose(
            error_code="BAD_REQUEST_PAYMENT_OTP_INCORRECT",
            error_description="Customer entered wrong OTP",
            error_source="customer",
            error_step="otp",
            error_reason="incorrect_otp",
        )
        assert res.failure_category == FailureCategory.AUTH_FAILED
        assert res.is_retryable is False
        assert res.confidence == 1.0
        assert res.evidence["matched_rule"] == "RULE_3_AUTHENTICATION_FAILURE"

    def test_insufficient_funds_category(self):
        res = DiagnosisEngine.diagnose(
            error_code="BAD_REQUEST_PAYMENT_ACCOUNT_INSUFFICIENT_BALANCE",
            error_description="Account has insufficient balance for transaction",
            error_source="bank",
            error_reason="insufficient_funds",
        )
        assert res.failure_category == FailureCategory.INSUFFICIENT_FUNDS
        assert res.is_retryable is True
        assert res.confidence == 1.0
        assert res.evidence["matched_rule"] == "RULE_4_INSUFFICIENT_FUNDS"

    def test_card_expired_category(self):
        res = DiagnosisEngine.diagnose(
            error_code="BAD_REQUEST_PAYMENT_CARD_EXPIRED",
            error_description="Card has expired on 08/24",
            error_source="customer",
            error_reason="card_expired",
        )
        assert res.failure_category == FailureCategory.CARD_EXPIRED
        assert res.is_retryable is False
        assert res.confidence == 1.0
        assert res.evidence["matched_rule"] == "RULE_5_CARD_EXPIRED"

    def test_bank_decline_category(self):
        res = DiagnosisEngine.diagnose(
            error_code="BAD_REQUEST_PAYMENT_DECLINED",
            error_description="Transaction not permitted by issuing bank",
            error_source="bank",
            error_reason="do_not_honor",
        )
        assert res.failure_category == FailureCategory.BANK_DECLINE
        assert res.is_retryable is False
        assert res.confidence == 0.9
        assert res.evidence["matched_rule"] == "RULE_6_BANK_DECLINE"

    def test_unknown_fallback_category(self):
        res = DiagnosisEngine.diagnose(
            error_code="CUSTOM_UNRECOGNIZED_CODE",
            error_description="Some weird error happened that is unclassified",
            error_source="unknown",
            error_reason="unknown_error",
        )
        assert res.failure_category == FailureCategory.UNKNOWN
        assert res.is_retryable is False
        assert res.confidence == 0.5
        assert res.evidence["matched_rule"] == "RULE_FALLBACK_UNKNOWN"

    def test_unknown_when_signals_are_none(self):
        res = DiagnosisEngine.diagnose()
        assert res.failure_category == FailureCategory.UNKNOWN
        assert res.is_retryable is False
        assert res.confidence == 0.5


class TestDiagnosisEnginePrecedenceAndConflicts:
    """Verify strict rule precedence when evidence has multiple conflicting signals."""

    def test_network_timeout_takes_precedence_over_bank_decline(self):
        # Network timeout takes precedence over bank source
        res = DiagnosisEngine.diagnose(
            error_code="TIMEOUT_WAITING_FOR_BANK",
            error_description="Timed out while waiting for bank response",
            error_source="bank",
            error_reason="gateway_timeout",
        )
        assert res.failure_category == FailureCategory.NETWORK_ERROR
        assert res.is_retryable is True
        assert res.evidence["matched_rule"] == "RULE_1_NETWORK_TIMEOUT"

    def test_gateway_error_takes_precedence_over_insufficient_funds(self):
        # Gateway error takes precedence over funds
        res = DiagnosisEngine.diagnose(
            error_code="GATEWAY_ERROR",
            error_description="Gateway internal server error checking balance",
            error_source="gateway",
            error_reason="internal_server_error",
        )
        assert res.failure_category == FailureCategory.GATEWAY_ERROR
        assert res.is_retryable is True
        assert res.evidence["matched_rule"] == "RULE_2_GATEWAY_INTERNAL_ERROR"

    def test_auth_failed_takes_precedence_over_insufficient_funds(self):
        # OTP failure step takes precedence over balance mentions in description
        res = DiagnosisEngine.diagnose(
            error_code="BAD_REQUEST_PAYMENT_OTP_INCORRECT",
            error_description="Customer entered wrong OTP for balance transfer",
            error_step="otp",
            error_reason="incorrect_otp",
        )
        assert res.failure_category == FailureCategory.AUTH_FAILED
        assert res.is_retryable is False

    def test_deterministic_repeated_execution(self):
        """Repeated evaluations with identical inputs yield identical outputs."""
        inputs = {
            "error_code": "BAD_REQUEST_PAYMENT_ACCOUNT_INSUFFICIENT_BALANCE",
            "error_description": "Low balance in customer account",
            "error_source": "bank",
            "error_step": "payment_authorization",
            "error_reason": "insufficient_funds",
        }
        res1 = DiagnosisEngine.diagnose(**inputs)
        res2 = DiagnosisEngine.diagnose(**inputs)
        assert res1 == res2


class TestRedactionAndSecurity:
    """Verify PAN, CVV, and sensitive data are never stored in evidence or logs."""

    def test_pan_redaction_in_text(self):
        raw_text = "Card 4111222233334444 failed validation"
        redacted = redact_sensitive_text(raw_text)
        assert "4111222233334444" not in redacted
        assert "[REDACTED_PAN]" in redacted

    def test_sensitive_dictionary_redaction(self):
        data = {
            "card_number": "4111222233334444",
            "cvv": "123",
            "pin": "9999",
            "safe_field": "some_value",
            "nested": {
                "token": "secret_abc",
                "message": "Failed card 5500000000000004",
            },
        }
        sanitized = sanitize_evidence_dict(data)
        assert sanitized["card_number"] == "[REDACTED]"
        assert sanitized["cvv"] == "[REDACTED]"
        assert sanitized["pin"] == "[REDACTED]"
        assert sanitized["safe_field"] == "some_value"
        assert sanitized["nested"]["token"] == "[REDACTED]"
        assert "5500000000000004" not in sanitized["nested"]["message"]
        assert "[REDACTED_PAN]" in sanitized["nested"]["message"]

    def test_evidence_in_engine_is_sanitized(self):
        res = DiagnosisEngine.diagnose(
            error_code="BAD_REQUEST",
            error_description="Customer with card 4111111111111111 had network timeout",
            error_source="gateway",
            error_reason="timeout",
        )
        assert "4111111111111111" not in str(res.evidence)
        assert "[REDACTED_PAN]" in str(res.evidence)


class TestDiagnosisPersistenceAndConcurrency:
    """Verify database persistence, idempotency, unique constraints, and RecoveryCase integration."""

    def test_diagnosis_persistence_and_recovery_case_integration(self, db_session: Session):
        merchant = Merchant(razorpay_account_id=f"acc_{uuid.uuid4().hex[:8]}", name="Test Merchant")
        db_session.add(merchant)
        db_session.flush()

        payment = Payment(
            merchant_id=merchant.id,
            razorpay_order_id=f"order_{uuid.uuid4().hex[:8]}",
            amount=250000,
            currency="INR",
            status="FAILED",
            payment_context="CHECKOUT",
        )
        db_session.add(payment)
        db_session.flush()

        attempt = PaymentAttempt(
            payment_id=payment.id,
            razorpay_payment_id=f"pay_{uuid.uuid4().hex[:8]}",
            attempt_number=1,
            method="card",
            status="FAILED",
            error_code="BAD_REQUEST_PAYMENT_ACCOUNT_INSUFFICIENT_BALANCE",
            error_description="Insufficient funds",
            attempted_at=payment.created_at,
        )
        db_session.add(attempt)
        db_session.flush()

        recovery_case = RecoveryCase(
            merchant_id=merchant.id,
            payment_id=payment.id,
            trigger_attempt_id=attempt.id,
            scenario="FAILED_PAYMENT",
            status="DIAGNOSED",
            revenue_at_risk=250000,
            currency="INR",
        )
        db_session.add(recovery_case)
        db_session.flush()

        repo = DiagnosisRepository(db_session)
        result = DiagnosisEngine.diagnose(
            error_code=attempt.error_code,
            error_description=attempt.error_description,
        )

        diagnosis, is_new = repo.create_or_get_diagnosis(
            recovery_case_id=recovery_case.id,
            payment_attempt_id=attempt.id,
            result=result,
            raw_error_code=attempt.error_code,
            raw_error_description=attempt.error_description,
        )

        assert is_new is True
        assert diagnosis.id is not None
        assert diagnosis.recovery_case_id == recovery_case.id
        assert diagnosis.payment_attempt_id == attempt.id
        assert diagnosis.failure_category == "INSUFFICIENT_FUNDS"
        assert diagnosis.is_retryable is True
        assert isinstance(diagnosis.evidence, dict)

        # Idempotent duplicate attempt on the same payment_attempt_id
        dup_diagnosis, is_new_dup = repo.create_or_get_diagnosis(
            recovery_case_id=recovery_case.id,
            payment_attempt_id=attempt.id,
            result=result,
        )
        assert is_new_dup is False
        assert dup_diagnosis.id == diagnosis.id

    def test_process_payment_failed_diagnosis_end_to_end(self, db_session: Session):
        """Test the end-to-end diagnosis handler with mock webhook payload."""
        pay_id = f"pay_e2e_{uuid.uuid4().hex[:8]}"
        order_id = f"order_e2e_{uuid.uuid4().hex[:8]}"
        acc_id = f"acc_e2e_{uuid.uuid4().hex[:8]}"

        payload = {
            "account_id": acc_id,
            "event": "payment.failed",
            "payload": {
                "payment": {
                    "entity": {
                        "id": pay_id,
                        "order_id": order_id,
                        "amount": 75000,
                        "currency": "INR",
                        "method": "card",
                        "error_code": "BAD_REQUEST_PAYMENT_CARD_EXPIRED",
                        "error_description": "Card has expired",
                        "error_source": "customer",
                        "error_step": "payment_initiation",
                        "error_reason": "card_expired",
                    }
                }
            },
        }

        diagnosis = process_payment_failed_diagnosis(db_session, payload)
        assert diagnosis is not None
        assert diagnosis.failure_category == "CARD_EXPIRED"
        assert diagnosis.is_retryable is False

        # Verify Payment and PaymentAttempt were persisted
        attempt = db_session.execute(
            select(PaymentAttempt).where(PaymentAttempt.razorpay_payment_id == pay_id)
        ).scalar_one()
        assert attempt.error_code == "BAD_REQUEST_PAYMENT_CARD_EXPIRED"
        assert attempt.diagnosis.id == diagnosis.id

        # Verify RecoveryCase was created
        recovery_case = db_session.execute(
            select(RecoveryCase).where(RecoveryCase.trigger_attempt_id == attempt.id)
        ).scalar_one()
        assert recovery_case.revenue_at_risk == 75000
        assert recovery_case.status == "DIAGNOSED"

        # Sending duplicate webhook payload should be idempotent
        dup_diagnosis = process_payment_failed_diagnosis(db_session, payload)
        assert dup_diagnosis.id == diagnosis.id

    def test_malformed_payment_reference_handled_safely(self, db_session: Session):
        """Ensure missing or malformed entities do not crash or create invalid records."""
        malformed_payload = {"event": "payment.failed", "payload": {}}
        diagnosis = process_payment_failed_diagnosis(db_session, malformed_payload)
        assert diagnosis is None
