import json
import os
from fastapi import APIRouter, HTTPException

router = APIRouter()

@router.get("/")
def get_evaluation_results():
    artifact_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../data/evaluation_results.json'))
    if not os.path.exists(artifact_path):
        raise HTTPException(status_code=404, detail="Evaluation artifact not found. Please run the evaluation simulator.")
    with open(artifact_path, 'r', encoding='utf-8') as f:
        return json.load(f)
