from celery import Celery
from app.core.config import settings

celery_app = Celery(
    "complaint_worker",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)

# Schedule the escalation task to run every hour
celery_app.conf.beat_schedule = {
    "check-escalations-every-hour": {
        "task": "app.tasks.escalation.check_escalations",
        "schedule": 3600.0,  # Every hour
    },
}