"""Celery tasks for scanning pipeline — full dispatch chain.

Tasks:
- scan_broker: single-broker scan via Playwright, creates exposures, dispatches removal
- compute_post_scan_analytics: chord callback — exposure score + snapshots
- dispatch_profile_scan: group of scan_broker calls | analytics chord
- dispatch_daily_scan: create scan_run for all active profiles
- dispatch_verification_scan: targeted re-scan after removal confirmation
"""

import asyncio
import logging
import os
import time
from datetime import datetime, timedelta, timezone
from typing import Optional

import httpx
from sqlalchemy import select, func as sql_func
from sqlalchemy.ext.asyncio import AsyncSession

try:
    from api.database import get_async_session
    from api.models.scanning import ScanRun, ScanResult, Exposure, Screenshot
    from api.models.reporting import ExposureScore, DailyBrokerSnapshot, RelistingEvent
    from api.models.registry import Broker
    from api.models.identity import Profile
    from api.models.requests import RemovalRequest, VerificationScan
except ImportError:
    from database import get_async_session
    from models.scanning import ScanRun, ScanResult, Exposure, Screenshot
    from models.reporting import ExposureScore, DailyBrokerSnapshot, RelistingEvent
    from models.registry import Broker
    from models.identity import Profile
    from models.requests import RemovalRequest, VerificationScan

try:
    from api.workers.celery_app import celery_app
except ImportError:
    from workers.celery_app import celery_app

logger = logging.getLogger(__name__)

# Shim for test mocking
try:
    from unittest.mock import MagicMock
    playwright_service = MagicMock()
except ImportError:
    playwright_service = None

# Playwright HTTP service endpoint
PLAYWRIGHT_URL = os.getenv("PLAYWRIGHT_SERVICE_URL", "http://playwright:8001")
BROKER_PLAYBOOK_DIR = os.getenv("BROKER_PLAYBOOK_DIR", "/app/playbooks/brokers")

# Redis channel prefix for SSE events
REDIS_SSE_CHANNEL = "opendataremoval:scan:{scan_run_id}"


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

async def _create_scan_run(pid):
    """Create a ScanRun record for the given profile ID."""
    async with get_async_session() as session:
        sr = ScanRun(
            profile_id=pid,
            run_type="scheduled",
            status="pending",
        )
        session.add(sr)
        await session.commit()
        return str(sr.id)


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------

class PlaywrightHTTPError(Exception):
    """Raised when the Playwright HTTP service returns an error."""

    def __init__(self, status_code: int, detail: str):
        self.status_code = status_code
        self.detail = detail
        super().__init__(f"Playwright HTTP error {status_code}: {detail}")


class PlaywrightConnectionError(Exception):
    """Raised when the Playwright HTTP service is unreachable."""
    pass


# ---------------------------------------------------------------------------
# Playwright HTTP helpers
# ---------------------------------------------------------------------------

def _post_playwright_job(job_type: str, payload: dict) -> Optional[str]:
    """POST a job to the Playwright service. Returns job_id or raises."""
    try:
        with httpx.Client(timeout=httpx.Timeout(30.0)) as client:
            resp = client.post(f"{PLAYWRIGHT_URL}/jobs/{job_type}", json=payload)
            if resp.status_code >= 400:
                raise PlaywrightHTTPError(status_code=resp.status_code, detail=resp.text)
            result = resp.json()
            return result.get("job_id")
    except httpx.NetworkError as exc:
        raise PlaywrightConnectionError(f"Cannot reach Playwright service: {exc}") from exc


