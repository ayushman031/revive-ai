"""Webhook orchestration service."""

import logging
import json
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.integrations.razorpay.webhooks import verify_webhook_signature
from app.schemas.webhook import RazorpayWebhookEnvelope
from app.repositories.webhook import WebhookRepository
from app.workers.webhook_tasks import process_webhook_event

logger = logging.getLogger(__name__)


class WebhookIngestionError(Exception):
    """Base exception for webhook ingestion failures."""
    pass


class InvalidSignatureError(WebhookIngestionError):
    """Raised when the HMAC signature is invalid."""
    pass


class MalformedPayloadError(WebhookIngestionError):
    """Raised when the webhook payload is not valid JSON or missing required fields."""
    pass


class MissingEventIdError(WebhookIngestionError):
    """Raised when the required x-razorpay-event-id header is missing."""
    pass


def ingest_razorpay_webhook(
    payload_body: bytes,
    signature: str,
    event_id: str | None,
    secret: str,
    session: Session,
) -> dict:
    """
    Ingest a Razorpay webhook securely and idempotently.

    Args:
        payload_body: Raw request bytes.
        signature: The x-razorpay-signature header.
        event_id: The x-razorpay-event-id header.
        secret: The webhook secret for HMAC verification.
        session: Active database session.

    Returns:
        dict: A success message payload.
    
    Raises:
        InvalidSignatureError: If signature verification fails.
        MalformedPayloadError: If the payload cannot be parsed.
        MissingEventIdError: If event_id is missing.
    """
    # 1. Verify Event ID exists
    if not event_id:
        logger.warning("Rejecting webhook: Missing x-razorpay-event-id header")
        raise MissingEventIdError("Missing event ID")

    # 2. Verify Signature
    if not verify_webhook_signature(payload_body, signature, secret):
        logger.warning(f"Rejecting webhook {event_id}: Invalid signature")
        raise InvalidSignatureError("Invalid signature")

    # 3. Parse JSON and validate minimal schema
    try:
        payload_dict = json.loads(payload_body)
    except json.JSONDecodeError as e:
        logger.warning(f"Rejecting webhook {event_id}: Malformed JSON - {e}")
        raise MalformedPayloadError("Malformed JSON payload")

    try:
        envelope = RazorpayWebhookEnvelope.model_validate(payload_dict)
    except ValidationError as e:
        logger.warning(f"Rejecting webhook {event_id}: Schema validation failed - {e}")
        raise MalformedPayloadError("Missing required event fields")

    # 4. Persist idempotently
    repo = WebhookRepository(session)
    
    # We rely on the repository's internal savepoint/rollback for IntegrityError
    event, is_new = repo.create_event(
        event_id=event_id,
        event_type=envelope.event,
        payload=payload_dict,
        signature=signature,
    )
    
    # We must flush/commit to ensure the row exists before Celery tries to read it.
    # The router/caller should ideally manage the commit, but we must ensure it's
    # committed before enqueueing. To keep things clean, we assume the caller
    # manages the transaction, but we will dispatch celery AFTER transaction commits
    # by utilizing SQLAlchemy event listeners or explicitly returning the intent to dispatch.
    
    # However, for simplicity and explicit control in Phase 3, we dispatch here.
    # A standard pattern is to enqueue *after* the DB session commits. We'll handle
    # that by having the caller commit, and we just return a status.
    # Actually, let's dispatch right here but it relies on the caller committing 
    # immediately after. A safer way is to commit here explicitly if the service owns it.
    # But architectural rules: "Transactions must be explicit."
    
    # Since we need to return whether to dispatch, let's just return the event UUID and is_new flag
    # so the router can commit and THEN dispatch.
    
    return {
        "event_uuid": str(event.id),
        "is_new": is_new,
        "status": "success",
    }
