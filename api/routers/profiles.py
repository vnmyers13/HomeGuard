"""Profile management router.

Endpoints:
  GET    /api/v1/profiles              – list profiles (with filters)
  POST   /api/v1/profiles              – create a new profile
  GET    /api/v1/profiles/{id}         – get a single profile
  PATCH  /api/v1/profiles/{id}         – update a profile
  DELETE /api/v1/profiles/{id}         – delete a profile (soft)
"""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_session
from schemas.profile import (
    ProfileCreate,
    ProfileResponse,
    ProfileUpdate,
)
from services.profile_service import ProfileService

router = APIRouter(prefix="/api/v1", tags=["profiles"])


# ---------------------------------------------------------------------------
# Dependency injection helper
# ---------------------------------------------------------------------------

async def get_profile_service(db: AsyncSession = Depends(get_session)) -> ProfileService:
    """Return a ProfileService bound to the current async DB session."""
    return ProfileService(db)


# ---------------------------------------------------------------------------
# CRUD endpoints
# ---------------------------------------------------------------------------

@router.get("/profiles", response_model=list[ProfileResponse])
async def list_profiles(
    active: Optional[bool] = Query(None, description="Filter by active status"),
    svc: ProfileService = Depends(get_profile_service),
):
    """List all profiles, optionally filtering by active status."""
    return await svc.list_all(active=active)


@router.post(
    "/profiles",
    response_model=ProfileResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_profile(
    payload: ProfileCreate,
    svc: ProfileService = Depends(get_profile_service),
):
    """Create a new profile."""
    return await svc.create(
        first_name=payload.first_name,
        middle_name=payload.middle_name,
        last_name=payload.last_name,
        dob=payload.dob,
        email=payload.email,
        phone=payload.phone,
        address_line1=payload.address_line1,
        address_line2=payload.address_line2,
        city=payload.city,
        state=payload.state,
        postal_code=payload.postal_code,
        country=payload.country,
    )


@router.get("/profiles/{profile_id}", response_model=ProfileResponse)
async def get_profile(
    profile_id: UUID,
    svc: ProfileService = Depends(get_profile_service),
):
    """Retrieve a single profile by ID."""
    return await svc.get_by_id(profile_id)


@router.patch("/profiles/{profile_id}", response_model=ProfileResponse)
async def update_profile(
    profile_id: UUID,
    payload: ProfileUpdate,
    svc: ProfileService = Depends(get_profile_service),
):
    """Update mutable fields on a profile."""
    return await svc.update(profile_id, payload.model_dump(exclude_unset=True))


@router.delete("/profiles/{profile_id}")
async def delete_profile(
    profile_id: UUID,
    svc: ProfileService = Depends(get_profile_service),
):
    """Soft-delete a profile by setting active=False."""
    return await svc.delete(profile_id)