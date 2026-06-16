"""PlaybookExecutor - orchestrates playbook execution with confirmation, CAPTCHA, and error handling."""

import asyncio
import json
import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Optional

from playwright.async_api import BrowserContext, Page

from actions import ActionResult, execute_actions
from models import PlaybookStep
from screenshot import capture_screenshot
from token_resolver import resolve_tokens

logger = logging.getLogger(__name__)


# --- Error Classification ---

class ErrorCategory(str, Enum):
    """Classification of execution errors."""
    RETRYABLE = "retryable"           # Network timeout, selector not found (transient)
    CAPTCHA = "captcha"               # CAPTCHA challenge detected
    CONFIRMATION = "confirmation"     # Human confirmation step required
    AUTH_REQUIRED = "auth_required"   # Authentication wall
    SELECTOR_STALE = "selector_stale" # Playbook needs update
    FATAL = "fatal"                   # Unrecoverable error


RETRYABLE_KEYWORDS = ["timeout", "net::", "crashed", "closed", "detached"]
CAPTCHA_KEYWORDS = ["captcha", "verify you are human", "robot check", "recaptcha", "hcaptcha"]
CONFIRMATION_KEYWORDS = ["confirm", "verify", "approve", "consent", "agree"]
AUTH_KEYWORDS = ["login", "sign in", "authentication", "unauthorized"]
STALE_KEYWORDS = ["selector", "not found", "element", "visible"]


def classify_error(error_msg: str) -> ErrorCategory:
    """Classify an error message into a category."""
    msg = error_msg.lower()

    for keyword in CAPTCHA_KEYWORDS:
        if keyword in msg:
            return ErrorCategory.CAPTCHA

    for keyword in AUTH_KEYWORDS:
        if keyword in msg and "error" in msg:
            return ErrorCategory.AUTH_REQUIRED

    for keyword in RETRYABLE_KEYWORDS:
        if keyword in msg:
            return ErrorCategory.RETRYABLE

    for keyword in STALE_KEYWORDS:
        if keyword in msg:
            return ErrorCategory.SELECTOR_STALE

    return ErrorCategory.FATAL


# --- Confirmation Step ---

@dataclass
class ConfirmationRequest:
    """A step requiring human confirmation before continuing."""
    step_name: str
    description: str
    screenshot_url: Optional[str] = None
    timeout: int = 300  # seconds to wait for confirmation


# --- Execution State ---

@dataclass
class ExecutionState:
    """Tracks state during playbook execution."""
    job_id: str
    context: dict = field(default_factory=dict)
    results: list[dict] = field(default_factory=list)
    screenshots: list[str] = field(default_factory=list)
    errors: list[dict] = field(default_factory=list)
    confirmations: list[ConfirmationRequest] = field(default_factory=list)
    captcha_detected: bool = False
    stopped: bool = False


# --- PlaybookExecutor ---

