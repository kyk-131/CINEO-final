from celery import Celery
from .config import settings

celery_app = Celery(
    "cineo_ai",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
)

celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
)

celery_app.autodiscover_tasks(['backend.tasks'])

# Import tasks to ensure they're registered
from . import tasks
