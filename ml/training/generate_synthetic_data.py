import argparse
import csv
import json
import random
import os
import sys

# Add backend directory to sys.path so we can import features
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../backend')))
from app.ml.features import FEATURE_VERSION

def generate_dataset(seed: int, num_samples: int, output_path: str):
    random.seed(seed)
    
    methods = ['card', 'upi', 'netbanking']
    failure_categories = ['insufficient_funds', 'authentication_failed', 'gateway_timeout', 'do_not_honor', 'invalid_card']
    
    with open(output_path, 'w', newline='') as csvfile:
        fieldnames = [
            'amount', 'attempt_number', 'method', 'failure_category', 'is_retryable',
            'target_retry', 'target_link', 'target_nudge'
        ]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        
        for _ in range(num_samples):
            method = random.choice(methods)
            failure_category = random.choice(failure_categories)
            attempt_number = random.choices([1, 2, 3], weights=[0.7, 0.2, 0.1])[0]
            amount = int(random.lognormvariate(8.5, 1.0)) * 100 # roughly up to 10k INR in paisa
            amount = max(10000, min(10000000, amount))
            
            # Deterministic is_retryable based on failure category
            is_retryable = 1 if failure_category in ['gateway_timeout', 'insufficient_funds'] else 0
            
            # Generate deterministic/probabilistic outcomes based on features
            
            # Retry success: high if gateway timeout, low otherwise. decreases with attempt number.
            prob_retry = 0.0
            if is_retryable:
                prob_retry = 0.8 if failure_category == 'gateway_timeout' else 0.4
            prob_retry *= (0.8 ** (attempt_number - 1))
            
            # Link success: higher for insufficient funds or do not honor, where user needs to use another method
            prob_link = 0.5
            if failure_category in ['insufficient_funds', 'do_not_honor']:
                prob_link = 0.7
            if amount > 500000: # high amount -> lower link success
                prob_link *= 0.6
                
            # Nudge success: generic low success, slightly higher for card/netbanking
            prob_nudge = 0.3
            if method in ['card', 'netbanking']:
                prob_nudge = 0.4
                
            target_retry = 1 if random.random() < prob_retry else 0
            target_link = 1 if random.random() < prob_link else 0
            target_nudge = 1 if random.random() < prob_nudge else 0
            
            writer.writerow({
                'amount': amount,
                'attempt_number': attempt_number,
                'method': method,
                'failure_category': failure_category,
                'is_retryable': is_retryable,
                'target_retry': target_retry,
                'target_link': target_link,
                'target_nudge': target_nudge,
            })
            
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--seed', type=int, default=42)
    parser.add_argument('--samples', type=int, default=10000)
    parser.add_argument('--output', type=str, default='ml/data/synthetic_dataset.csv')
    args = parser.parse_args()
    
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    generate_dataset(args.seed, args.samples, args.output)
    
    metadata = {
        "seed": args.seed,
        "samples": args.samples,
        "feature_version": FEATURE_VERSION
    }
    with open(os.path.join(os.path.dirname(args.output), 'dataset_metadata.json'), 'w') as f:
        json.dump(metadata, f, indent=2)
    print(f"Generated {args.samples} samples to {args.output}")
