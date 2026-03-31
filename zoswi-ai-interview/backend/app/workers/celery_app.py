from celery import Celery

from app.core.config import get_settings

settings = get_settings()

celery_app = Celery(
    "zoswi_worker",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
)
celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    task_always_eager=settings.celery_task_always_eager,
    timezone="UTC",
    enable_utc=True,
)

