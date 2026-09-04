"""Deterministic payment diagnosis service for Phase 4."""

import logging
import uuid
from datetime import datetime, timezone
from typing import Any
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models.merchant import Merchant
from app.models.payment import Payment
from app.models.payment_attempt import PaymentAttempt
from app.models.recovery_case import RecoveryCase
from app.models.diagnosis import Diagnosis
from app.services.diagnosis_engine import DiagnosisEngine, redact_sensitive_text
from app.repositories.diagnosis import DiagnosisRepository

logger = logging.getLogger(__name__)


def process_payment_failed_diagnosis(session: Session, payload: dict[str, Any]) -> Diagnosis | None:
    """
    Process payment failure:
    1. Extract payment and attempt entities safely from Razorpay payload.
    2. Upsert Merchant (or default merchant placeholder for the account).
    3. Upsert Payment record.
    4. Upsert PaymentAttempt with failure details.
    5. Find or create active RecoveryCase for this payment.
    6. Execute deterministic DiagnosisEngine.
    7. Persist Diagnosis idempotently linked to RecoveryCase and PaymentAttempt.
    """
    payment_entity = payload.get("payload", {}).get("payment", {}).get("entity", {})
    if not payment_entity:
        logger.warning("No payment entity found in payload; skipping diagnosis.")
        return None

    razorpay_payment_id = payment_entity.get("id")
    if not razorpay_payment_id:
        logger.warning("No razorpay_payment_id in payment entity; skipping diagnosis.")
        return None

    # Step 1: Merchant
    # In Razorpay webhooks, account_id might be at root or in headers, default to entity or fallback
    account_id = payload.get("account_id") or "acc_default"
    merchant = session.execute(
        select(Merchant).where(Merchant.razorpay_account_id == account_id)
    ).scalar_one_or_none()

    if not merchant:
        merchant = Merchant(
            razorpay_account_id=account_id,
            name="Default Merchant",
            status="ACTIVE",
        )
        session.add(merchant)
        session.flush()

    # Step 2: Payment
    # Unique per razorpay_order_id or razorpay_payment_id fallback
    order_id = payment_entity.get("order_id")
    amount = int(payment_entity.get("amount", 0))
    currency = payment_entity.get("currency", "INR")
    method = payment_entity.get("method", "card")

    # Check if Payment exists
    payment = None
    if order_id:
        payment = session.execute(
            select(Payment).where(Payment.razorpay_order_id == order_id)
        ).scalar_one_or_none()

    if not payment:
        payment = Payment(
            merchant_id=merchant.id,
            razorpay_order_id=order_id,
            razorpay_invoice_id=payment_entity.get("invoice_id"),
            currency=currency,
            amount=amount,
            status="FAILED",
            payment_context="E_COMMERCE",
        )
        session.add(payment)
        session.flush()
    else:
        payment.status = "FAILED"
        session.flush()

    # Step 3: PaymentAttempt
    attempt = session.execute(
        select(PaymentAttempt).where(PaymentAttempt.razorpay_payment_id == razorpay_payment_id)
    ).scalar_one_or_none()

    error_code = payment_entity.get("error_code")
    raw_error_desc = payment_entity.get("error_description")
    error_desc = redact_sensitive_text(raw_error_desc)
    error_source = payment_entity.get("error_source")
    error_step = payment_entity.get("error_step")
    error_reason = payment_entity.get("error_reason")
    bank = payment_entity.get("bank") or payment_entity.get("issuer")

    if not attempt:
        # Determine attempt number
        existing_attempts_count = session.execute(
            select(PaymentAttempt).where(PaymentAttempt.payment_id == payment.id)
        ).scalars().all()
        attempt_number = len(existing_attempts_count) + 1

        attempt = PaymentAttempt(
            payment_id=payment.id,
            razorpay_payment_id=razorpay_payment_id,
            attempt_number=attempt_number,
            method=method,
            bank_or_issuer=bank,
            status="FAILED",
            error_code=error_code,
            error_description=error_desc,
            error_source=error_source,
            error_step=error_step,
            error_reason=error_reason,
            attempted_at=datetime.now(timezone.utc),
        )
        session.add(attempt)
        session.flush()

    # Step 4: RecoveryCase
    recovery_case = session.execute(
        select(RecoveryCase).where(RecoveryCase.payment_id == payment.id)
    ).scalar_one_or_none()

    if not recovery_case:
        recovery_case = RecoveryCase(
            merchant_id=merchant.id,
            payment_id=payment.id,
            trigger_attempt_id=attempt.id,
            scenario="FAILED_PAYMENT",
            status="DIAGNOSED",
            revenue_at_risk=amount,
            currency=currency,
        )
        session.add(recovery_case)
        session.flush()
    else:
        recovery_case.status = "DIAGNOSED"
        recovery_case.trigger_attempt_id = attempt.id
        session.flush()

    # Step 5: Execute Deterministic Diagnosis
    diagnosis_result = DiagnosisEngine.diagnose(
        error_code=attempt.error_code,
        error_description=attempt.error_description,
        error_source=attempt.error_source,
        error_step=attempt.error_step,
        error_reason=attempt.error_reason,
        method=attempt.method,
    )

    # Step 6: Persist Diagnosis idempotently
    repo = DiagnosisRepository(session)
    diagnosis, is_new = repo.create_or_get_diagnosis(
        recovery_case_id=recovery_case.id,
        payment_attempt_id=attempt.id,
        result=diagnosis_result,
        raw_error_code=error_code,
        raw_error_description=error_desc,
    )

    logger.info(
        f"Diagnosed attempt {razorpay_payment_id}: category={diagnosis.failure_category}, "
        f"retryable={diagnosis.is_retryable}, is_new={is_new}"
    )

    return diagnosis
