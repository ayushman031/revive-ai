"""Webhook event handlers for Phase 3."""

import logging
from typing import Any

from app.models.webhook_event import WebhookEvent
from app.services.diagnosis_service import process_payment_failed_diagnosis

logger = logging.getLogger(__name__)


def handle_payment_failed(event: WebhookEvent, session: Any = None) -> None:
    """Handle payment.failed events by running the deterministic diagnosis pipeline."""
    logger.info(f"Processing payment.failed event: {event.event_id}")
    if session and event.payload:
        process_payment_failed_diagnosis(session, event.payload)


def handle_payment_captured(event: WebhookEvent, session: Any = None) -> None:
    """Handle payment.captured events."""
    logger.info(f"Safely processed payment.captured event: {event.event_id}")


def handle_order_paid(event: WebhookEvent, session: Any = None) -> None:
    """Handle order.paid events."""
    logger.info(f"Safely processed order.paid event: {event.event_id}")



# Dispatch map for supported events
WEBHOOK_HANDLERS = {
    "payment.failed": handle_payment_failed,
    "payment.captured": handle_payment_captured,
    "order.paid": handle_order_paid,
}
