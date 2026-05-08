"""Pydantic schemas for profile endpoints."""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class ProfileFieldCreate(BaseModel):
    field_type: str = Field(..., pattern="^(address|phone|email|alias)$")
    value: str = Field(..., min_length=1)


class ProfileFieldResponse(BaseModel):
    id: str
    field_type: str
    value: str  # decrypted for response
    is_current: bool
    effective_from: datetime
    effective_to: Optional[datetime]

    class Config:
        from_attributes = True


class ProfileCreate(BaseModel):
    full_legal_name: str = Field(..., min_length=1)
    date_of_birth: Optional[datetime] = None


class ProfileResponse(BaseModel):
    id: str
    full_legal_name: str  # decrypted for response
    date_of_birth: Optional[datetime]
    exposure_score: float
    is_current: bool
    created_at: datetime
    fields: List[ProfileFieldResponse] = []

    class Config:
        from_attributes = True


class ProfileUpdate(BaseModel):
    full_legal_name: Optional[str] = None
    date_of_birth: Optional[datetime] = None


class ProfileDeleteResponse(BaseModel):
    message: str
    archived_profile_id: Optional[str] = None