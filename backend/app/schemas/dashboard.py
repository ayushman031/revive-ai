from typing import Any
from pydantic import BaseModel, Field

class ActionMetrics(BaseModel):
    total: int = 0
    successful: int = 0
    failed: int = 0
    pending: int = 0

class InterventionMetric(BaseModel):
    recoveries: int = 0
    recovered_revenue: int = 0

class DashboardMetricsResponse(BaseModel):
    total_failed_attempts: int = 0
    total_cases: int = 0
    open_cases: int = 0
    recovered_cases: int = 0
    recovery_rate: float = 0.0
    revenue_at_risk: int = 0
    recovered_revenue: int = 0
    attributed_revenue: int = 0
    unattributed_revenue: int = 0
    actions: ActionMetrics
    policy_decisions: dict[str, int] = Field(default_factory=dict)
    intervention_metrics: dict[str, InterventionMetric] = Field(default_factory=dict)
    diagnosis_metrics: dict[str, InterventionMetric] = Field(default_factory=dict)
    method_metrics: dict[str, InterventionMetric] = Field(default_factory=dict)
