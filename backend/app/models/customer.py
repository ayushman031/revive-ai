import uuid
from datetime import datetime

from sqlalchemy import ForeignKey, Index, String, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Customer(Base):
    __tablename__ = "customers"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    merchant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("merchants.id"), index=True)
    razorpay_customer_id: Mapped[str | None] = mapped_column(String(64))
    email_hash: Mapped[str | None] = mapped_column(String(64))
    phone_hash: Mapped[str | None] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(
        server_default=text("NOW()"),
    )
    updated_at: Mapped[datetime] = mapped_column(
        server_default=text("NOW()"),
        onupdate=text("NOW()"),
    )

    merchant: Mapped["Merchant"] = relationship(back_populates="customers")
    payments: Mapped[list["Payment"]] = relationship(back_populates="customer")

    __table_args__ = (
        UniqueConstraint("merchant_id", "razorpay_customer_id", name="uq_merchant_razorpay_customer"),
        Index("ix_customers_merchant_email", "merchant_id", "email_hash"),
        Index("ix_customers_merchant_phone", "merchant_id", "phone_hash"),
    )
