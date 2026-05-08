"""Webhook service - processes n8n callbacks."""

import logging
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text, select, update
from models.scanning import ScanRun, ScanResult, Exposure
from models.requests import RemovalRequest

logger = logging.getLogger(__name__)


class WebhookService:
    """Process webhook payloads from n8n workflows."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def process_scan_result(self, payload: dict) -> dict:
        """Process a scan result webhook from n8n.

        Updates the individual ScanResult and then reconciles the parent
        ScanRun progress (completed_brokers, exposures_found).
        """
        scan_result = (
            await self.db.execute(
                select(ScanResult).where(ScanResult.id == payload["scan_id"])
            )
        ).scalar_one_or_none()

        if not scan_result:
            logger.warning(f"ScanResult not found for webhook: {payload['scan_id']}")
            return {"error": "scan_not_found"}

        # --- Update the individual result ------------------------------
        scan_result.status = "found" if payload.get("found_listing") else "not_found"
        scan_result.data_found = payload.get("data_found")
        scan_result.error_message = payload.get("error_message")
        scan_result.screenshot_path = payload.get("screenshot_path")
        scan_result.completed_at = datetime.now(timezone.utc)

        # --- Create Exposure if listing found --------------------------
        if payload.get("found_listing"):
            exposure = Exposure(
                profile_id=scan_result.profile_id,
                broker_id=scan_result.broker_id,
                data_fields_found=payload.get("data_found"),
                scan_run_id=scan_result.scan_run_id,
            )
            await self.db.add(exposure)

        # --- Reconcile parent ScanRun ----------------------------------
        scan_run = (
            await self.db.execute(
                select(ScanRun).where(ScanRun.id == scan_result.scan_run_id)
            )
        ).scalar_one_or_none()

        if scan_run:
            scan_run.completed_brokers += 1
            if payload.get("found_listing"):
                scan_run.exposures_found += 1

            # Check if all brokers accounted for
            if scan_run.completed_brokers >= scan_run.total_brokers:
                scan_run.status = "completed"
                scan_run.completed_at = datetime.now(timezone.utc)

        await self.db.commit()

        logger.info(
            f"Processed scan result: scan_result={scan_result.id}, "
            f"found={scan_result.status == 'found'}"
        )
        return {"processed": True, "scan_id": scan_result.id}

    # ------------------------------------------------------------------
    async def process_captcha_update(self, payload: dict) -> dict:
        """Process a CAPTCHA challenge update from n8n.

        Records the CAPTCHA event on the ScanResult so the operator can
        intervene via the dashboard if needed.
        """
        scan_result = (
            await self.db.execute(
                select(ScanResult).where(ScanResult.id == payload["scan_id"])
            )
        ).scalar_one_or_none()

        if not scan_result:
            logger.warning(f"ScanResult not found for CAPTCHA update: {payload['scan_id']}")
            return {"error": "scan_not_found"}

        # Store CAPTCHA metadata in data_found (extend as needed)
        meta = scan_result.data_found or {}
        meta["captcha_required"] = True
        meta["captcha_url"] = payload.get("captcha_url")
        scan_result.data_found = meta
        scan_result.updated_at = datetime.now(timezone.utc)

        await self.db.commit()

        logger.info(f"CAPTCHA update recorded for scan_result={scan_result.id}")
        return {"processed": True, "scan_id": scan_result.id}

    # ------------------------------------------------------------------
    async def process_removal_result(self, payload: dict) -> dict:
        """Process a removal request result from n8n."""
        request = (
            await self.db.execute(
                select(RemovalRequest).where(RemovalRequest.id == payload["request_id"])
            )
        ).scalar_one_or_none()

        if not request:
            logger.warning(
                f"RemovalRequest not found for webhook: {payload['request_id']}"
            )
            return {"error": "removal_request_not_found"}

        request.status = payload.get("status", "unknown")
        request.broker_response = payload.get("message")
        request.updated_at = datetime.now(timezone.utc)

        if payload.get("success"):
            request.confirmed_at = datetime.now(timezone.utc)
            request.status = "confirmed"

            # Mark related exposures as removed
            await self.db.execute(
                update(Exposure)
                .where(
                    Exposure.removal_request_id == str(request.id),
                    Exposure.is_active.is_(True),
                )
                .values(is_removed=True, is_active=False, removed_at=datetime.now(timezone.utc))
            )

        await self.db.commit()

        logger.info(
            f"Processed removal result: request={request.id}, status={request.status}"
        )
        return {"processed": True, "request_id": request.id}