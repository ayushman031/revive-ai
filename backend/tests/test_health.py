"""Tests for the API health endpoint."""

from fastapi.testclient import TestClient


def test_health_returns_ok(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200


def test_health_response_structure(client: TestClient) -> None:
    response = client.get("/health")
    assert response.json() == {"status": "ok", "service": "revive-api"}
