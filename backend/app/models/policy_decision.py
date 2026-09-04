import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import ForeignKey, Index, String, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class PolicyDecision(Base):
    __tablename__ = "policy_decisions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    recovery_case_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("recovery_cases.id"))
    diagnosis_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("diagnoses.id"), index=True)
    recommendation_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("recommendations.id"))
    policy_version: Mapped[str] = mapped_column(String(32))
    evaluated_intervention: Mapped[str] = mapped_column(String(64))
    decision: Mapped[str] = mapped_column(String(32))
    rules_evaluated: Mapped[dict[str, Any]] = mapped_column(JSONB)
    rejection_reasons: Mapped[dict[str, Any]] = mapped_column(JSONB)
    evaluated_at: Mapped[datetime] = mapped_column(
        server_default=text("NOW()"),
    )

    recommendation: Mapped["Recommendation | None"] = relationship(back_populates="policy_decisions")
    diagnosis: Mapped["Diagnosis"] = relationship(back_populates="policy_decisions")
    recovery_actions: Mapped[list["RecoveryAction"]] = relationship(back_populates="policy_decision")

    __table_args__ = (
        Index("ix_policy_decisions_case_decision", "recovery_case_id", "decision"),
    )
