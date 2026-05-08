"""Broker management and scan API router.

Endpoints:
  GET    /api/v1/brokers              - list brokers (active only by default)
  POST   /api/v1/brokers              - register a new broker (auto-playbook)
  GET    /api/v1/brokers/{broker_id}  - retrieve a single broker
  PATCH  /api/v1/brokers/{broker_id}  - update mutable fields
  DELETE /api/v1/brokers/{broker_id}  - soft-delete (deactivate)
  POST   /api/v1/brokers/{broker_id}/health-check - health check
  POST   /api/v1/profiles/{profile_id}/scan         - trigger scan
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_async_db
from schemas.broker import BrokerCreate, BrokerResponse, BrokerUpdate, ScanRequest, ScanResponse
from services.broker_service import BrokerService

router = APIRouter(prefix="/api/v1", tags=["brokers"])


# ---------------------------------------------------------------------------
# Dependency injection helper
# ---------------------------------------------------------------------------

async def get_broker_service(db: AsyncSession = Depends(get_async_db)) -> BrokerService:
    """Return a BrokerService bound to the current async DB session."""
    return BrokerService(db)


# ---------------------------------------------------------------------------
# CRUD endpoints
# ---------------------------------------------------------------------------

@router.get("/brokers", response_model=list[BrokerResponse])
async def list_brokers(
    active_only: bool = True,
    svc: BrokerService = Depends(get_broker_service),
):
    """List all brokers, optionally filtering to active ones."""
    return await svc.list_all(active_only=active_only)


@router.post(
    "/brokers",
    response_model=BrokerResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_broker(
    payload: BrokerCreate,
    svc: BrokerService = Depends(get_broker_service),
):
    """Register a new broker, auto-loading playbook if available."""
    try:
        return await svc.create(domain=payload.domain, name=payload.name)
    except HTTPException as exc:
        raise exc


@router.get("/brokers/{broker_id}", response_model=BrokerResponse)
async def get_broker(
    broker_id: UUID,
    svc: BrokerService = Depends(get_broker_service),
):
    """Retrieve a single broker by ID."""
    return await svc.get_by_id(broker_id)


@router.patch("/brokers/{broker_id}", response_model=BrokerResponse)
async def update_broker(
    broker_id: UUID,
    payload: BrokerUpdate,
    svc: BrokerService = Depends(get_broker_service),
):
    """Update mutable fields on a broker with audit tracking."""
    try:
        return await svc.update(broker_id, payload.model_dump(exclude_none=True))
    except HTTPException as exc:
        raise exc


@router.delete("/brokers/{broker_id}")
async def delete_broker(
    broker_id: UUID,
    svc: BrokerService = Depends(get_broker_service),
):
    """Soft-delete a broker by deactivating it."""
    return await svc.delete(broker_id)


# ---------------------------------------------------------------------------
# Health check & scanning endpoints
# ---------------------------------------------------------------------------

@router.post("/brokers/{broker_id}/health-check")
async def health_check_broker(
    broker_id: UUID,
    svc: BrokerService = Depends(get_broker_service),
):
    """Ping the broker's opt_out_url to check reachability."""
    return await svc.health_check(broker_id)


@router.post("/profiles/{profile_id}/scan", response_model=ScanResponse)
async def scan_profile(
    profile_id: UUID,
    payload: ScanRequest | None = None,
    svc: BrokerService = Depends(get_broker_service),
):
    """Queue a broker scan for the given profile.

    If `broker_ids` is provided, only those brokers are scanned.
    Otherwise all active brokers for the profile are scanned.
    """
    broker_ids = payload.broker_ids if payload else None

    # Validate profile exists (quick check)
    from sqlalchemy import text
    row = (
        await svc.db.execute(
            text("SELECT id FROM registry.profiles WHERE id = :pid"),
            {"pid": str(profile_id)},
        )
    ).first()

    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Profile {profile_id} not found",
        )

    result = await svc.trigger_scan(str(profile_id), broker_ids)
    return ScanResponse(**result)