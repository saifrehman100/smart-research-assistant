"""Celery tasks for async processing."""

from celery import Celery

from app.config import settings

# Initialize Celery
celery_app = Celery(
    "research_assistant",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
)

# Configure Celery
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
)

# Import tasks to register them
from app.tasks.document_processing import process_document_task  # noqa: E402, F401

__all__ = ["celery_app", "process_document_task"]
