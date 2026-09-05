import argparse
import json
import os
import sys
from datetime import datetime

import joblib
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

# Add backend directory to sys.path so we can import features
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../backend')))
from app.ml.features import FEATURE_VERSION

MODEL_VERSION = "1.0.0"

def evaluate_model(model, X_test, y_test):
    y_pred = model.predict(X_test)
    y_prob = model.predict_proba(X_test)[:, 1]
    
    try:
        roc_auc = roc_auc_score(y_test, y_prob)
    except ValueError:
        roc_auc = None
        
    return {
        "accuracy": accuracy_score(y_test, y_pred),
        "precision": precision_score(y_test, y_pred, zero_division=0),
        "recall": recall_score(y_test, y_pred, zero_division=0),
        "f1": f1_score(y_test, y_pred, zero_division=0),
        "roc_auc": roc_auc,
        "class_balance_positive_ratio": float(y_test.mean())
    }

def train_and_save(target_name: str, X_train, y_train, X_val, y_val, X_test, y_test, preprocessor, output_dir: str, seed: int):
    print(f"Training model for {target_name}...")
    pipeline = Pipeline([
        ('preprocessor', preprocessor),
        ('classifier', LogisticRegression(random_state=seed, max_iter=1000, class_weight='balanced'))
    ])
    
    pipeline.fit(X_train, y_train)
    
    val_metrics = evaluate_model(pipeline, X_val, y_val)
    test_metrics = evaluate_model(pipeline, X_test, y_test)
    
    os.makedirs(output_dir, exist_ok=True)
    model_path = os.path.join(output_dir, 'model.joblib')
    joblib.dump(pipeline, model_path)
    
    metadata = {
        "target": target_name,
        "model_version": MODEL_VERSION,
        "feature_version": FEATURE_VERSION,
        "seed": seed,
        "training_timestamp": datetime.utcnow().isoformat() + "Z",
        "evaluation": {
            "validation": val_metrics,
            "test": test_metrics
        }
    }
    
    with open(os.path.join(output_dir, 'metadata.json'), 'w') as f:
        json.dump(metadata, f, indent=2)
        
    print(f"Saved {target_name} model to {output_dir}")
    print(f"Test metrics: {test_metrics}")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--dataset', type=str, default='ml/data/synthetic_dataset.csv')
    parser.add_argument('--seed', type=int, default=42)
    parser.add_argument('--output_dir', type=str, default='ml/models')
    args = parser.parse_args()
    
    print(f"Loading dataset from {args.dataset}")
    df = pd.read_csv(args.dataset)
    
    # Feature columns based on the feature schema
    feature_cols = ['amount', 'attempt_number', 'method', 'failure_category', 'is_retryable']
    
    X = df[feature_cols]
    y_retry = df['target_retry']
    y_link = df['target_link']
    y_nudge = df['target_nudge']
    
    # Preprocessor for numerical and categorical features
    numeric_features = ['amount', 'attempt_number', 'is_retryable']
    categorical_features = ['method', 'failure_category']
    
    preprocessor = ColumnTransformer(
        transformers=[
            ('num', StandardScaler(), numeric_features),
            ('cat', OneHotEncoder(handle_unknown='ignore'), categorical_features)
        ])
    
    # Split into train/val/test
    # 60% train, 20% val, 20% test
    X_train_val, X_test, y_retry_train_val, y_retry_test, y_link_train_val, y_link_test, y_nudge_train_val, y_nudge_test = train_test_split(
        X, y_retry, y_link, y_nudge, test_size=0.2, random_state=args.seed
    )
    
    X_train, X_val, y_retry_train, y_retry_val, y_link_train, y_link_val, y_nudge_train, y_nudge_val = train_test_split(
        X_train_val, y_retry_train_val, y_link_train_val, y_nudge_train_val, test_size=0.25, random_state=args.seed
    )
    
    train_and_save("target_retry", X_train, y_retry_train, X_val, y_retry_val, X_test, y_retry_test, preprocessor, os.path.join(args.output_dir, 'retry'), args.seed)
    train_and_save("target_link", X_train, y_link_train, X_val, y_link_val, X_test, y_link_test, preprocessor, os.path.join(args.output_dir, 'link'), args.seed)
    train_and_save("target_nudge", X_train, y_nudge_train, X_val, y_nudge_val, X_test, y_nudge_test, preprocessor, os.path.join(args.output_dir, 'nudge'), args.seed)

if __name__ == "__main__":
    main()
