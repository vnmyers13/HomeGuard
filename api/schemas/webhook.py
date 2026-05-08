"""Webhook schemas - n8n callback payloads and responses."""

from enum import Enum
from pydantic import BaseModel, Field
from typing import Optional


class WebhookEvent(str, Enum):
    """Supported webhook event types."""
    PROFILE_CREATED = "profile.created"
    PROFILE_UPDATED = "profile.updated"
    REQUEST_COMPLETED = "request.completed"
    SCAN_COMPLETED = "scan.completed"


class WebhookCreate(BaseModel):
    """Request body for creating a webhook subscription."""
    event_type: str = Field(..., min_length=1)
    target_url: str = Field(..., min_length=1)
    secret: Optional[str] = None


class WebhookResponse(BaseModel):
    """Webhook subscription response."""
    id: int
    event_type: str
    target_url: str
    status: str = "active"

    class Config:
        from_attributes = True


class WebhookScanResult(BaseModel):
    """Payload from n8n when a scan completes."""
    scan_id: str
    broker_domain: str
    url: Optional[str] = None
    found_listing: bool
    data_found: Optional[dict] = None
    error_message: Optional[str] = None


class WebhookCAPAUpdate(BaseModel):
    """Payload from n8n when CAPTCHA status changes."""
    scan_id: str
    broker_domain: str
    captcha_required: bool
    captcha_type: Optional[str] = None


class WebhookRemovalResult(BaseModel):
    """Payload from n8n when a removal request completes."""
    request_id: str
    broker_domain: str
    success: bool
    status: str = Field(..., description="e.g., 'confirmed', 'pending_review', 'failed'")
    message: Optional[str] = None


class WebhookAckResponse(BaseModel):
    """Standard webhook acknowledgment response."""
    received: bool = True
    processed_at: Optional[str] = None
