import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import ForeignKey, Index, String, text, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class RecoveryAction(Base):
    __tablename__ = "recovery_actions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    recovery_case_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("recovery_cases.id"), index=True)
    policy_decision_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("policy_decisions.id"))
    action_type: Mapped[str] = mapped_column(String(64))
    status: Mapped[str] = mapped_column(String(32))
    idempotency_key: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    scheduled_for: Mapped[datetime]
    executed_at: Mapped[datetime | None]
    external_reference_id: Mapped[str | None] = mapped_column(String(128))
    execution_payload: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    execution_response: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    error_message: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        server_default=text("NOW()"),
    )
    updated_at: Mapped[datetime] = mapped_column(
        server_default=text("NOW()"),
        onupdate=text("NOW()"),
    )

    recovery_case: Mapped["RecoveryCase"] = relationship(back_populates="recovery_actions")
    policy_decision: Mapped["PolicyDecision"] = relationship(back_populates="recovery_actions")

    __table_args__ = (
        Index("ix_recovery_actions_status_scheduled", "status", "scheduled_for"),
    )
