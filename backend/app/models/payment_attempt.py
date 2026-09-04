import uuid
from datetime import datetime

from sqlalchemy import ForeignKey, Index, Integer, String, text, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class PaymentAttempt(Base):
    __tablename__ = "payment_attempts"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    payment_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("payments.id"))
    razorpay_payment_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    attempt_number: Mapped[int] = mapped_column(Integer)
    method: Mapped[str] = mapped_column(String(32))
    bank_or_issuer: Mapped[str | None] = mapped_column(String(64))
    status: Mapped[str] = mapped_column(String(32))
    error_code: Mapped[str | None] = mapped_column(String(64))
    error_description: Mapped[str | None] = mapped_column(Text)
    error_source: Mapped[str | None] = mapped_column(String(64))
    error_step: Mapped[str | None] = mapped_column(String(64))
    error_reason: Mapped[str | None] = mapped_column(String(64))
    attempted_at: Mapped[datetime]

    payment: Mapped["Payment"] = relationship(back_populates="attempts")
    diagnosis: Mapped["Diagnosis | None"] = relationship(back_populates="payment_attempt", uselist=False)

    __table_args__ = (
        Index("ix_payment_attempts_payment_attempt_number", "payment_id", "attempt_number"),
    )

