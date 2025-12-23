from celery import Celery
from sqlalchemy.orm import Session

from api.utils.config import settings
from api.db.database import SessionLocal
from api.utils.logger import logger

# Create Celery app
celery_app = Celery(
    "workers",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["api.v1.workers.tasks"]
)

# Configure Celery
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    worker_concurrency=settings.WORKER_CONCURRENCY,
    worker_max_tasks_per_child=settings.WORKER_MAX_TASKS_PER_CHILD,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_track_started=True,
    task_time_limit=300,
    task_soft_time_limit=240,
)


# def get_db() -> Session:
#     db = SessionLocal()
#     try:
#         yield db
#     finally:
#         db.close()


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def process_image_task(self, upload_id: str):
    from api.v1.workers.tasks import process_image
    try:
        logger.info(f"Celery received task process_image_task for upload_id={upload_id}")
        result = process_image(upload_id)
        logger.info(f"Celery completed task process_image_task for upload_id={upload_id}")
        return result
    except Exception as exc:
        logger.exception(f"Exception in Celery task process_image_task for upload_id={upload_id}: {exc}")
        raise
