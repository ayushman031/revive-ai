import argparse
import csv
import sys
import os
import json

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.evaluation.models import EvalTransaction
from app.evaluation.baselines import AlwaysRetryBaseline
from app.evaluation.revive_adapter import ReviveStrategyAdapter
from app.evaluation.simulator import EvaluationSimulator

def load_dataset(csv_path: str) -> list[EvalTransaction]:
    dataset = []
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader):
            txn = EvalTransaction(
                transaction_id=f"txn_{i}",
                amount=int(row['amount']),
                attempt_number=int(row['attempt_number']),
                method=row['method'],
                failure_category=row['failure_category'],
                is_retryable=int(row['is_retryable']),
                ground_truth={
                    "retry": int(row['target_retry']),
                    "link": int(row['target_link']),
                    "nudge": int(row['target_nudge']),
                }
            )
            dataset.append(txn)
    return dataset

def format_percentage(val: float) -> str:
    return f"{val * 100:.2f}%"

def main():
    parser = argparse.ArgumentParser(description="Run Phase 7 Evaluation")
    parser.add_argument('--dataset', type=str, default='../ml/data/synthetic_dataset.csv')
    args = parser.parse_args()

    print("Loading dataset...")
    dataset = load_dataset(args.dataset)
    
    simulator = EvaluationSimulator()
    
    # 1. Baseline
    baseline_strategy = AlwaysRetryBaseline()
    baseline_metrics, _ = simulator.simulate(dataset, baseline_strategy)
    
    # 2. REVIVE
    revive_strategy = ReviveStrategyAdapter()
    revive_metrics, _ = simulator.simulate(dataset, revive_strategy)
    
    # 3. Compare
    comparisons = simulator.compare(baseline_metrics, revive_metrics)
    
    # 4. Report
    print("\nPHASE 7 EVALUATION\n")
    print("Dataset:")
    print(f"Transactions: {baseline_metrics.total_transactions}")
    print(f"Revenue at Risk: INR {baseline_metrics.revenue_at_risk / 100:,.2f}\n")
    
    print("BASELINE")
    print(f"Recovery Rate: {format_percentage(baseline_metrics.recovery_rate)}")
    print(f"Recovered Revenue: INR {baseline_metrics.recovered_revenue / 100:,.2f}")
    print(f"Intervention Cost: INR {baseline_metrics.intervention_cost / 100:,.2f}")
    print(f"Net Recovered Revenue: INR {baseline_metrics.net_recovered_revenue / 100:,.2f}")
    print(f"Unnecessary Interventions: {format_percentage(baseline_metrics.unnecessary_intervention_rate)}")
    print(f"Policy Violations: {baseline_metrics.policy_violations}\n")
    
    print("REVIVE")
    print(f"Recovery Rate: {format_percentage(revive_metrics.recovery_rate)}")
    print(f"Recovered Revenue: INR {revive_metrics.recovered_revenue / 100:,.2f}")
    print(f"Intervention Cost: INR {revive_metrics.intervention_cost / 100:,.2f}")
    print(f"Net Recovered Revenue: INR {revive_metrics.net_recovered_revenue / 100:,.2f}")
    print(f"Unnecessary Interventions: {format_percentage(revive_metrics.unnecessary_intervention_rate)}")
    print(f"Policy Violations: {revive_metrics.policy_violations}\n")
    
    print("DELTA")
    for comp in comparisons:
        is_perc = comp.metric in ["Recovery Rate", "Unnecessary Interventions Rate"]
        delta_str = ""
        if is_perc:
            # We display absolute percentage point delta for rates
            val = comp.absolute_delta * 100
            delta_str = f"{val:+.2f} pp"
        elif comp.metric == "Policy Violations" or comp.metric == "Average Recovery Latency":
            delta_str = f"{comp.absolute_delta:+.2f}"
        else:
            delta_str = f"INR {comp.absolute_delta / 100:+,.2f}"
            
        print(f"{comp.metric}: {delta_str}")
        
    # 5. Export JSON artifact
    artifact_path = os.path.join(os.path.dirname(__file__), '../data/evaluation_results.json')
    os.makedirs(os.path.dirname(artifact_path), exist_ok=True)
    
    # We will build a structured dict with all the results
    results_dict = {
        "metadata": {
            "dataset_size": baseline_metrics.total_transactions,
            "revenue_at_risk": baseline_metrics.revenue_at_risk,
            "assumptions": {
                "costs": {
                    "retry": 0,
                    "link": 10,
                    "nudge": 2
                },
                "latency_minutes": {
                    "retry": 1,
                    "link": 120,
                    "nudge": 1440
                }
            }
        },
        "baseline": {
            "recovery_rate": baseline_metrics.recovery_rate,
            "recovered_revenue": baseline_metrics.recovered_revenue,
            "intervention_cost": baseline_metrics.intervention_cost,
            "net_recovered_revenue": baseline_metrics.net_recovered_revenue,
            "unnecessary_intervention_rate": baseline_metrics.unnecessary_intervention_rate,
            "policy_violations": baseline_metrics.policy_violations,
            "average_recovery_latency": baseline_metrics.average_recovery_latency
        },
        "revive": {
            "recovery_rate": revive_metrics.recovery_rate,
            "recovered_revenue": revive_metrics.recovered_revenue,
            "intervention_cost": revive_metrics.intervention_cost,
            "net_recovered_revenue": revive_metrics.net_recovered_revenue,
            "unnecessary_intervention_rate": revive_metrics.unnecessary_intervention_rate,
            "policy_violations": revive_metrics.policy_violations,
            "average_recovery_latency": revive_metrics.average_recovery_latency
        },
        "deltas": {
            comp.metric: {
                "absolute_delta": comp.absolute_delta,
                "relative_percentage": comp.relative_percentage
            } for comp in comparisons
        }
    }
    
    with open(artifact_path, 'w', encoding='utf-8') as f:
        json.dump(results_dict, f, indent=2)
    print(f"\nArtifact saved to {artifact_path}")

if __name__ == "__main__":
    main()
