"""Playbook executor for OpenDataRemoval.

Orchestrates the execution of a playbook against a target page,
handling retries, confirmation requests, screenshots, and context
passing between steps.
"""

import asyncio
import logging
from dataclasses import dataclass, field
from typing import Any, Callable, List, Optional

from playwright.async_api import Page as AsyncPage

from .actions import ActionResult, execute_actions
from .models import PlaybookStep
from .screenshot import capture_screenshot

logger = logging.getLogger(__name__)


# ─── Error classification ───────────────────────────────────────

CAPTCHA_KEYWORDS = ("captcha", "recaptcha", "hcaptcha", "verify you are human")
STALE_KEYWORDS = ("selector not found", "staleelement", "no such element", "timeout")
NETWORK_KEYWORDS = ("net::err_", "networkchanged", "connection refused", "dns_resolve")
TIMEOUT_ERRORS = (asyncio.TimeoutError,)


def classify_error(error_msg: str) -> str:
    """Classify an error message into a known category.

    Returns one of: captcha | stale | network | timeout | unknown
    """
    lower = error_msg.lower()
    for kw in CAPTCHA_KEYWORDS:
        if kw in lower:
            return "captcha"
    for kw in STALE_KEYWORDS:
        if kw in lower:
            return "stale"
    for kw in NETWORK_KEYWORDS:
        if kw in lower:
            return "network"
    return "unknown"


def is_retryable(error_msg: str) -> bool:
    """Return True when the error *is* retryable.

    Only network errors and generic unknown errors are retried.
    CAPTCHA and stale-selector errors are NOT retried.
    """
    return classify_error(error_msg) in ("network", "unknown")


# ─── Data classes ───────────────────────────────────────────────

@dataclass
class ConfirmationRequest:
    step_name: str
    description: Optional[str] = None
    screenshot_url: Optional[str] = None
    timeout: int = 300


@dataclass
class ExecutionState:
    job_id: str
    context: dict = field(default_factory=dict)
    results: list = field(default_factory=list)
    screenshots: list = field(default_factory=list)
    errors: list = field(default_factory=list)
    captcha_detected: bool = False
    stopped: bool = False


# ─── Executor ───────────────────────────────────────────────────

class PlaybookExecutor:
    """Execute a list of playbook steps on a single page.

    Parameters
    ----------
    max_retries : int
        Maximum retry attempts per step (default 2).
    confirm_fn : callable
        Optional async function ``async fn(req: ConfirmationRequest) -> bool``
        that is invoked when a step requires confirmation.  When *None* the
        executor auto-approves every request.
    upload_fn : callable
        Optional async function ``async fn(data: bytes, key: str) -> str`` that
        uploads a screenshot and returns the public URL.
    """

    def __init__(
        self,
        max_retries: int = 2,
        confirm_fn: Optional[Callable] = None,
        upload_fn: Optional[Callable] = None,
    ):
        self.max_retries = max_retries
        self.confirm_fn = confirm_fn
        self.upload_fn = upload_fn

    # ── public entry point ──────────────────────────────────────

    async def execute(
        self,
        page: AsyncPage,
        steps: List[PlaybookStep],
        job_id: str,
        initial_ctx: Optional[dict] = None,
    ) -> ExecutionState:
        """Run *steps* sequentially on *page* and return the final state."""
        state = ExecutionState(job_id=job_id, context=dict(initial_ctx or {}))

        try:
            for idx, step in enumerate(steps):
                if state.stopped:
                    logger.info("Execution stopped by external signal, aborting at step %d", idx)
                    break

                result = await self._execute_step_with_retry(page, step, state)
                state.results.append(result)

                # Merge data back into context for subsequent steps
                if result.get("data"):
                    state.context.update(result["data"])

                # Record error
                if result.get("error"):
                    state.errors.append(result["error"])

                # CAPTCHA detection from errors
                if result.get("error") and classify_error(result["error"]) == "captcha":
                    state.captcha_detected = True

                # Screenshot (after action results are collected)
                if step.screenshot:
                    await self._capture_step_screenshot(page, step, state)

        finally:
            # Ensure page is cleaned up
            try:
                await page.close()
            except Exception:
                pass

        return state

    # ── step-level execution ────────────────────────────────────

    async def _execute_step_with_retry(
        self,
        page: AsyncPage,
        step: PlaybookStep,
        state: ExecutionState,
    ) -> dict:
        attempts = 0
        last_error = None

        while attempts <= self.max_retries:
            try:
                if state.stopped:
                    break

                # Confirmation gate
                if step.requires_confirmation:
                    approved = await self._request_confirmation(state, step, page)
                    if not approved:
                        return {
                            "step": step.name,
                            "success": False,
                            "error": "Confirmation denied",
                            "data": {},
                            "attempts": attempts or 1,
                        }

                results = await execute_actions(page, step.actions, state.context)
                data = {}
                error = None
                for r in results:
                    if r.data:
                        data.update(r.data)
                    if r.error:
                        error = r.error

                return {
                    "step": step.name,
                    "success": all(r.success for r in results),
                    "data": data,
                    "error": error,
                    "attempts": attempts or 1,
                }

            except Exception as exc:
                last_error = str(exc)
                err_class = classify_error(last_error)

                # CAPTCHA / stale → stop immediately
                if err_class in ("captcha", "stale"):
                    state.captcha_detected = (err_class == "captcha")
                    break

                attempts += 1
                if attempts > self.max_retries:
                    break

                wait = 0.5 * (2 ** (attempts - 1))
                logger.warning(
                    "Step %s attempt %d failed (%s), retrying in %.1fs …",
                    step.name, attempts, last_error, wait,
                )
                await asyncio.sleep(wait)

        # Exhausted retries or non-retryable error
        return {
            "step": step.name,
            "success": False,
            "data": {},
            "error": last_error,
            "attempts": attempts or 1,
        }

    # ── confirmation ────────────────────────────────────────────

    async def _request_confirmation(
        self,
        state: ExecutionState,
        step: PlaybookStep,
        page: AsyncPage,
    ) -> bool:
        if self.confirm_fn is None:
            return True  # auto-approve

        ss_url = None
        if self.upload_fn:
            raw = await capture_screenshot(page)
            key = f"confirmations/{state.job_id}/{step.name}.png"
            ss_url = await self.upload_fn(raw, key)

        req = ConfirmationRequest(
            step_name=step.name,
            description=step.description,
            screenshot_url=ss_url,
            timeout=getattr(step, "confirmation_timeout", 300),
        )

        try:
            return await self.confirm_fn(req)
        except asyncio.TimeoutError:
            logger.info("Confirmation timed out for step %s, auto-proceeding", step.name)
            return True  # auto-proceed on timeout

    # ── screenshot ──────────────────────────────────────────────

    async def _capture_step_screenshot(
        self,
        page: AsyncPage,
        step: PlaybookStep,
        state: ExecutionState,
    ):
        if not self.upload_fn:
            return
        raw = await capture_screenshot(page)
        key = f"screenshots/{state.job_id}/{step.name}.png"
        url = await self.upload_fn(raw, key)
        state.screenshots.append(url)

    # ── summary helper ──────────────────────────────────────────

    @staticmethod
    def get_summary(state: ExecutionState) -> dict:
        successful = sum(1 for r in state.results if r.get("success"))
        failed = len(state.results) - successful
        return {
            "job_id": state.job_id,
            "total_steps": len(state.results),
            "successful_steps": successful,
            "failed_steps": failed,
            "total_screenshots": len(state.screenshots),
            "captcha_detected": state.captcha_detected,
            "errors": list(state.errors),
        }