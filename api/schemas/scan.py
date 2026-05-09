"""Scan-related Pydantic schemas."""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel


class ScanCreateRequest(BaseModel):
    """Request body for triggering a new deletion scan."""

    profile_id: str


class ScanResponse(BaseModel):
    """Single scan object returned in API responses."""

    id: str
    user_id: str
    profile_id: Optional[str] = None
    status: str  # running, completed, failed, cancelled
    broker_count: int = 0
    request_count: int = 0
    success_count: int = 0
    failure_count: int = 0
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ScanListResponse(BaseModel):
    """Paginated list of scans."""

    success: bool = True
    data: List[ScanResponse]
    total: int = 0


class ScanDetailResponse(BaseModel):
    """Single scan detail."""

    success: bool = True
    data: ScanResponse