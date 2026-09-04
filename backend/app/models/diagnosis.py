import uuid
from datetime import datetime

from sqlalchemy import Boolean, ForeignKey, String, text, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Diagnosis(Base):
    __tablename__ = "diagnoses"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    recovery_case_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("recovery_cases.id"), index=True)
    failure_category: Mapped[str] = mapped_column(String(64))
    is_retryable: Mapped[bool] = mapped_column(Boolean)
    root_cause_summary: Mapped[str] = mapped_column(String(255))
    raw_error_code: Mapped[str | None] = mapped_column(String(64))
    raw_error_description: Mapped[str | None] = mapped_column(Text)
    rule_version: Mapped[str] = mapped_column(String(32))
    diagnosed_at: Mapped[datetime] = mapped_column(
        server_default=text("NOW()"),
    )

    recovery_case: Mapped["RecoveryCase"] = relationship(back_populates="diagnoses")
