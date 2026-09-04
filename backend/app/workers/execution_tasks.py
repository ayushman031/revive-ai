"""Celery tasks for execution engine."""

import uuid
import logging
from app.workers.celery_app import celery_app
from app.core.database import get_session_factory
from app.services.execution_engine import ExecutionEngine

logger = logging.getLogger(__name__)

@celery_app.task(bind=True, max_retries=3)
def execute_recovery_action_task(self, action_id_str: str) -> None:
    try:
        action_id = uuid.UUID(action_id_str)
    except ValueError:
        logger.error(f"Invalid UUID string for action_id: {action_id_str}")
        return

    SessionFactory = get_session_factory()
    with SessionFactory() as session:
        engine = ExecutionEngine(session)
        success = engine.execute_action(action_id)
        if not success:
            logger.info(f"Execution of action {action_id} did not succeed (may have failed, or already executing).")
