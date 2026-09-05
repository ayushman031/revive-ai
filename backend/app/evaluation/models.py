from dataclasses import dataclass
from typing import Optional

@dataclass(frozen=True)
class EvalTransaction:
    transaction_id: str
    amount: int
    attempt_number: int
    method: str
    failure_category: str
    is_retryable: int
    ground_truth: dict[str, int]

@dataclass(frozen=True)
class EvalResult:
    transaction_id: str
    amount: int
    intervention: str
    action_taken: bool
    policy_allowed: bool
    recovered_amount: int
    intervention_cost: int
    net_recovered_amount: int
    recovery_latency: int
    unnecessary_intervention: bool
    policy_violation: bool

@dataclass
class EvaluationMetrics:
    total_transactions: int = 0
    eligible_transactions: int = 0
    actions_taken: int = 0
    revenue_at_risk: int = 0
    recovered_revenue: int = 0
    intervention_cost: int = 0
    policy_violations: int = 0
    unnecessary_interventions: int = 0
    sum_recovery_latency: int = 0
    successful_recoveries: int = 0

    @property
    def recovery_rate(self) -> float:
        if self.revenue_at_risk == 0:
            return 0.0
        return self.recovered_revenue / self.revenue_at_risk

    @property
    def net_recovered_revenue(self) -> int:
        return self.recovered_revenue - self.intervention_cost

    @property
    def unnecessary_intervention_rate(self) -> float:
        if self.actions_taken == 0:
            return 0.0
        return self.unnecessary_interventions / self.actions_taken

    @property
    def average_recovery_latency(self) -> float:
        if self.successful_recoveries == 0:
            return 0.0
        return self.sum_recovery_latency / self.successful_recoveries

@dataclass
class ComparativeResult:
    metric: str
    baseline_value: float | int
    revive_value: float | int
    absolute_delta: float | int
    relative_percentage: Optional[float] = None
