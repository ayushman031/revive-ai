import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import CheckConstraint, ForeignKey, Numeric, String, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Prediction(Base):
    __tablename__ = "predictions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    recovery_case_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("recovery_cases.id"), index=True)
    model_id: Mapped[str] = mapped_column(String(64))
    model_version: Mapped[str] = mapped_column(String(32))
    feature_version: Mapped[str] = mapped_column(String(32))
    features_snapshot: Mapped[dict[str, Any]] = mapped_column(JSONB)
    risk_score: Mapped[float] = mapped_column(Numeric(5, 4))
    recovery_probability_retry: Mapped[float] = mapped_column(Numeric(5, 4))
    recovery_probability_link: Mapped[float] = mapped_column(Numeric(5, 4))
    recovery_probability_nudge: Mapped[float] = mapped_column(Numeric(5, 4))
    predicted_at: Mapped[datetime] = mapped_column(
        server_default=text("NOW()"),
    )

    recovery_case: Mapped["RecoveryCase"] = relationship(back_populates="predictions")
    recommendations: Mapped[list["Recommendation"]] = relationship(back_populates="prediction")

    __table_args__ = (
        CheckConstraint("risk_score >= 0 AND risk_score <= 1", name="chk_pred_risk_score_range"),
        CheckConstraint(
            "recovery_probability_retry >= 0 AND recovery_probability_retry <= 1",
            name="chk_pred_prob_retry_range",
        ),
        CheckConstraint(
            "recovery_probability_link >= 0 AND recovery_probability_link <= 1",
            name="chk_pred_prob_link_range",
        ),
        CheckConstraint(
            "recovery_probability_nudge >= 0 AND recovery_probability_nudge <= 1",
            name="chk_pred_prob_nudge_range",
        ),
    )
