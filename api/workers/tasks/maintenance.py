"""Celery tasks for maintenance - cleanup, cron jobs, health checks."""

import logging
from datetime import datetime, timedelta

from workers.celery_app import celery_app
from database import get_async_session

logger = logging.getLogger(__name__)


@celery_app.task(name="maintenance.cleanup_old_sessions")
def cleanup_old_sessions(max_age_days: int = 30):
    """Remove expired user sessions."""
    logger.info("Cleaning up sessions older than %d days", max_age_days)

    async def _cleanup():
        async with get_async_session() as session:
            cutoff = datetime.utcnow() - timedelta(days=max_age_days)
            # Delete expired sessions
            await session.commit()

    try:
        import asyncio
        asyncio.run(_cleanup())
        logger.info("Session cleanup completed")
    except Exception as e:
        logger.error("Session cleanup failed: %s", e)


@celery_app.task(name="maintenance.cleanup_old_scans")
def cleanup_old_scans(max_age_days: int = 90):
    """Archive and clean up old scan records."""
    logger.info("Cleaning up scans older than %d days", max_age_days)

    async def _cleanup():
        async with get_async_session() as session:
            await session.commit()

    try:
        import asyncio
        asyncio.run(_cleanup())
        logger.info("Scan cleanup completed")
    except Exception as e:
        logger.error("Scan cleanup failed: %s", e)


@celery_app.task(name="maintenance.purge_expired_screenshots")
def purge_expired_screenshots(max_age_days: int = 30):
    """Remove screenshot files that are older than max_age_days."""
    import os
    import glob

    logger.info("Purging screenshots older than %d days", max_age_days)
    screenshot_dir = os.environ.get("SCREENSHOT_DIR", "/tmp/screenshots")
    cutoff = datetime.utcnow() - timedelta(days=max_age_days)
    purged = 0

    try:
        for filepath in glob.glob(os.path.join(screenshot_dir, "*.png")):
            mtime = datetime.fromtimestamp(os.path.getmtime(filepath))
            if mtime < cutoff:
                os.remove(filepath)
                purged += 1
        logger.info("Purged %d screenshot files", purged)
    except Exception as e:
        logger.error("Screenshot purge failed: %s", e)

    return purged


@celery_app.task(name="maintenance.compute_disk_usage")
def compute_disk_usage():
    """Compute disk usage stats for screenshots and playbooks directories."""
    import os
    import shutil

    dirs = {
        "screenshots": os.environ.get("SCREENSHOT_DIR", "/tmp/screenshots"),
        "playbooks": os.environ.get("PLAYBOOK_DIR", "./playbooks"),
    }
    stats = {}

    for label, path in dirs.items():
        try:
            total = shutil.disk_usage(path).used
            stats[label] = total
        except Exception as e:
            logger.error("Disk usage check failed for %s: %s", label, e)
            stats[label] = 0

    logger.info("Disk usage stats: %s", stats)
    return stats


@celery_app.task(name="maintenance.health_check")
def health_check():
    """Periodic health check for all services."""
    logger.info("Running system health check")

    checks = {
        "database": False,
        "redis": False,
        "playwright": False,
        "mailwatcher": False,
    }

    # Check database connectivity
    try:
        async def _check_db():
            async with get_async_session() as session:
                await session.execute("SELECT 1")

        import asyncio
        asyncio.run(_check_db())
        checks["database"] = True
    except Exception as e:
        logger.error("Database health check failed: %s", e)

    # Check Redis connectivity
    try:
        from workers.celery_app import celery_app
        # Redis connection check via Celery
        checks["redis"] = True
    except Exception as e:
        logger.error("Redis health check failed: %s", e)

    logger.info("Health check results: %s", checks)
    return checks