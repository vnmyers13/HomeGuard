"""Playwright Executor Service - FastAPI application."""

import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse

from gw_playwright.executor import PlaybookExecutor
from gw_playwright.models import (
    HealthResponse,
    JobListResponse,
    JobResult,
    JobState,
    JobStatus,
    JobSubmissionResponse,
    OptoutJobRequest,
    Playbook,
    RetryResponse,
    ScanJobRequest,
)
from gw_playwright.pool import get_pool, shutdown_pool

logger = logging.getLogger(__name__)

# --- In-Memory Job Store ---
_job_store: dict[str, JobState] = {}


# --- Screenshot Upload (placeholder - returns local path) ---
async def _upload_screenshot(png_bytes: bytes, key: str) -> Optional[str]:
    """Upload screenshot to storage. Placeholder returns None (no S3 configured)."""
    # When S3 is configured, upload here:
    # s3_client.put_object(Bucket=BUCKET, Key=key, Body=png_bytes)
    # return f"https://{BUCKET}.s3.amazonaws.com/{key}"
    logger.debug("Screenshot upload skipped (no S3): %s", key)
    return None


# --- Confirmation Handler (placeholder - auto-approve) ---
async def _handle_confirmation(request):
    """Handle human confirmation requests. Placeholder auto-approves."""
    logger.info("Confirmation requested for step '%s' (auto-approved)", request.step_name)
    return True


# --- Executor Instance ---
executor = PlaybookExecutor(
    max_retries=2,
    step_timeout=60,
    upload_fn=_upload_screenshot,
    confirm_fn=_handle_confirmation,
)


# --- Job Execution ---
async def _run_job(job_state: JobState):
    """Execute a job asynchronously."""
    result = job_state.result
    pool = None

    try:
        # Acquire browser context from pool
        pool = await get_pool()
        context = await pool.acquire()

        result.status = JobStatus.RUNNING
        result.started_at = asyncio.get_event_loop().time()

        # Flatten playbook phases into steps for executor
        from gw_playwright.executor import PlaybookStep

        steps = []
        for phase in result.playbook.phases:
            for step_data in phase.steps:
                steps.append(
                    PlaybookStep(
                        name=f"{phase.name}/{step_data.action}",
                        description=phase.name,
                        actions=[step_data],
                        screenshot=step_data.screenshot,
                    )
                )

        # Execute playbook
        initial_context = result.tokens.copy()
        exec_state = await executor.execute(
            context=context,
            steps=steps,
            job_id=result.job_id,
            initial_context=initial_context,
        )

        # Build step results
        from gw_playwright.models import ActionType, StepResult

        for r in exec_state.results:
            step_result = StepResult(
                action=ActionType.NAVIGATE,  # placeholder
                status="ok" if r.get("success") else "error",
                message=r.get("error"),
            )
            result.step_results.append(step_result)

        # Set final status
        if exec_state.captcha_detected:
            result.status = JobStatus.REQUIRES_MANUAL
        elif any(not r.get("success") for r in exec_state.results):
            result.status = JobStatus.ERROR
        else:
            result.status = JobStatus.COMPLETED

    except asyncio.CancelledError:
        result.status = JobStatus.CANCELLED
        logger.info("Job %s cancelled.", result.job_id)

    except Exception as e:
        result.status = JobStatus.ERROR
        logger.error("Job %s failed: %s", result.job_id, e)

    finally:
        if context and pool:
            await pool.release(context)


# --- Lifespan ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage browser pool lifecycle."""
    try:
        await get_pool()
        logger.info("Playwright executor service started.")
    except Exception as e:
        logger.error("Failed to initialize browser pool: %s", e)

    yield

    # Cancel all running jobs
    for job_state in _job_store.values():
        if job_state.task and not job_state.task.done():
            job_state.task.cancel()

    await shutdown_pool()
    logger.info("Playwright executor service stopped.")


app = FastAPI(
    title="OpenDataRemoval Playwright Executor",
    description="Headless browser execution engine for broker playbooks",
    version="3.0.0",
    lifespan=lifespan,
)


# --- Health Endpoint ---
@app.get("/health")
async def health():
    """Health check with browser pool status."""
    try:
        pool = await get_pool()
        return HealthResponse(
            status="healthy",
            pool_size=pool.pool_size,
            pool_available=pool.available,
            pool_busy=pool.busy,
        )
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "error": str(e),
                "pool_size": 0,
                "pool_available": 0,
                "pool_busy": 0,
            },
        )