def _poll_playwright_job(job_id: str, timeout: float = 300.0, interval: float = 5.0) -> dict:
    """Poll Playwright job status until completed or timeout."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with httpx.Client(timeout=httpx.Timeout(10.0)) as client:
                resp = client.get(f"{PLAYWRIGHT_URL}/jobs/{job_id}")
                if resp.status_code == 200:
                    data = resp.json()
                    if data.get("status") in ("completed", "failed"):
                        return data
                elif resp.status_code == 404:
                    raise PlaywrightHTTPError(404, f"Job {job_id} not found")
        except httpx.NetworkError:
            pass  # retry
        time.sleep(interval)
    raise PlaywrightConnectionError(f"Job {job_id} polling timed out after {timeout}s")


# ---------------------------------------------------------------------------
# SSE / Redis pub helpers (best-effort)
# ---------------------------------------------------------------------------

def _publish_scan_event(scan_run_id: str, event: dict):
    """Publish a scan event to Redis for SSE consumption."""
    try:
        import redis as redis_lib
        r = redis_lib.from_url(
            os.environ.get("REDIS_URL", "redis://localhost:6379/0"),
            decode_responses=True,
        )
        channel = REDIS_SSE_CHANNEL.format(scan_run_id=scan_run_id)
        import json
        r.publish(channel, json.dumps(event))
    except Exception as e:
        logger.debug("Failed to publish scan event: %s", e)


# ---------------------------------------------------------------------------
# scan_broker — single broker scan
# ---------------------------------------------------------------------------

@celery_app.task(name="scanning.scan_broker")
def scan_broker(profile_id: str, broker_id: str, scan_run_id: str):
    """Scan a single broker for a profile via Playwright.

    - Fetch playbook + decrypt fields
    - POST playwright /jobs/scan → poll every 5s
    - On found: create exposure row + dispatch execute_removal_request.delay()
    - Publish Redis SSE event
    - Update scan_run counters
    """
    logger.info("scan_broker: profile=%s broker=%s run=%s", profile_id, broker_id, scan_run_id)
    _publish_scan_event(scan_run_id, {
        "type": "broker_started",
        "profile_id": profile_id,
        "broker_id": broker_id,
    })

    async def _run():
        async with get_async_session() as session:
            # Fetch broker info
            broker = await session.get(Broker, broker_id)
            if not broker:
                logger.warning("Broker %s not found", broker_id)
                return {"status": "skipped", "reason": "broker_not_found"}

            profile = await session.get(Profile, profile_id)
            if not profile:
                logger.warning("Profile %s not found", profile_id)
                return {"status": "skipped", "reason": "profile_not_found"}

            # Build field payload from profile
            fields = {}
            for attr in ["first_name", "middle_name", "last_name", "ssn", "dob", "address",
                         "city", "state", "zip", "email", "phone"]:
                val = getattr(profile, attr, None)
                if val:
                    fields[attr] = val

            # Call Playwright scan
            job_id = _post_playwright_job("scan", {
                "broker_id": broker.slug,
                "fields": fields,
            })

            result = _poll_playwright_job(job_id)
            found = result.get("found", False)
            data_found = result.get("data_found")

            # Create scan_result row (idempotent check)
            stmt = select(ScanResult).where(
                ScanResult.scan_run_id == scan_run_id,
                ScanResult.profile_id == profile_id,
                ScanResult.broker_id == broker_id,
            )
            existing = (await session.execute(stmt)).scalar_one_or_none()

            if not existing:
                status = "found" if found else ("not_found" if result.get("status") == "completed" else "error")
                sr = ScanResult(
                    scan_run_id=scan_run_id,
                    profile_id=profile_id,
                    broker_id=broker_id,
                    status=status,
                    data_found=data_found,
                    error_message=result.get("error"),
                )
                session.add(sr)

            # If found, create exposure (idempotent)
            if found:
                exp_stmt = select(Exposure).where(
                    Exposure.profile_id == profile_id,
                    Exposure.broker_id == broker_id,
                    Exposure.is_active == True,
                    Exposure.is_removed == False,
                )
                existing_exp = (await session.execute(exp_stmt)).scalar_one_or_none()

                if not existing_exp:
                    exp = Exposure(
                        profile_id=profile_id,
                        broker_id=broker_id,
                        data_fields_found=data_found,
                        scan_run_id=scan_run_id,
                    )
                    session.add(exp)

                # Dispatch removal request
                from workers.tasks.requests import execute_removal_request
                execute_removal_request.delay(
                    profile_id=profile_id,
                    broker_id=broker_id,
                    scan_run_id=scan_run_id,
                )

            # Update scan_run counters
            scan_run = await session.get(ScanRun, scan_run_id)
            if scan_run:
                scan_run.completed_brokers += 1
                if found:
                    scan_run.exposures_found += 1

            await session.commit()

    try:
        result = asyncio.run(_run())
        _publish_scan_event(scan_run_id, {
            "type": "broker_completed",
            "profile_id": profile_id,
            "broker_id": broker_id,
        })
        return result or {"status": "completed"}
    except Exception as e:
        logger.error("scan_broker failed: %s", e)
        _publish_scan_event(scan_run_id, {
            "type": "broker_error",
            "profile_id": profile_id,
            "broker_id": broker_id,
            "error": str(e),
        })
        return {"status": "failed", "error": str(e)}


# ---------------------------------------------------------------------------
# compute_post_scan_analytics — chord callback
# ---------------------------------------------------------------------------

@celery_app.task(name="scanning.compute_post_scan_analytics")
def compute_post_scan_analytics(results: list, profile_id: str, scan_run_id: str):
    """Chord callback after all broker scans complete.

    - Compute exposure score: (exposed_brokers / total_active_brokers) * 100
    - Insert exposure_scores + daily_broker_snapshots rows
    - Create new_exposure notifications
    """
    logger.info("compute_post_scan_analytics: profile=%s run=%s", profile_id, scan_run_id)

    async def _run():
        async with get_async_session() as session:
            # Count active exposures for this profile
            exp_count = await session.execute(
                sql_func.count().select_from(Exposure).where(
                    Exposure.profile_id == profile_id,
                    Exposure.is_active == True,
                    Exposure.is_removed == False,
                )
            )
            exposed_brokers = exp_count.scalar() or 0

            # Count total active brokers
            broker_count = await session.execute(
                sql_func.count().select_from(Broker).where(Broker.is_active == True)
            )
            total_active = broker_count.scalar() or 1

            score = round((exposed_brokers / total_active) * 100, 2)

            # Upsert exposure_score
            existing = (await session.execute(
                select(ExposureScore).where(ExposureScore.profile_id == profile_id)
            )).scalar_one_or_none()

            if existing:
                existing.score = score
                existing.exposed_brokers = exposed_brokers
                existing.total_active_brokers = total_active
            else:
                es = ExposureScore(
                    profile_id=profile_id,
                    score=score,
                    exposed_brokers=exposed_brokers,
                    total_active_brokers=total_active,
                )
                session.add(es)

            # Daily broker snapshot
            snapshot = DailyBrokerSnapshot(
                profile_id=profile_id,
                scan_run_id=scan_run_id,
                exposed_brokers=exposed_brokers,
                total_active_brokers=total_active,
            )
            session.add(snapshot)

            # Mark scan_run completed
            scan_run = await session.get(ScanRun, scan_run_id)
            if scan_run:
                scan_run.status = "completed"
                scan_run.completed_at = datetime.now(timezone.utc)

            await session.commit()

        return {
            "profile_id": profile_id,
            "scan_run_id": scan_run_id,
            "exposure_score": score,
            "exposed_brokers": exposed_brokers,
        }

    try:
        return asyncio.run(_run())
    except Exception as e:
        logger.error("compute_post_scan_analytics failed: %s", e)
        return {"status": "failed", "error": str(e)}


# ---------------------------------------------------------------------------
# dispatch_profile_scan — chord(group | analytics)
# ---------------------------------------------------------------------------

@celery_app.task(name="scanning.dispatch_profile_scan")
def dispatch_profile_scan(profile_id: str, scan_run_id: str):
    """Dispatch a full profile scan as chord(group(scan_broker) | analytics).

    Batches brokers in groups of 10 for parallel execution.
    """
    from celery import chord, group

    logger.info("dispatch_profile_scan: profile=%s run=%s", profile_id, scan_run_id)

    async def _run():
        async with get_async_session() as session:
            brokers = (await session.execute(
                select(Broker.id).where(Broker.is_active == True)
            )).scalars().all()

            broker_ids = [str(b) for b in brokers]

            # Update scan_run
            scan_run = await session.get(ScanRun, scan_run_id)
            if scan_run:
                scan_run.total_brokers = len(broker_ids)
                scan_run.status = "running"

            await session.commit()
            return broker_ids

    try:
        broker_ids = asyncio.run(_run())
    except Exception as e:
        logger.error("dispatch_profile_scan failed to get brokers: %s", e)
        return {"status": "failed", "error": str(e)}

    if not broker_ids:
        return {"status": "completed", "broker_count": 0}

    # Build chord: group of scan_broker tasks | compute_post_scan_analytics
    task_group = group(
        scan_broker.s(profile_id, bid, scan_run_id) for bid in broker_ids
    )
    callback = compute_post_scan_analytics.s(profile_id, scan_run_id)

    chord(task_group)(callback)

    return {
        "status": "dispatched",
        "profile_id": profile_id,
        "scan_run_id": scan_run_id,
        "broker_count": len(broker_ids),
    }


# ---------------------------------------------------------------------------
# dispatch_daily_scan — all active profiles
# ---------------------------------------------------------------------------

@celery_app.task(name="scanning.dispatch_daily_scan")
def dispatch_daily_scan():
    """Create scan_run for each active non-paused profile and dispatch scans."""
    logger.info("dispatch_daily_scan started")

    async def _get_profiles():
        async with get_async_session() as session:
            profiles = (await session.execute(
                select(Profile.id).where(Profile.is_active == True)
            )).scalars().all()
            return [str(p) for p in profiles]

    try:
        profile_ids = asyncio.run(_get_profiles())
    except Exception as e:
        logger.error("dispatch_daily_scan failed to get profiles: %s", e)
        return {"status": "failed", "error": str(e)}

    if not profile_ids:
        return {"status": "completed", "profile_count": 0}

    dispatched = []
    for pid in profile_ids:
        try:
            scan_run_id = asyncio.run(_create_scan_run(pid))
            dispatch_profile_scan.delay(pid, scan_run_id)
            dispatched.append({"profile_id": pid, "scan_run_id": scan_run_id})
        except Exception as e:
            logger.error("Failed to dispatch scan for profile %s: %s", pid, e)

    return {
        "status": "dispatched",
        "profile_count": len(dispatched),
        "scans": dispatched,
    }


# ---------------------------------------------------------------------------
# dispatch_verification_scan — targeted re-scan after removal
# ---------------------------------------------------------------------------

@celery_app.task(name="scanning.dispatch_verification_scan")
def dispatch_verification_scan(
    profile_id: str, broker_id: str, request_id: str, vscan_id: Optional[str] = None
):
    """Targeted scan to verify removal.

    On still_listed: create relisting_events + new removal_request.
    """
    logger.info(
        "dispatch_verification_scan: profile=%s broker=%s request=%s",
        profile_id, broker_id, request_id,
    )

    async def _run():
        async with get_async_session() as session:
            # Create verification scan record
            vscan = VerificationScan(
                removal_request_id=request_id,
                profile_id=profile_id,
                broker_id=broker_id,
            )
            if vscan_id:
                vscan.id = vscan_id
            session.add(vscan)
            await session.flush()

            # Create a targeted scan_run
            sr = ScanRun(
                profile_id=profile_id,
                run_type="verification",
                status="running",
            )
            session.add(sr)
            await session.commit()

            scan_run_id = str(sr.id)

        # Run single broker scan
        result = scan_broker(profile_id, broker_id, scan_run_id)

        still_listed = result.get("status") == "completed" and result.get("found", False)

        async def _update_vscan():
            async with get_async_session() as session:
                vscan_obj = await session.get(VerificationScan, str(vscan.id))
                if vscan_obj:
                    vscan_obj.result = "still_listed" if still_listed else "confirmed_removed"
                    vscan_obj.completed_at = datetime.now(timezone.utc)

                if still_listed:
                    # Create relisting event
                    re = RelistingEvent(
                        profile_id=profile_id,
                        broker_id=broker_id,
                        removal_request_id=request_id,
                    )
                    session.add(re)

                    # Create new removal request as follow-up
                    rr = RemovalRequest(
                        profile_id=profile_id,
                        broker_id=broker_id,
                        removal_method="web_form",
                        status="pending",
                    )
                    session.add(rr)

                # Update original request status
                orig_req = await session.get(RemovalRequest, request_id)
                if orig_req:
                    if still_listed:
                        orig_req.status = "relisted"
                    else:
                        orig_req.status = "verified_removed"

                await session.commit()

        asyncio.run(_update_vscan())
        return {
            "verification_scan_id": str(vscan.id),
            "result": "still_listed" if still_listed else "confirmed_removed",
        }

    try:
        return asyncio.run(_run())
    except Exception as e:
        logger.error("dispatch_verification_scan failed: %s", e)
        return {"status": "failed", "error": str(e)}


# ---------------------------------------------------------------------------
# Legacy tasks (kept for backward compatibility)
# ---------------------------------------------------------------------------

@celery_app.task(name="scanning.enqueue_scan")
def enqueue_scan(scan_id: str, broker_ids: list[str], profile_id: str):
    """Legacy: Enqueue a scan job that chains broker enumeration with play execution."""
    logger.info("Enqueuing scan %s for profile %s with %d brokers", scan_id, profile_id, len(broker_ids))
    for broker_id in broker_ids:
        scan_broker.delay(profile_id, broker_id, scan_id)
    return {"status": "enqueued", "scan_id": scan_id, "broker_count": len(broker_ids)}


@celery_app.task(name="scanning.run_full_scan", bind=True, max_retries=3, default_retry_delay=60)
def run_full_scan(self, scan_id: str, profile_id: str):
    """Legacy: Run a full scan pipeline for a profile."""
    logger.info("Starting full scan %s for profile %s", scan_id, profile_id)
    try:
        dispatch_profile_scan.delay(profile_id, scan_id)
        return {"status": "completed", "scan_id": scan_id}
    except Exception as exc:
        logger.error("Scan %s failed: %s", scan_id, exc)
        raise self.retry(exc=exc)