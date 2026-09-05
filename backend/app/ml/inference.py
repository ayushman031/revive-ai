import json
import logging
import os
from typing import Any

import joblib
import pandas as pd

logger = logging.getLogger(__name__)

class InferenceEngine:
    def __init__(self, models_dir: str):
        self.models_dir = os.path.abspath(models_dir)
        self.models = {}
        self.metadata = {}
        self._load_models()

    def _load_models(self):
        targets = ["retry", "link", "nudge"]
        for target in targets:
            model_path = os.path.join(self.models_dir, target, "model.joblib")
            meta_path = os.path.join(self.models_dir, target, "metadata.json")
            
            if os.path.exists(model_path) and os.path.exists(meta_path):
                try:
                    self.models[target] = joblib.load(model_path)
                    with open(meta_path, 'r') as f:
                        self.metadata[target] = json.load(f)
                    logger.info(f"Loaded ML model for {target}")
                except Exception as e:
                    logger.error(f"Failed to load model for {target}: {e}")
                    self.models[target] = None
            else:
                logger.warning(f"Model or metadata missing for {target} at {self.models_dir}")
                self.models[target] = None

    def predict(self, features: dict[str, Any]) -> dict[str, Any]:
        """
        Returns probabilities for each intervention and model versions.
        """
        df = pd.DataFrame([features])
        
        probabilities = {}
        versions = {}
        feature_versions = {}
        
        for target, model in self.models.items():
            if model is not None:
                prob = model.predict_proba(df)[0][1]
                probabilities[f"recovery_probability_{target}"] = float(prob)
                versions[target] = self.metadata[target].get("model_version", "unknown")
                feature_versions[target] = self.metadata[target].get("feature_version", "unknown")
            else:
                probabilities[f"recovery_probability_{target}"] = None
                versions[target] = None
                feature_versions[target] = None
                
        return {
            "probabilities": probabilities,
            "model_versions": versions,
            "feature_versions": feature_versions
        }

# Global singleton or injected instance
_engine = None

def get_inference_engine() -> InferenceEngine:
    global _engine
    if _engine is None:
        # In a real app, models_dir would come from config.
        # We assume the API is run from backend/ or root, so we resolve relative to root
        root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../"))
        models_dir = os.path.join(root_dir, "ml", "models")
        _engine = InferenceEngine(models_dir)
    return _engine
