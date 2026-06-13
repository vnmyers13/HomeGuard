"""Removal requests schemas - Pydantic models for the requests API."""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel


class RemovalRequestCreate(BaseModel):
    """Create a new removal request."""
    profile_id: str
    broker_id: str
    removal_method: str  # web_form, email, legal_letter


class RemovalRequestUpdate(BaseModel):
    """Update an existing removal request."""
    status: Optional[str] = None
    confirmation_message: Optional[str] = None
    next_action_at: Optional[datetime] = None


class RemovalRequestResponse(BaseModel):
    """Single removal request response."""
    id: str
    profile_id: str
    broker_id: str
    exposure_id: Optional[str] = None
    removal_method: str
    status: str
    confirmation_message: Optional[str] = None
    next_action_at: Optional[datetime] = None
    followup_count: int = 0
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class RemovalRequestListResponse(BaseModel):
    """Paginated list of removal requests."""
    success: bool = True
    data: List[RemovalRequestResponse]
    total: int = 0


class RemovalRequestDetailResponse(BaseModel):
    """Single removal request detail with related data."""
    success: bool = True
    data: RemovalRequestResponse


class RequestStatusLogResponse(BaseModel):
    """Status log entry."""
    id: str
    request_id: str
    previous_status: Optional[str] = None
    new_status: str
    change_reason: Optional[str] = None
    meta_data: Optional[dict] = None
    created_at: datetime

    class Config:
        from_attributes = True


class FollowupCreate(BaseModel):
    """Create a followup for a removal request."""
    method_used: str
    response_details: Optional[str] = None
    scheduled_at: Optional[datetime] = None


class FollowupResponse(BaseModel):
    """Followup response."""
    id: str
    request_id: str
    followup_number: int
    method_used: str
    response_received: bool = False
    response_details: Optional[str] = None
    scheduled_at: datetime
    executed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class VerificationScanCreate(BaseModel):
    """Create a verification scan."""
    profile_id: str
    broker_id: str


class VerificationScanResponse(BaseModel):
    """Verification scan response."""
    id: str
    removal_request_id: str
    profile_id: str
    broker_id: str
    result: Optional[str] = None
    evidence_path: Optional[str] = None
    scheduled_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True
