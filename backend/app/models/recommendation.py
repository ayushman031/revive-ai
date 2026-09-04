import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import BigInteger, ForeignKey, Integer, String, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Recommendation(Base):
    __tablename__ = "recommendations"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    recovery_case_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("recovery_cases.id"), index=True)
    prediction_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("predictions.id"))
    recommended_intervention: Mapped[str] = mapped_column(String(64))
    ranking_rationale: Mapped[dict[str, Any]] = mapped_column(JSONB)
    expected_recoverable_amount: Mapped[int] = mapped_column(BigInteger)
    recommended_execution_delay_seconds: Mapped[int] = mapped_column(Integer)
    recommended_at: Mapped[datetime] = mapped_column(
        server_default=text("NOW()"),
    )

    prediction: Mapped["Prediction"] = relationship(back_populates="recommendations")
    policy_decisions: Mapped[list["PolicyDecision"]] = relationship(back_populates="recommendation")
