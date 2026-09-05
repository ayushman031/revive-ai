import pytest
from fastapi.testclient import TestClient
import json
import os
from unittest.mock import patch, mock_open

from app.main import app

client = TestClient(app)

def test_get_evaluation_results_success():
    mock_data = {
        "metadata": {"dataset_size": 10000},
        "baseline": {"recovery_rate": 0.218},
        "revive": {"recovery_rate": 0.2249},
        "deltas": {}
    }
    mock_json = json.dumps(mock_data)
    
    with patch("os.path.exists", return_value=True):
        with patch("builtins.open", mock_open(read_data=mock_json)):
            response = client.get("/api/v1/evaluation")
            
    assert response.status_code == 200
    assert response.json() == mock_data

def test_get_evaluation_results_not_found():
    with patch("os.path.exists", return_value=False):
        response = client.get("/api/v1/evaluation")
        
    assert response.status_code == 404
