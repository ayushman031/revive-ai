"""Celery tasks for processing webhooks."""

import uuid
import logging
from datetime import datetime, timezone

from app.workers.celery_app import celery_app
from app.core.database import get_session_factory
from app.repositories.webhook import WebhookRepository
from app.models.constants import ProcessingStatus
from app.services.webhook_handlers import WEBHOOK_HANDLERS

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, max_retries=3)
def process_webhook_event(self, event_id_str: str) -> None:
    """
    Process a webhook event asynchronously.
    
    Args:
        event_id_str: The primary key UUID string of the WebhookEvent.
    """
    try:
        event_id = uuid.UUID(event_id_str)
    except ValueError:
        logger.error(f"Invalid UUID string for event_id: {event_id_str}")
        return

    SessionFactory = get_session_factory()
    
    with SessionFactory() as session:
        repo = WebhookRepository(session)
        
        # Step 1: Transition status to PROCESSING atomically
        # We commit this immediately so other concurrent workers are blocked out
        with session.begin():
            event = repo.transition_status(
                event_id=event_id,
                from_status=ProcessingStatus.RECEIVED,
                to_status=ProcessingStatus.PROCESSING
            )
            if not event:
                logger.info(
                    f"Event {event_id} is not in RECEIVED state or not found. "
                    "Skipping processing (idempotent)."
                )
                return
                
            event_type = event.event_type

        logger.info(f"Worker started processing event {event_id} of type {event_type}")
        
        # Step 2: Process the event
        error_msg = None
        handler = WEBHOOK_HANDLERS.get(event_type)
        
        if handler:
            try:
                # We fetch the event again within a new transaction for the handler to use
                with session.begin():
                    current_event = repo.get_event_by_id(event_id)
                    handler(current_event, session=session)
            except Exception as e:
                logger.exception(f"Error executing handler for event {event_id}")
                error_msg = str(e)

        else:
            logger.warning(f"No handler registered for event type {event_type}")

        # Step 3: Transition to PROCESSED or FAILED
        final_status = ProcessingStatus.FAILED if error_msg else ProcessingStatus.PROCESSED
        
        with session.begin():
            event = repo.transition_status(
                event_id=event_id,
                from_status=ProcessingStatus.PROCESSING,
                to_status=final_status,
                error_message=error_msg
            )
            if event:
                event.processed_at = datetime.now(timezone.utc)
                
        logger.info(f"Worker completed event {event_id} with status {final_status.value}")
