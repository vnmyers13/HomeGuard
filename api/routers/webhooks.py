"""Webhook router - receives callbacks from n8n workflows."""

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_session
from schemas.webhook import WebhookResponse
from services.webhook_service import WebhookService

router = APIRouter(prefix="/api/v1", tags=["webhooks"])


# ---------------------------------------------------------------------------
# Dependency injection helper
# ---------------------------------------------------------------------------

async def get_webhook_service(db: AsyncSession = Depends(get_session)) -> WebhookService:
    return WebhookService(db)


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/webhooks/scan-result", response_model=WebhookResponse)
async def handle_scan_result(
    payload: dict,
    svc: WebhookService = Depends(get_webhook_service),
):
    """Receive scan result from n8n workflow."""
    return await svc.process_scan_result(payload)


@router.post("/webhooks/captcha-update", response_model=WebhookResponse)
async def handle_captcha_update(
    payload: dict,
    svc: WebhookService = Depends(get_webhook_service),
):
    """Receive CAPTCHA challenge update from n8n workflow."""
    return await svc.process_captcha_update(payload)


@router.post("/webhooks/removal-result", response_model=WebhookResponse)
async def handle_removal_result(
    payload: dict,
    svc: WebhookService = Depends(get_webhook_service),
):
    """Receive removal request result from n8n workflow."""
    return await svc.process_removal_result(payload)