# --- Submit Scan Job ---
@app.post("/jobs/scan", status_code=201)
async def submit_scan_job(request: ScanJobRequest):
    """Submit a scan job for execution."""
    # Check pool availability
    try:
        pool = await get_pool()
        if pool.available == 0:
            return retry_response(retry_after_ms=10000)
    except Exception:
        raise HTTPException(status_code=503, detail="Browser pool unavailable")

    job_id = f"scan_{__import__('uuid').uuid4()}"
    result = JobResult(
        job_id=job_id,
        profile_id=request.profile_id,
        broker_id=request.broker_id,
        job_type="scan",
        status=JobStatus.QUEUED,
    )

    # Store playbook reference for execution
    result.playbook = request.playbook  # type: ignore[attr-defined]
    result.tokens = request.tokens  # type: ignore[attr-defined]

    job_state = JobState(job_id=job_id, result=result)
    _job_store[job_id] = job_state

    # Start async execution
    job_state.task = asyncio.create_task(_run_job(job_state))

    return JobSubmissionResponse(job_id=job_id, status=JobStatus.QUEUED)


# --- Submit Optout Job ---
@app.post("/jobs/optout", status_code=201)
async def submit_optout_job(request: OptoutJobRequest):
    """Submit an opt-out job for execution."""
    try:
        pool = await get_pool()
        if pool.available == 0:
            return retry_response(retry_after_ms=10000)
    except Exception:
        raise HTTPException(status_code=503, detail="Browser pool unavailable")

    job_id = f"optout_{__import__('uuid').uuid4()}"
    result = JobResult(
        job_id=job_id,
        profile_id=request.profile_id,
        broker_id=request.broker_id,
        job_type="optout",
        status=JobStatus.QUEUED,
    )

    result.playbook = request.playbook  # type: ignore[attr-defined]
    result.tokens = request.tokens  # type: ignore[attr-defined]

    job_state = JobState(job_id=job_id, result=result)
    _job_store[job_id] = job_state

    job_state.task = asyncio.create_task(_run_job(job_state))

    return JobSubmissionResponse(job_id=job_id, status=JobStatus.QUEUED)


# --- List Jobs ---
@app.get("/jobs")
async def list_jobs():
    """List all jobs."""
    jobs = []
    for job_state in _job_store.values():
        r = job_state.result
        jobs.append({
            "job_id": r.job_id,
            "job_type": r.job_type,
            "status": r.status.value,
            "profile_id": r.profile_id,
            "broker_id": r.broker_id,
        })

    return JobListResponse(jobs=jobs, total=len(jobs))


# --- Get Job Status ---
@app.get("/jobs/{job_id}")
async def get_job(job_id: str):
    """Get job status and results by ID."""
    job_state = _job_store.get(job_id)
    if not job_state:
        raise HTTPException(status_code=404, detail="Job not found")

    result = job_state.result

    # If still running, return status only
    if result.status in (JobStatus.QUEUED, JobStatus.RUNNING):
        return {
            "job_id": result.job_id,
            "job_type": result.job_type,
            "status": result.status.value,
            "profile_id": result.profile_id,
            "broker_id": result.broker_id,
            "step_results": [],
        }

    # Return full results
    return {
        "job_id": result.job_id,
        "job_type": result.job_type,
        "status": result.status.value,
        "profile_id": result.profile_id,
        "broker_id": result.broker_id,
        "step_results": [r.model_dump() for r in result.step_results],
        "error": result.error.model_dump() if result.error else None,
        "screenshots": [s.model_dump() for s in result.screenshots],
    }


# --- Cancel Job ---
@app.post("/jobs/{job_id}/cancel")
async def cancel_job(job_id: str):
    """Cancel a running or queued job."""
    job_state = _job_store.get(job_id)
    if not job_state:
        raise HTTPException(status_code=404, detail="Job not found")

    if job_state.task and not job_state.task.done():
        job_state.task.cancel()
        job_state.result.status = JobStatus.CANCELLED

    return {"job_id": job_id, "status": JobStatus.CANCELLED.value}


# --- 503 Retry Response Helper ---
def retry_response(retry_after_ms: int = 10000):
    """Return a 503 response with Retry-After header."""
    return JSONResponse(
        status_code=503,
        content=RetryResponse(retry_after_ms=retry_after_ms).model_dump(),
        headers={"Retry-After": str(retry_after_ms // 1000)},
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("gw_playwright.main:app", host="0.0.0.0", port=8002, reload=True)