class PlaybookExecutor:
    """Executes a broker playbook against a browser page.

    Args:
        max_retries: Maximum retry attempts for retryable errors per step.
        step_timeout: Timeout in seconds for each individual step.
        upload_fn: Optional async function (bytes, key) -> url for S3 uploads.
        confirm_fn: Optional async function (ConfirmationRequest) -> bool for human confirmation.
    """

    def __init__(
        self,
        max_retries: int = 2,
        step_timeout: int = 60,
        upload_fn: Optional[Callable] = None,
        confirm_fn: Optional[Callable] = None,
    ):
        self.max_retries = max_retries
        self.step_timeout = step_timeout
        self.upload_fn = upload_fn
        self.confirm_fn = confirm_fn

    async def execute(
        self,
        context: BrowserContext,
        steps: list[PlaybookStep],
        job_id: str,
        initial_context: Optional[dict] = None,
    ) -> ExecutionState:
        """Execute a sequence of playbook steps.

        Args:
            context: The browser context to use.
            steps: List of playbook steps to execute.
            job_id: The scan job ID for logging and S3 keys.
            initial_context: Initial token context (e.g., target name, address).

        Returns:
            ExecutionState with all results, errors, and metadata.
        """
        state = ExecutionState(job_id=job_id, context=initial_context or {})
        page = await context.new_page()

        try:
            for step_idx, step in enumerate(steps):
                if state.stopped:
                    break

                logger.info(
                    "Job %s: Executing step %d/%d - %s",
                    job_id, step_idx + 1, len(steps), step.name,
                )

                # Check for confirmation requirement
                if step.requires_confirmation:
                    confirmed = await self._request_confirmation(state, step, page)
                    if not confirmed:
                        logger.info("Job %s: Step %s not confirmed; skipping.", job_id, step.name)
                        continue

                # Execute step actions with retry
                step_result = await self._execute_step_with_retry(page, step, state)
                state.results.append(step_result)

                # Check for CAPTCHA in errors
                if step_result.get("error"):
                    category = classify_error(step_result["error"])
                    if category == ErrorCategory.CAPTCHA:
                        state.captcha_detected = True
                        logger.warning("Job %s: CAPTCHA detected at step %s", job_id, step.name)

                # Update context with extracted data
                if step_result.get("data"):
                    state.context.update(step_result["data"])

        finally:
            await page.close()

        return state

    async def _execute_step_with_retry(self, page: Page, step: PlaybookStep, state: ExecutionState) -> dict:
        """Execute a single step with retry logic."""
        last_error = None

        for attempt in range(self.max_retries + 1):
            try:
                if attempt > 0:
                    logger.info("Job %s: Retry %d for step %s", state.job_id, attempt, step.name)
                    wait_time = 2 ** attempt  # Exponential backoff
                    await asyncio.sleep(wait_time)

                results = await asyncio.wait_for(
                    execute_actions(page, step.actions, state.context),
                    timeout=self.step_timeout,
                )

                # Collect results
                step_data = {}
                step_errors = []
                all_success = True

                for r in results:
                    rd = r.to_dict()
                    if r.data:
                        step_data.update(r.data)
                    if not r.success:
                        all_success = False
                        step_errors.append(rd.get("error", "unknown"))

                # Take screenshot if step requests it
                if step.screenshot:
                    png_bytes = await capture_screenshot(page, name=f"{step.name}_result")
                    if self.upload_fn:
                        key = f"screenshots/{state.job_id}/{step.name}.png"
                        url = await self.upload_fn(png_bytes, key)
                        if url:
                            state.screenshots.append(url)

                return {
                    "step": step.name,
                    "success": all_success and len(step_errors) == 0,
                    "data": step_data,
                    "error": "; ".join(step_errors) if step_errors else None,
                    "attempts": attempt + 1,
                }

            except asyncio.TimeoutError:
                last_error = f"Step {step.name} timed out after {self.step_timeout}s"
                logger.warning("Job %s: %s", state.job_id, last_error)

            except Exception as e:
                error_msg = str(e)
                category = classify_error(error_msg)

                if category == ErrorCategory.CAPTCHA:
                    state.captcha_detected = True
                    last_error = f"CAPTCHA detected: {error_msg}"
                    break  # Don't retry CAPTCHA

                if category == ErrorCategory.SELECTOR_STALE:
                    last_error = error_msg
                    break  # Don't retry stale selectors

                last_error = error_msg
                logger.error("Job %s: Step %s failed (attempt %d): %s", state.job_id, step.name, attempt + 1, error_msg)

        return {
            "step": step.name,
            "success": False,
            "data": {},
            "error": last_error,
            "attempts": self.max_retries + 1,
        }

    async def _request_confirmation(self, state: ExecutionState, step: PlaybookStep, page: Page) -> bool:
        """Request human confirmation for a step."""
        if self.confirm_fn is None:
            logger.info("No confirm_fn provided; auto-approving step %s", step.name)
            return True

        # Take screenshot for the confirmation request
        png_bytes = await capture_screenshot(page, name=f"confirm_{step.name}")
        screenshot_url = None

        if self.upload_fn and png_bytes:
            key = f"screenshots/{state.job_id}/confirm_{step.name}.png"
            screenshot_url = await self.upload_fn(png_bytes, key)

        request = ConfirmationRequest(
            step_name=step.name,
            description=step.description or step.name,
            screenshot_url=screenshot_url,
            timeout=step.confirmation_timeout or 300,
        )

        try:
            confirmed = await asyncio.wait_for(
                self.confirm_fn(request),
                timeout=request.timeout,
            )
            return bool(confirmed)
        except asyncio.TimeoutError:
            logger.warning("Confirmation for step %s timed out; proceeding.", step.name)
            return True  # Auto-proceed on timeout to avoid hanging

    def get_summary(self, state: ExecutionState) -> dict:
        """Generate a summary of execution."""
        total_steps = len(state.results)
        successful = sum(1 for r in state.results if r.get("success"))
        failed = total_steps - successful

        return {
            "job_id": state.job_id,
            "total_steps": total_steps,
            "successful_steps": successful,
            "failed_steps": failed,
            "captcha_detected": state.captcha_detected,
            "total_screenshots": len(state.screenshots),
            "extracted_data": state.context,
            "errors": [r for r in state.results if not r.get("success")],
        }