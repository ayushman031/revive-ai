import uuid
from datetime import datetime
from typing import Any
from pydantic import BaseModel, Field

class RecoveryCaseSummary(BaseModel):
    id: uuid.UUID
    scenario: str
    status: str
    revenue_at_risk: int
    currency: str
    created_at: datetime
    closed_at: datetime | None = None
    razorpay_order_id: str | None = None

class PaginatedCasesResponse(BaseModel):
    items: list[RecoveryCaseSummary]
    total: int
    limit: int
    offset: int

class PaymentAttemptDetail(BaseModel):
    id: uuid.UUID
    method: str
    status: str
    error_code: str | None = None
    error_reason: str | None = None
    attempted_at: datetime

class DiagnosisDetail(BaseModel):
    id: uuid.UUID
    failure_category: str
    is_retryable: bool
    root_cause_summary: str
    diagnosed_at: datetime

class PredictionDetail(BaseModel):
    id: uuid.UUID
    risk_score: float
    recovery_probability_retry: float
    recovery_probability_link: float
    recovery_probability_nudge: float
    predicted_at: datetime

class RecommendationDetail(BaseModel):
    id: uuid.UUID
    recommended_intervention: str
    expected_recoverable_amount: int
    recommended_at: datetime

class PolicyDecisionDetail(BaseModel):
    id: uuid.UUID
    decision: str
    evaluated_intervention: str
    rejection_reasons: dict[str, Any] = Field(default_factory=dict)
    evaluated_at: datetime

class RecoveryActionDetail(BaseModel):
    id: uuid.UUID
    action_type: str
    status: str
    scheduled_for: datetime
    executed_at: datetime | None = None
    error_message: str | None = None

class RecoveryMeasurementDetail(BaseModel):
    id: uuid.UUID
    attribution_status: str
    verified_recovered_amount: int
    time_to_recovery_seconds: int | None = None
    attribution_basis: dict[str, Any] = Field(default_factory=dict)
    measured_at: datetime

class RecoveryCaseDetail(BaseModel):
    id: uuid.UUID
    merchant_id: uuid.UUID
    scenario: str
    status: str
    revenue_at_risk: int
    currency: str
    created_at: datetime
    closed_at: datetime | None = None

    payment_attempt: PaymentAttemptDetail | None = None
    diagnoses: list[DiagnosisDetail] = Field(default_factory=list)
    predictions: list[PredictionDetail] = Field(default_factory=list)
    recommendations: list[RecommendationDetail] = Field(default_factory=list)
    policy_decisions: list[PolicyDecisionDetail] = Field(default_factory=list)
    recovery_actions: list[RecoveryActionDetail] = Field(default_factory=list)
    measurement: RecoveryMeasurementDetail | None = None
