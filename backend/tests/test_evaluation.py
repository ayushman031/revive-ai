import pytest
from app.evaluation.models import EvalTransaction, EvaluationMetrics
from app.evaluation.baselines import AlwaysRetryBaseline
from app.evaluation.revive_adapter import ReviveStrategyAdapter
from app.evaluation.simulator import EvaluationSimulator

def test_eval_metrics_zero_denominators():
    metrics = EvaluationMetrics()
    assert metrics.recovery_rate == 0.0
    assert metrics.unnecessary_intervention_rate == 0.0
    assert metrics.average_recovery_latency == 0.0

def test_always_retry_baseline():
    baseline = AlwaysRetryBaseline()
    txn = EvalTransaction(
        transaction_id="1", amount=1000, attempt_number=1,
        method="card", failure_category="insufficient_funds", is_retryable=1,
        ground_truth={"retry": 1, "link": 0, "nudge": 0}
    )
    assert baseline.evaluate(txn) == "retry"

def test_revive_adapter_policy_allow():
    adapter = ReviveStrategyAdapter()
    txn = EvalTransaction(
        transaction_id="1", amount=1000, attempt_number=1,
        method="card", failure_category="insufficient_funds", is_retryable=1,
        ground_truth={"retry": 1, "link": 0, "nudge": 0}
    )
    # Policy should ALLOW because attempt=1 (<3) and is_retryable=True
    res = adapter.evaluate_policy(txn)
    assert res.decision == "ALLOW"

def test_revive_adapter_policy_deny():
    adapter = ReviveStrategyAdapter()
    txn = EvalTransaction(
        transaction_id="2", amount=1000, attempt_number=4,
        method="card", failure_category="insufficient_funds", is_retryable=1,
        ground_truth={"retry": 1, "link": 0, "nudge": 0}
    )
    # Policy should DENY because attempt=4 (retry_limit)
    res = adapter.evaluate_policy(txn)
    assert res.decision == "DENY"
    assert "retry_limit" in res.rejection_reasons

def test_simulator_deterministic_run():
    simulator = EvaluationSimulator()
    baseline = AlwaysRetryBaseline()
    
    txn_success = EvalTransaction(
        transaction_id="1", amount=5000, attempt_number=1,
        method="upi", failure_category="gateway_timeout", is_retryable=1,
        ground_truth={"retry": 1, "link": 0, "nudge": 0}
    )
    txn_fail = EvalTransaction(
        transaction_id="2", amount=2000, attempt_number=1,
        method="upi", failure_category="gateway_timeout", is_retryable=1,
        ground_truth={"retry": 0, "link": 0, "nudge": 0}
    )
    
    metrics, results = simulator.simulate([txn_success, txn_fail], baseline)
    
    assert metrics.total_transactions == 2
    assert metrics.revenue_at_risk == 7000
    assert metrics.actions_taken == 2
    assert metrics.successful_recoveries == 1
    assert metrics.recovered_revenue == 5000
    
    # Retry cost is 0, so net should be 5000
    assert metrics.intervention_cost == 0
    assert metrics.net_recovered_revenue == 5000
    
    # One succeeded, one failed
    assert metrics.unnecessary_interventions == 1
    assert metrics.unnecessary_intervention_rate == 0.5
    
    # Average latency: 1 successful retry = 1 min
    assert metrics.average_recovery_latency == 1.0

def test_simulator_comparative_result():
    simulator = EvaluationSimulator()
    base = EvaluationMetrics(
        total_transactions=1, revenue_at_risk=1000, recovered_revenue=500, intervention_cost=0
    )
    rev = EvaluationMetrics(
        total_transactions=1, revenue_at_risk=1000, recovered_revenue=1000, intervention_cost=10
    )
    
    comps = simulator.compare(base, rev)
    
    rr_comp = next(c for c in comps if c.metric == "Recovery Rate")
    assert rr_comp.baseline_value == 0.5
    assert rr_comp.revive_value == 1.0
    assert rr_comp.absolute_delta == 0.5
    
    nrr_comp = next(c for c in comps if c.metric == "Net Recovered Revenue")
    assert nrr_comp.baseline_value == 500
    assert nrr_comp.revive_value == 990
    assert nrr_comp.absolute_delta == 490
    
    un_comp = next(c for c in comps if c.metric == "Unnecessary Interventions Rate")
    assert un_comp.baseline_value == 0.0
    assert un_comp.revive_value == 0.0
