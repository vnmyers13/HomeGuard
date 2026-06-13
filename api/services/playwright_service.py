"""Playwright Executor HTTP client for the OpenDataRemoval API.

This service communicates with the Playwright executor service via HTTP
to submit scan/optout jobs and retrieve their results.
"""

import logging
import os
from typing import Any, Optional

import httpx

logger = logging.getLogger(__name__)

# Playwright service URL from environment
PLAYWRIGHT_SERVICE_URL = os.getenv("PLAYWRIGHT_SERVICE_URL", "http://playwright:8002")


class PlaywrightServiceError(Exception):
    """Base exception for Playwright service errors."""

    def __init__(self, message: str, status_code: Optional[int] = None, response_data: Optional[dict] = None):
        super().__init__(message)
        self.status_code = status_code
        self.response_data = response_data


class PlaywrightPoolExhaustedError(PlaywrightServiceError):
    """Raised when the Playwright browser pool is exhausted (503)."""

    pass


class PlaywrightJobNotFoundError(PlaywrightServiceError):
    """Raised when a job is not found (404)."""

    pass


class PlaywrightService:
    """HTTP client for the Playwright executor service."""

    def __init__(self, base_url: Optional[str] = None):
        self.base_url = (base_url or PLAYWRIGHT_SERVICE_URL).rstrip("/")
        self._client = None

    def _get_client(self) -> httpx.Client:
        """Get or create an HTTP client with proper timeouts."""
        if self._client is None:
            self._client = httpx.Client(
                base_url=self.base_url,
                timeout=httpx.Timeout(30.0, connect=10.0),
            )
        return self._client

    def close(self):
        """Close the underlying HTTP client."""
        if self._client is not None:
            self._client.close()
            self._client = None

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    # --- Health Check ---
    def health_check(self) -> dict[str, Any]:
        """Check Playwright service health and pool status."""
        client = self._get_client()
        response = client.get("/health")
        response.raise_for_status()
        return response.json()

    # --- Submit Scan Job ---
    def submit_scan_job(
        self,
        profile_id: str,
        broker_id: str,
        playbook: dict[str, Any],
        tokens: Optional[dict[str, Any]] = None,
        dry_run: bool = False,
    ) -> str:
        """Submit a scan job to the Playwright executor.

        Args:
            profile_id: The profile being scanned.
            broker_id: The broker to scan against.
            playbook: The playbook configuration dict.
            tokens: Optional token resolution context.
            dry_run: If True, simulate without executing.

        Returns:
            The job_id assigned by the Playwright service.

        Raises:
            PlaywrightPoolExhaustedError: If no browser sessions are available.
            PlaywrightServiceError: If the service returns an error.
        """
        payload = {
            "profile_id": profile_id,
            "broker_id": broker_id,
            "playbook": playbook,
            "tokens": tokens or {},
            "dry_run": dry_run,
        }

        client = self._get_client()
        try:
            response = client.post("/jobs/scan", json=payload)
            if response.status_code == 503:
                data = response.json()
                raise PlaywrightPoolExhaustedError(
                    "Playwright browser pool exhausted",
                    status_code=503,
                    response_data=data,
                )
            response.raise_for_status()
            result = response.json()
            return result["job_id"]
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 503:
                raise PlaywrightPoolExhaustedError(
                    "Playwright browser pool exhausted",
                    status_code=503,
                ) from e
            raise PlaywrightServiceError(
                f"Failed to submit scan job: {e.response.text}",
                status_code=e.response.status_code,
            ) from e

    # --- Submit Optout Job ---
    def submit_optout_job(
        self,
        profile_id: str,
        broker_id: str,
        playbook: dict[str, Any],
        tokens: Optional[dict[str, Any]] = None,
    ) -> str:
        """Submit an optout job to the Playwright executor.

        Args:
            profile_id: The profile requesting opt-out.
            broker_id: The broker to opt-out from.
            playbook: The optout playbook configuration dict.
            tokens: Optional token resolution context.

        Returns:
            The job_id assigned by the Playwright service.

        Raises:
            PlaywrightPoolExhaustedError: If no browser sessions are available.
            PlaywrightServiceError: If the service returns an error.
        """
        payload = {
            "profile_id": profile_id,
            "broker_id": broker_id,
            "playbook": playbook,
            "tokens": tokens or {},
        }

        client = self._get_client()
        try:
            response = client.post("/jobs/optout", json=payload)
            if response.status_code == 503:
                data = response.json()
                raise PlaywrightPoolExhaustedError(
                    "Playwright browser pool exhausted",
                    status_code=503,
                    response_data=data,
                )
            response.raise_for_status()
            result = response.json()
            return result["job_id"]
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 503:
                raise PlaywrightPoolExhaustedError(
                    "Playwright browser pool exhausted",
                    status_code=503,
                ) from e
            raise PlaywrightServiceError(
                f"Failed to submit optout job: {e.response.text}",
                status_code=e.response.status_code,
            ) from e

    # --- Get Job Status ---
    def get_job_status(self, job_id: str) -> dict[str, Any]:
        """Get the status and results of a job.

        Args:
            job_id: The job identifier returned from submit_scan_job or submit_optout_job.

        Returns:
            Dict with job status, step_results, error info, and screenshots.

        Raises:
            PlaywrightJobNotFoundError: If the job does not exist.
            PlaywrightServiceError: If the service returns an error.
        """
        client = self._get_client()
        try:
            response = client.get(f"/jobs/{job_id}")
            if response.status_code == 404:
                raise PlaywrightJobNotFoundError(f"Job {job_id} not found", status_code=404)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                raise PlaywrightJobNotFoundError(
                    f"Job {job_id} not found",
                    status_code=404,
                ) from e
            raise PlaywrightServiceError(
                f"Failed to get job status: {e.response.text}",
                status_code=e.response.status_code,
            ) from e

    # --- Cancel Job ---
    def cancel_job(self, job_id: str) -> dict[str, Any]:
        """Cancel a running or queued job.

        Args:
            job_id: The job identifier to cancel.

        Returns:
            Dict confirming cancellation.

        Raises:
            PlaywrightJobNotFoundError: If the job does not exist.
            PlaywrightServiceError: If the service returns an error.
        """
        client = self._get_client()
        try:
            response = client.post(f"/jobs/{job_id}/cancel")
            if response.status_code == 404:
                raise PlaywrightJobNotFoundError(f"Job {job_id} not found", status_code=404)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                raise PlaywrightJobNotFoundError(
                    f"Job {job_id} not found",
                    status_code=404,
                ) from e
            raise PlaywrightServiceError(
                f"Failed to cancel job: {e.response.text}",
                status_code=e.response.status_code,
            ) from e

    # --- Poll Job Until Complete ---
    def wait_for_job(
        self,
        job_id: str,
        poll_interval: float = 2.0,
        timeout: float = 600.0,
    ) -> dict[str, Any]:
        """Poll a job until it completes or times out.

        Args:
            job_id: The job identifier to poll.
            poll_interval: Seconds between status checks.
            timeout: Maximum time to wait in seconds.

        Returns:
            Final job result dict with status, step_results, etc.

        Raises:
            PlaywrightServiceError: If polling times out or service error occurs.
        """
        import time

        start = time.time()

        while True:
            elapsed = time.time() - start
            if elapsed > timeout:
                raise PlaywrightServiceError(
                    f"Job {job_id} polling timed out after {timeout}s",
                )

            result = self.get_job_status(job_id)
            status = result.get("status")

            # Terminal states
            if status in ("completed", "error", "requires_manual", "cancelled"):
                return result

            time.sleep(poll_interval)


