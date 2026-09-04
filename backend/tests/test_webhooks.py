"""Tests for Phase 3: Webhook Ingestion and Idempotency."""

import json
import hmac
import hashlib
import uuid
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.main import app
from app.core.config import get_settings
from app.models.webhook_event import WebhookEvent
from app.models.constants import ProcessingStatus
from app.repositories.webhook import WebhookRepository
from app.workers.webhook_tasks import process_webhook_event


@pytest.fixture
def test_secret() -> str:
    return get_settings().razorpay_webhook_secret or "test_secret_for_tests"


@pytest.fixture
def generate_signature(test_secret: str):
    def _generate(payload: dict) -> str:
        msg = json.dumps(payload, separators=(',', ':')).encode("utf-8")
        return hmac.new(
            key=test_secret.encode("utf-8"),
            msg=msg,
            digestmod=hashlib.sha256
        ).hexdigest()
    return _generate


def test_webhook_ingestion_valid_signature(client: TestClient, db_session: Session, generate_signature):
    payload = {"event": "payment.failed", "payload": {"payment": {"entity": {"id": "pay_123"}}}}
    event_id = f"evt_{uuid.uuid4().hex}"
    
    # We must format exactly as the client sends it so the signature matches the raw body.
    raw_body = json.dumps(payload).encode("utf-8")
    sig = hmac.new(
        key=get_settings().razorpay_webhook_secret.encode("utf-8"),
        msg=raw_body,
        digestmod=hashlib.sha256
    ).hexdigest()
    
    response = client.post(
        "/api/v1/webhooks/razorpay",
        content=raw_body,
        headers={
            "x-razorpay-signature": sig,
            "x-razorpay-event-id": event_id,
            "Content-Type": "application/json"
        }
    )
    
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    
    # Verify persistence
    event = db_session.execute(
        select(WebhookEvent).where(WebhookEvent.event_id == event_id)
    ).scalar_one()
    
    assert event.event_type == "payment.failed"
    assert event.processing_status in (ProcessingStatus.RECEIVED.value, ProcessingStatus.PROCESSED.value)
    assert event.payload == payload


def test_webhook_ingestion_invalid_signature(client: TestClient):
    payload = {"event": "payment.failed"}
    event_id = f"evt_{uuid.uuid4().hex}"
    
    response = client.post(
        "/api/v1/webhooks/razorpay",
        json=payload,
        headers={
            "x-razorpay-signature": "invalid_signature",
            "x-razorpay-event-id": event_id
        }
    )
    
    assert response.status_code == 401
    assert "Invalid signature" in response.json()["detail"]


def test_webhook_ingestion_missing_signature(client: TestClient):
    response = client.post(
        "/api/v1/webhooks/razorpay",
        json={"event": "payment.failed"},
        headers={"x-razorpay-event-id": "evt_123"}
    )
    assert response.status_code == 400
    assert "Missing signature" in response.json()["detail"]


def test_webhook_ingestion_missing_event_id(client: TestClient):
    raw_body = json.dumps({"event": "payment.failed"}).encode("utf-8")
    sig = hmac.new(
        key=get_settings().razorpay_webhook_secret.encode("utf-8"),
        msg=raw_body,
        digestmod=hashlib.sha256
    ).hexdigest()

    response = client.post(
        "/api/v1/webhooks/razorpay",
        content=raw_body,
        headers={"x-razorpay-signature": sig}
    )
    assert response.status_code == 400
    assert "Missing event ID" in response.json()["detail"]


def test_webhook_ingestion_malformed_payload(client: TestClient):
    raw_body = b"not a json object"
    sig = hmac.new(
        key=get_settings().razorpay_webhook_secret.encode("utf-8"),
        msg=raw_body,
        digestmod=hashlib.sha256
    ).hexdigest()

    response = client.post(
        "/api/v1/webhooks/razorpay",
        content=raw_body,
        headers={
            "x-razorpay-signature": sig,
            "x-razorpay-event-id": "evt_123"
        }
    )
    assert response.status_code == 400
    assert "Malformed JSON" in response.json()["detail"]


def test_idempotent_duplicate_ingestion(client: TestClient, db_session: Session):
    payload = {"event": "payment.captured"}
    event_id = f"evt_{uuid.uuid4().hex}"
    
    raw_body = json.dumps(payload).encode("utf-8")
    sig = hmac.new(
        key=get_settings().razorpay_webhook_secret.encode("utf-8"),
        msg=raw_body,
        digestmod=hashlib.sha256
    ).hexdigest()
    
    headers = {
        "x-razorpay-signature": sig,
        "x-razorpay-event-id": event_id,
        "Content-Type": "application/json"
    }
    
    # First request
    r1 = client.post("/api/v1/webhooks/razorpay", content=raw_body, headers=headers)
    assert r1.status_code == 200
    
    # Ensure it's in DB
    events = db_session.execute(select(WebhookEvent).where(WebhookEvent.event_id == event_id)).scalars().all()
    assert len(events) == 1
    
    # Second request (duplicate)
    r2 = client.post("/api/v1/webhooks/razorpay", content=raw_body, headers=headers)
    assert r2.status_code == 200
    
    # Ensure it's STILL only 1 in DB
    events_after = db_session.execute(select(WebhookEvent).where(WebhookEvent.event_id == event_id)).scalars().all()
    assert len(events_after) == 1


def test_celery_task_processing_lifecycle(db_session: Session):
    repo = WebhookRepository(db_session)
    event_id_str = f"evt_{uuid.uuid4().hex}"
    event, is_new = repo.create_event(
        event_id=event_id_str,
        event_type="payment.failed",
        payload={"event": "payment.failed"},
        signature="dummy"
    )
    db_session.commit()
    
    # Run the celery task synchronously
    process_webhook_event(str(event.id))
    
    # Verify status changed to PROCESSED
    db_session.expire_all()
    processed_event = repo.get_event_by_id(event.id)
    assert processed_event.processing_status == ProcessingStatus.PROCESSED.value
    assert processed_event.processed_at is not None


def test_celery_task_unsupported_event(db_session: Session):
    repo = WebhookRepository(db_session)
    event_id_str = f"evt_{uuid.uuid4().hex}"
    event, is_new = repo.create_event(
        event_id=event_id_str,
        event_type="unknown.event",
        payload={"event": "unknown.event"},
        signature="dummy"
    )
    db_session.commit()
    
    # Run the celery task synchronously
    process_webhook_event(str(event.id))
    
    # Verify status changed to PROCESSED (safely acknowledged even if unhandled)
    db_session.expire_all()
    processed_event = repo.get_event_by_id(event.id)
    assert processed_event.processing_status == ProcessingStatus.PROCESSED.value
