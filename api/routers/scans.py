"""Scans router - list, detail, trigger, cancel."""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from database import get_db
from security import require_auth
from models.scanning import DeletionScan
from schemas.scan import ScanCreateRequest, ScanResponse, ScanListResponse, ScanDetailResponse

router = APIRouter(prefix="/scans", tags=["scans"])


# --- List scans ---

@router.get("", response_model=ScanListResponse)
async def list_scans(
    user_id: str = Depends(require_auth),
    status: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    """List deletion scans for the authenticated user."""
    query = db.query(DeletionScan).filter(DeletionScan.user_id == user_id)

    if status:
        query = query.filter(DeletionScan.status == status)

    total = query.count()
    scans = query.order_by(DeletionScan.created_at.desc()).offset(offset).limit(limit).all()

    return ScanListResponse(
        data=[ScanResponse.model_validate(s) for s in scans],
        total=total,
    )


# --- Scan detail ---

@router.get("/{scan_id}", response_model=ScanDetailResponse)
async def get_scan(
    scan_id: str,
    user_id: str = Depends(require_auth),
    db: Session = Depends(get_db),
):
    """Get a single scan by ID."""
    scan = db.query(DeletionScan).filter(
        DeletionScan.id == scan_id,
        DeletionScan.user_id == user_id,
    ).first()

    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")

    return ScanDetailResponse(data=ScanResponse.model_validate(scan))


# --- Trigger new scan ---

@router.post("", response_model=ScanDetailResponse)
async def trigger_scan(
    body: ScanCreateRequest,
    user_id: str = Depends(require_auth),
    db: Session = Depends(get_db),
):
    """Trigger a new deletion scan for a profile."""
    import uuid

    scan = DeletionScan(
        id=str(uuid.uuid4()),
        user_id=user_id,
        profile_id=body.profile_id,
        status="running",
    )
    db.add(scan)
    db.commit()
    db.refresh(scan)

    # TODO: dispatch Celery task in Sprint 3
    # from workers.tasks.scanning import run_scan_task
    # run_scan_task.delay(scan.id)

    return ScanDetailResponse(data=ScanResponse.model_validate(scan))


# --- Cancel scan ---

@router.post("/{scan_id}/cancel", response_model=ScanDetailResponse)
async def cancel_scan(
    scan_id: str,
    user_id: str = Depends(require_auth),
    db: Session = Depends(get_db),
):
    """Cancel a running scan."""
    scan = db.query(DeletionScan).filter(
        DeletionScan.id == scan_id,
        DeletionScan.user_id == user_id,
    ).first()

    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")

    if scan.status not in ("running",):
        raise HTTPException(status_code=400, detail="Scan is not currently running")

    scan.status = "cancelled"
    db.commit()
    db.refresh(scan)

    return ScanDetailResponse(data=ScanResponse.model_validate(scan))