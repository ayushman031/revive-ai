from app.evaluation.models import EvalTransaction, EvalResult, EvaluationMetrics, ComparativeResult
from app.evaluation.config import INTERVENTION_COSTS, INTERVENTION_LATENCY_MINUTES
from app.evaluation.revive_adapter import ReviveStrategyAdapter

class EvaluationSimulator:
    def __init__(self):
        # We use this adapter strictly for the policy engine adapter for the baseline too
        self.adapter = ReviveStrategyAdapter()

    def simulate(self, dataset: list[EvalTransaction], strategy) -> tuple[EvaluationMetrics, list[EvalResult]]:
        metrics = EvaluationMetrics()
        results = []

        for txn in dataset:
            metrics.total_transactions += 1
            metrics.revenue_at_risk += txn.amount

            # Both strategies undergo the exact same policy gate
            policy_result = self.adapter.evaluate_policy(txn)
            
            # The strategy selects an intervention
            intervention = strategy.evaluate(txn)
            
            action_taken = False
            policy_allowed = policy_result.decision == "ALLOW"
            policy_violation = False
            recovered_amount = 0
            intervention_cost = 0
            recovery_latency = 0
            unnecessary = False

            if policy_allowed:
                action_taken = True
                metrics.actions_taken += 1
                
                # Check Ground Truth (dataset has target_retry, target_link, etc.)
                target_col = f"{intervention}"
                success = txn.ground_truth.get(target_col, 0) == 1

                intervention_cost = INTERVENTION_COSTS.get(intervention, 0)
                metrics.intervention_cost += intervention_cost

                if success:
                    recovered_amount = txn.amount
                    metrics.recovered_revenue += recovered_amount
                    metrics.successful_recoveries += 1
                    
                    latency = INTERVENTION_LATENCY_MINUTES.get(intervention, 0)
                    recovery_latency = latency
                    metrics.sum_recovery_latency += latency
                else:
                    unnecessary = True
                    metrics.unnecessary_interventions += 1
            else:
                # If policy DENIES, we don't take action.
                # If an action WAS taken despite a DENY, it's a violation. We respect the gate here.
                # So policy_violation remains False since the system enforces it.
                pass

            result = EvalResult(
                transaction_id=txn.transaction_id,
                amount=txn.amount,
                intervention=intervention,
                action_taken=action_taken,
                policy_allowed=policy_allowed,
                recovered_amount=recovered_amount,
                intervention_cost=intervention_cost,
                net_recovered_amount=recovered_amount - intervention_cost,
                recovery_latency=recovery_latency,
                unnecessary_intervention=unnecessary,
                policy_violation=policy_violation
            )
            results.append(result)

        return metrics, results

    def compare(self, baseline_metrics: EvaluationMetrics, revive_metrics: EvaluationMetrics) -> list[ComparativeResult]:
        comparisons = []
        
        metrics_to_compare = [
            ("Recovery Rate", baseline_metrics.recovery_rate, revive_metrics.recovery_rate, True),
            ("Recovered Revenue", baseline_metrics.recovered_revenue, revive_metrics.recovered_revenue, False),
            ("Intervention Cost", baseline_metrics.intervention_cost, revive_metrics.intervention_cost, False),
            ("Net Recovered Revenue", baseline_metrics.net_recovered_revenue, revive_metrics.net_recovered_revenue, False),
            ("Unnecessary Interventions Rate", baseline_metrics.unnecessary_intervention_rate, revive_metrics.unnecessary_intervention_rate, True),
            ("Policy Violations", baseline_metrics.policy_violations, revive_metrics.policy_violations, False),
            ("Average Recovery Latency", baseline_metrics.average_recovery_latency, revive_metrics.average_recovery_latency, False),
        ]

        for name, base_val, rev_val, is_percentage in metrics_to_compare:
            abs_delta = rev_val - base_val
            rel_perc = None
            if base_val != 0:
                rel_perc = (abs_delta / abs(base_val)) * 100

            comparisons.append(ComparativeResult(
                metric=name,
                baseline_value=base_val,
                revive_value=rev_val,
                absolute_delta=abs_delta,
                relative_percentage=rel_perc
            ))

        return comparisons
