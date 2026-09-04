import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import BigInteger, ForeignKey, Index, Integer, String, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class RecoveryMeasurement(Base):
    __tablename__ = "recovery_measurements"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    recovery_case_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("recovery_cases.id"), unique=True, index=True)
    attribution_status: Mapped[str] = mapped_column(String(64))
    verified_recovered_amount: Mapped[int] = mapped_column(BigInteger)
    currency: Mapped[str] = mapped_column(String(3), server_default="INR")
    resolution_attempt_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("payment_attempts.id"))
    resolution_webhook_event_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("webhook_events.id"))
    time_to_recovery_seconds: Mapped[int | None] = mapped_column(Integer)
    attribution_basis: Mapped[dict[str, Any]] = mapped_column(JSONB)
    measured_at: Mapped[datetime] = mapped_column(
        server_default=text("NOW()"),
    )

    recovery_case: Mapped["RecoveryCase"] = relationship(back_populates="measurement")
    resolution_attempt: Mapped["PaymentAttempt | None"] = relationship(foreign_keys=[resolution_attempt_id])
    resolution_webhook: Mapped["WebhookEvent | None"] = relationship(foreign_keys=[resolution_webhook_event_id])
