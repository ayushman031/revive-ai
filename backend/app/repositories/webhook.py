"""Webhook database repository."""

import uuid
from typing import Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from sqlalchemy import select

from app.models.webhook_event import WebhookEvent
from app.models.constants import ProcessingStatus


class WebhookRepository:
    """Repository for WebhookEvent persistence and atomic updates."""

    def __init__(self, session: Session):
        self.session = session

    def create_event(
        self,
        event_id: str,
        event_type: str,
        payload: dict[str, Any],
        signature: str,
    ) -> Tuple[WebhookEvent, bool]:
        """
        Idempotently insert a new webhook event.

        Returns:
            Tuple containing the WebhookEvent and a boolean indicating if it was newly created.
        """
        event = WebhookEvent(
            event_id=event_id,
            event_type=event_type,
            payload=payload,
            signature=signature,
            processing_status=ProcessingStatus.RECEIVED.value,
        )

        try:
            # We use a nested savepoint to catch IntegrityError safely
            with self.session.begin_nested():
                self.session.add(event)
            self.session.flush()
            return event, True
        except IntegrityError:
            # Rollback the nested transaction (savepoint), but the outer transaction remains valid
            # The event already exists, so we fetch it
            existing_event = self.session.execute(
                select(WebhookEvent).where(WebhookEvent.event_id == event_id)
            ).scalar_one()
            return existing_event, False

    def get_event_by_id(self, event_id: uuid.UUID) -> WebhookEvent | None:
        """Fetch a webhook event by its primary key UUID."""
        return self.session.get(WebhookEvent, event_id)

    def transition_status(
        self,
        event_id: uuid.UUID,
        from_status: ProcessingStatus,
        to_status: ProcessingStatus,
        error_message: str | None = None
    ) -> WebhookEvent | None:
        """
        Atomically transition an event's processing status using row locking.
        
        Returns the updated event if the transition was successful,
        or None if the event was not found or was not in the expected from_status.
        """
        # Select for update ensures no other worker can concurrently modify this row
        event = self.session.execute(
            select(WebhookEvent)
            .where(WebhookEvent.id == event_id)
            .with_for_update()
        ).scalar_one_or_none()

        if not event or event.processing_status != from_status.value:
            return None

        event.processing_status = to_status.value
        if error_message:
            event.error_message = error_message
            
        self.session.flush()
        return event
