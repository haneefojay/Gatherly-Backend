"""Celery application configuration"""
from celery import Celery
from app.core.settings import get_settings

settings = get_settings()

celery_app = Celery(
    "gatherly",
    broker=settings.REDIS_BROKER_URL,
    backend=settings.REDIS_BROKER_URL,
    include=[
        "app.worker.suspension_tasks",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    beat_schedule={
        "lift-expired-suspensions-every-5-minutes": {
            "task": "app.worker.suspension_tasks.lift_expired_suspensions",
            "schedule": 300.0,  # every 5 minutes
        },
    },
)
