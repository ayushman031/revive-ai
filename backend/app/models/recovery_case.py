import uuid
from datetime import datetime

from sqlalchemy import BigInteger, ForeignKey, Index, String, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class RecoveryCase(Base):
    __tablename__ = "recovery_cases"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    merchant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("merchants.id"))
    payment_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("payments.id"), unique=True, index=True)
    trigger_attempt_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("payment_attempts.id"))
    scenario: Mapped[str] = mapped_column(String(64))
    status: Mapped[str] = mapped_column(String(32))
    revenue_at_risk: Mapped[int] = mapped_column(BigInteger)
    currency: Mapped[str] = mapped_column(String(3), server_default="INR")
    created_at: Mapped[datetime] = mapped_column(
        server_default=text("NOW()"),
        index=True,
    )
    updated_at: Mapped[datetime] = mapped_column(
        server_default=text("NOW()"),
        onupdate=text("NOW()"),
    )
    closed_at: Mapped[datetime | None]

    payment: Mapped["Payment"] = relationship(back_populates="recovery_case")
    trigger_attempt: Mapped["PaymentAttempt"] = relationship(foreign_keys=[trigger_attempt_id])
    
    diagnoses: Mapped[list["Diagnosis"]] = relationship(back_populates="recovery_case")
    predictions: Mapped[list["Prediction"]] = relationship(back_populates="recovery_case")
    recovery_actions: Mapped[list["RecoveryAction"]] = relationship(back_populates="recovery_case")
    measurement: Mapped["RecoveryMeasurement | None"] = relationship(back_populates="recovery_case", uselist=False)

    __table_args__ = (
        Index("ix_recovery_cases_merchant_status", "merchant_id", "status"),
    )
