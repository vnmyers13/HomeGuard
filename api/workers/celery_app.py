import os
from celery import Celery
from celery.schedules import crontab

REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")

celery_app = Celery(
    "homeguard",
    broker=REDIS_URL,
    backend=REDIS_URL,
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="America/Detroit",
    enable_utc=True,
    task_track_started=True,
    worker_prefetch_multiplier=1,
    task_acks_late=True,
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
            "task": "workers.tasks.requests.followup_removal_request",
            "schedule": crontab(minute=0),
        },
    },
)

if __name__ == "__main__":
    celery_app.start()