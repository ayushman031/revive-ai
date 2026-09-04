import uuid
from datetime import datetime

from sqlalchemy import BigInteger, CheckConstraint, ForeignKey, Index, String, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Payment(Base):
    __tablename__ = "payments"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    merchant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("merchants.id"))
    customer_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("customers.id"))
    razorpay_order_id: Mapped[str | None] = mapped_column(String(64), index=True)
    razorpay_invoice_id: Mapped[str | None] = mapped_column(String(64))
    razorpay_subscription_id: Mapped[str | None] = mapped_column(String(64))
    currency: Mapped[str] = mapped_column(String(3), server_default="INR")
    amount: Mapped[int] = mapped_column(BigInteger)
    status: Mapped[str] = mapped_column(String(32))
    payment_context: Mapped[str] = mapped_column(String(32))
    created_at: Mapped[datetime] = mapped_column(
        server_default=text("NOW()"),
        index=True,
    )
    updated_at: Mapped[datetime] = mapped_column(
        server_default=text("NOW()"),
        onupdate=text("NOW()"),
    )

    merchant: Mapped["Merchant"] = relationship(back_populates="payments")
    customer: Mapped["Customer | None"] = relationship(back_populates="payments")
    attempts: Mapped[list["PaymentAttempt"]] = relationship(back_populates="payment", cascade="all, delete-orphan")
    recovery_case: Mapped["RecoveryCase | None"] = relationship(back_populates="payment", uselist=False)

    __table_args__ = (
        CheckConstraint("amount >= 0", name="chk_payment_amount_positive"),
        Index("ix_payments_merchant_status", "merchant_id", "status"),
    )
