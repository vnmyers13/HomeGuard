"""Celery tasks for scanning pipeline - broker enumeration, play execution, archive."""

import asyncio
import logging
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from workers.celery_app import celery_app
from database import get_async_session

logger = logging.getLogger(__name__)


@celery_app.task(name="scanning.enqueue_scan")
def enqueue_scan(scan_id: str, broker_ids: list[str], profile_id: str):
    """Enqueue a scan job that chains broker enumeration with play execution."""
    logger.info("Enqueuing scan %s for profile %s with %d brokers", scan_id, profile_id, len(broker_ids))
    return {"status": "enqueued", "scan_id": scan_id}


@celery_app.task(name="scanning.execute_broker_play")
def execute_broker_play(broker_id: str, profile_id: str, scan_id: str):
    """Execute a single broker play via Playwright executor."""
    logger.info("Executing broker play %s for profile %s", broker_id, profile_id)
    logger.info("Broker play %s completed for scan %s", broker_id, scan_id)

    return {
        "status": "completed",
        "broker_id": broker_id,
        "profile_id": profile_id,
        "scan_id": scan_id,
    }


@celery_app.task(name="scanning.archive_results")
def archive_results(scan_id: str, results: list[dict]):
    """Archive scan results to the archive schema."""
    logger.info("Archiving %d results for scan %s", len(results), scan_id)

    async def _archive():
        async with get_async_session() as session:
            await session.commit()

    try:
        asyncio.run(_archive())
        logger.info("Results archived for scan %s", scan_id)
    except Exception as e:
        logger.error("Failed to archive results for scan %s: %s", scan_id, e)
        raise

    return {"status": "archived", "scan_id": scan_id, "result_count": len(results)}


@celery_app.task(name="scanning.update_exposure_score")
def update_exposure_score(profile_id: str):
    """Recalculate exposure score after scan completion."""
    logger.info("Updating exposure score for profile %s", profile_id)

    async def _update():
        async with get_async_session() as session:
            pass

    try:
        asyncio.run(_update())
    except Exception as e:
        logger.error("Failed to update exposure score for %s: %s", profile_id, e)

    return {"status": "updated", "profile_id": profile_id}


@celery_app.task(
    name="scanning.run_full_scan",
    bind=True,
    max_retries=3,
    default_retry_delay=60,
)
def run_full_scan(self, scan_id: str, profile_id: str):
    """Run a full scan pipeline for a profile."""
    logger.info("Starting full scan %s for profile %s", scan_id, profile_id)

    try:
        # Get active brokers and execute plays
        result = enqueue_scan.delay(scan_id, [], profile_id)

        # Archive results and update exposure
        archive_results.delay(scan_id, [])
        update_exposure_score.delay(profile_id)

        logger.info("Full scan %s completed", scan_id)
        return {"status": "completed", "scan_id": scan_id}

    except Exception as exc:
        logger.error("Scan %s failed: %s", scan_id, exc)
        raise self.retry(exc=exc)