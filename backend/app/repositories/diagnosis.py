"""Repository for Diagnosis persistence and atomic operations."""

import uuid
from typing import Tuple, Any
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from sqlalchemy import select

from app.models.diagnosis import Diagnosis
from app.services.diagnosis_engine import DiagnosisResult


class DiagnosisRepository:
    """Repository for Diagnosis entity."""

    def __init__(self, session: Session):
        self.session = session

    def create_or_get_diagnosis(
        self,
        recovery_case_id: uuid.UUID,
        payment_attempt_id: uuid.UUID,
        result: DiagnosisResult,
        raw_error_code: str | None = None,
        raw_error_description: str | None = None,
    ) -> Tuple[Diagnosis, bool]:
        """
        Idempotently persist a diagnosis for a payment attempt.

        Returns:
            Tuple[Diagnosis, bool]: (diagnosis, is_new)
        """
        diagnosis = Diagnosis(
            recovery_case_id=recovery_case_id,
            payment_attempt_id=payment_attempt_id,
            failure_category=result.failure_category.value,
            is_retryable=result.is_retryable,
            root_cause_summary=result.root_cause_summary,
            raw_error_code=raw_error_code,
            raw_error_description=raw_error_description,
            evidence=result.evidence,
            rule_version=result.rule_version,
        )

        try:
            with self.session.begin_nested():
                self.session.add(diagnosis)
            self.session.flush()
            return diagnosis, True
        except IntegrityError:
            # Row already exists for payment_attempt_id due to unique constraint
            existing = self.session.execute(
                select(Diagnosis).where(Diagnosis.payment_attempt_id == payment_attempt_id)
            ).scalar_one()
            return existing, False

    def get_by_payment_attempt_id(self, payment_attempt_id: uuid.UUID) -> Diagnosis | None:
        """Fetch diagnosis by payment_attempt_id."""
        return self.session.execute(
            select(Diagnosis).where(Diagnosis.payment_attempt_id == payment_attempt_id)
        ).scalar_one_or_none()
