"""Webhook event handlers for Phase 3."""

import logging
from typing import Any

from app.models.webhook_event import WebhookEvent

logger = logging.getLogger(__name__)


def handle_payment_failed(event: WebhookEvent) -> None:
    """Handle payment.failed events."""
    # Phase 3 stub: Just acknowledge safely.
    logger.info(f"Safely processed payment.failed event: {event.event_id}")


def handle_payment_captured(event: WebhookEvent) -> None:
    """Handle payment.captured events."""
    # Phase 3 stub: Just acknowledge safely.
    logger.info(f"Safely processed payment.captured event: {event.event_id}")


def handle_order_paid(event: WebhookEvent) -> None:
    """Handle order.paid events."""
    # Phase 3 stub: Just acknowledge safely.
    logger.info(f"Safely processed order.paid event: {event.event_id}")


# Dispatch map for supported events
WEBHOOK_HANDLERS = {
    "payment.failed": handle_payment_failed,
    "payment.captured": handle_payment_captured,
    "order.paid": handle_order_paid,
}
