"""Celery application configuration."""

from celery import Celery
from app.core.config import get_settings

settings = get_settings()

celery_app = Celery(
    "revive",
    broker=settings.redis_url,
    include=["app.workers.webhook_tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    # Ensure tasks are idempotent and can be safely retried
    task_acks_late=True,
    task_reject_on_worker_lost=True,
)