# --- Module-level singleton for convenience ---
_default_service = PlaywrightService()


def get_playwright_service() -> PlaywrightService:
    """Get the default Playwright service instance."""
    return _default_service


# Convenience functions using default service
def submit_scan(
    profile_id: str,
    broker_id: str,
    playbook: dict[str, Any],
    tokens: Optional[dict[str, Any]] = None,
    dry_run: bool = False,
) -> str:
    """Submit a scan job via the default Playwright service."""
    return _default_service.submit_scan_job(profile_id, broker_id, playbook, tokens, dry_run)


def submit_optout(
    profile_id: str,
    broker_id: str,
    playbook: dict[str, Any],
    tokens: Optional[dict[str, Any]] = None,
) -> str:
    """Submit an optout job via the default Playwright service."""
    return _default_service.submit_optout_job(profile_id, broker_id, playbook, tokens)


def get_job(job_id: str) -> dict[str, Any]:
    """Get job status via the default Playwright service."""
    return _default_service.get_job_status(job_id)


def cancel_job(job_id: str) -> dict[str, Any]:
    """Cancel a job via the default Playwright service."""
    return _default_service.cancel_job(job_id)


def wait_for_job_completion(
    job_id: str,
    poll_interval: float = 2.0,
    timeout: float = 600.0,
) -> dict[str, Any]:
    """Wait for a job to complete via the default Playwright service."""
    return _default_service.wait_for_job(job_id, poll_interval, timeout)