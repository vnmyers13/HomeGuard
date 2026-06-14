import os
import logging
from celery import Celery, Task
from celery.schedules import crontab

logger = logging.getLogger(__name__)

REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
REDIS_BACKEND = os.environ.get("REDIS_BACKEND_URL", "redis://localhost:6379/1")

celery_app = Celery(
    "opendataremoval",
    broker=REDIS_URL,
    backend=REDIS_BACKEND,
)


class AuditTask(Task):
    """Base task class that writes to audit.system_events on success/failure."""

    def on_success(self, retval, task_id, args, kwargs):
        logger.info("Task %s succeeded: %s", self.name, retval)
        try:
            _write_audit_event("task_success", {
                "task_id": task_id,
                "task_name": self.name,
                "retval_summary": str(retval)[:500] if retval else None,
            })
        except Exception as e:
            logger.debug("Failed to write audit event for task success: %s", e)

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        logger.error("Task %s failed: %s", self.name, exc)
        try:
            _write_audit_event("task_failure", {
                "task_id": task_id,
                "task_name": self.name,
                "error": str(exc)[:500],
                "traceback": str(einfo)[:1000],
            })
        except Exception as e:
            logger.debug("Failed to write audit event for task failure: %s", e)


def _write_audit_event(event_type: str, data: dict):
    """Write an event to audit.system_events via async DB session."""
    import asyncio
    try:
        from api.database import get_async_session
        from api.models.audit import SystemEvent
    except ImportError:
        from database import get_async_session
        from models.audit import SystemEvent

    async def _write():
        async with get_async_session() as session:
            event = SystemEvent(event_type=event_type, event_data=data)
            session.add(event)
            await session.commit()

    asyncio.run(_write())


celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="America/Detroit",
    enable_utc=True,
    task_track_started=True,
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    result_expires=3600,
    task_base=AuditTask,
    beat_schedule={
        "daily_full_scan": {
            "task": "workers.tasks.scanning.dispatch_daily_scan",
            "schedule": crontab(hour=2, minute=0),
        },
        "nightly_screenshot_purge": {
            "task": "workers.tasks.maintenance.purge_expired_screenshots",
            "schedule": crontab(hour=3, minute=0),
        },
        "weekly_broker_health_check": {
            "task": "workers.tasks.registry.check_broker_opt_out_urls",
            "schedule": crontab(hour=4, minute=0, day_of_week=0),
        },
        "hourly_followup_check": {
            "task": "workers.tasks.requests.hourly_followup_check",
            "schedule": crontab(minute=0),
        },
    },
)

# Auto-discover task modules
celery_app.conf.update(
    include=["api.workers.tasks"],
)

if __name__ == "__main__":
    celery_app.start()
