"""Pydantic schemas for broker endpoints."""

from enum import Enum
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class BrokerStatus(str, Enum):
    """Broker health/status states."""
    active = "active"
    inactive = "inactive"
    error = "error"


class BrokerCreate(BaseModel):
    domain: str = Field(..., min_length=3)
    name: str = Field(..., min_length=1)


class BrokerUpdate(BaseModel):
    name: Optional[str] = None
    is_active: Optional[bool] = None


class BrokerPlaybookResponse(BaseModel):
    id: str
    version: int
    is_active: bool


class BrokerResponse(BaseModel):
    id: str
    domain: str
    name: str
    is_active: bool
    status: str = "active"
    playbook_version: Optional[int] = None
    health_status: str = "unknown"

    class Config:
        from_attributes = True


class BrokerListResponse(BaseModel):
    """Paginated broker list response."""
    brokers: List[BrokerResponse] = []
    total: int = 0


class BrokerHealthCheck(BaseModel):
    domain: str
    is_reachable: bool
    response_time_ms: Optional[float] = None
    http_status: Optional[int] = None


class BrokerScanRequest(BaseModel):
    profile_id: str
    broker_ids: List[str] = []


class BrokerScanResponse(BaseModel):
    scan_run_id: str
    broker_count: int


class ScanRequest(BaseModel):
    """Request body for scan endpoint with optional broker filter."""
    broker_ids: Optional[List[str]] = None


class ScanResponse(BaseModel):
    """Scan trigger response."""
    scan_run_id: str
    broker_ids_queued: List[str]


class BrokerDeleteResponse(BaseModel):
    success: bool
    message: str