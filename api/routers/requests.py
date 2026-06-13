"""Removal requests router - CRUD for removal requests, followups, and verification scans."""

import io
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import text

from database import get_db
from security import require_auth
from models.requests import RemovalRequest, RequestStatusLog, Followup, VerificationScan
from schemas.request import (
    RemovalRequestCreate, RemovalRequestUpdate, RemovalRequestResponse,
    RemovalRequestListResponse, RemovalRequestDetailResponse,
    RequestStatusLogResponse, FollowupCreate, FollowupResponse,
    VerificationScanCreate, VerificationScanResponse,
)

router = APIRouter(prefix="/requests", tags=["removal-requests"])


# --- List removal requests ---

@router.get("", response_model=RemovalRequestListResponse)
async def list_requests(
    user_id: str = Depends(require_auth),
    status: Optional[str] = Query(None, description="Filter by status"),
    removal_method: Optional[str] = Query(None, description="Filter by removal method"),
    profile_id: Optional[str] = Query(None, description="Filter by profile"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    """List removal requests for the authenticated user's household."""
    from models.auth import Household, User

    # Get user's household profiles
    user = db.query(User).filter(User.id == text(f"'{user_id}'")).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    household = db.query(Household).filter(Household.id == user.household_id).first()
    if not household:
        return RemovalRequestListResponse(data=[], total=0)

    query = db.query(RemovalRequest).join(
        RemovalRequest.profile
    ).filter(
        RemovalRequest.profile.has(HouseholdId=household.id)
    )

    if status:
        query = query.filter(RemovalRequest.status == status)
    if removal_method:
        query = query.filter(RemovalRequest.removal_method == removal_method)
    if profile_id:
        query = query.filter(RemovalRequest.profile_id == text(f"'{profile_id}'"))

    total = query.count()
    requests = query.order_by(RemovalRequest.created_at.desc()).offset(offset).limit(limit).all()

    return RemovalRequestListResponse(
        data=[RemovalRequestResponse.model_validate(r) for r in requests],
        total=total,
    )


# --- Request detail ---

@router.get("/{request_id}", response_model=RemovalRequestDetailResponse)
async def get_request(
    request_id: str,
    user_id: str = Depends(require_auth),
    db: Session = Depends(get_db),
):
    """Get a single removal request by ID."""
    from models.auth import Household, User

    request = db.query(RemovalRequest).join(
        RemovalRequest.profile
    ).join(
        RemovalRequest.profile.Household
    ).filter(
        RemovalRequest.id == text(f"'{request_id}'"),
        Household.user_id == text(f"'{user_id}'"),
    ).first()

    if not request:
        raise HTTPException(status_code=404, detail="Removal request not found")

    return RemovalRequestDetailResponse(data=RemovalRequestResponse.model_validate(request))


# --- Create removal request ---

@router.post("", response_model=RemovalRequestDetailResponse)
async def create_request(
    body: RemovalRequestCreate,
    user_id: str = Depends(require_auth),
    db: Session = Depends(get_db),
):
    """Create a new removal request."""
    from models.auth import Household, User
    import uuid

    user = db.query(User).filter(User.id == text(f"'{user_id}'")).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    household = db.query(Household).filter(Household.id == user.household_id).first()
    if not household:
        raise HTTPException(status_code=404, detail="Household not found")

    # Verify profile belongs to household
    profile = db.query(
        text("SELECT 1 FROM identity.profiles WHERE id = :pid AND household_id = :hid")
    ).params(pid=body.profile_id, hid=household.id).first()
    if not profile:
        raise HTTPException(status_code=400, detail="Profile does not belong to your household")

    request = RemovalRequest(
        id=uuid.uuid4(),
        profile_id=body.profile_id,
        broker_id=body.broker_id,
        removal_method=body.removal_method,
        status="pending",
    )
    db.add(request)
    db.flush()

    # Create status log
    status_log = RequestStatusLog(
        request_id=request.id,
        new_status="pending",
        change_reason="Request created",
    )
    db.add(status_log)
    db.commit()
    db.refresh(request)

    return RemovalRequestDetailResponse(data=RemovalRequestResponse.model_validate(request))


# --- Update removal request ---

@router.patch("/{request_id}", response_model=RemovalRequestDetailResponse)
async def update_request(
    request_id: str,
    body: RemovalRequestUpdate,
    user_id: str = Depends(require_auth),
    db: Session = Depends(get_db),
):
    """Update a removal request status."""
    from models.auth import Household, User

    request = db.query(RemovalRequest).join(
        RemovalRequest.profile
    ).join(
        RemovalRequest.profile.Household
    ).filter(
        RemovalRequest.id == text(f"'{request_id}'"),
        Household.user_id == text(f"'{user_id}'"),
    ).first()

    if not request:
        raise HTTPException(status_code=404, detail="Removal request not found")

    old_status = request.status
    if body.status:
        request.status = body.status
    if body.confirmation_message is not None:
        request.confirmation_message = body.confirmation_message
    if body.next_action_at is not None:
        request.next_action_at = body.next_action_at

    # Create status log
    status_log = RequestStatusLog(
        request_id=request.id,
        previous_status=old_status,
        new_status=request.status,
        change_reason=f"Status updated from {old_status} to {request.status}",
    )
    db.add(status_log)
    db.commit()
    db.refresh(request)

    return RemovalRequestDetailResponse(data=RemovalRequestResponse.model_validate(request))


# --- Delete removal request ---

@router.delete("/{request_id}")
async def delete_request(
    request_id: str,
    user_id: str = Depends(require_auth),
    db: Session = Depends(get_db),
):
    """Delete a removal request."""
    from models.auth import Household, User

    request = db.query(RemovalRequest).join(
        RemovalRequest.profile
    ).join(
        RemovalRequest.profile.Household
    ).filter(
        RemovalRequest.id == text(f"'{request_id}'"),
        Household.user_id == text(f"'{user_id}'"),
    ).first()

    if not request:
        raise HTTPException(status_code=404, detail="Removal request not found")

    db.delete(request)
    db.commit()

    return {"success": True, "message": "Removal request deleted"}


# --- Request status logs ---

@router.get("/{request_id}/logs", response_model=dict)
async def get_request_logs(
    request_id: str,
    user_id: str = Depends(require_auth),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    """Get status change logs for a removal request."""
    from models.auth import Household, User

    # Verify ownership
    request = db.query(RemovalRequest).join(
        RemovalRequest.profile
    ).join(
        RemovalRequest.profile.Household
    ).filter(
        RemovalRequest.id == text(f"'{request_id}'"),
        Household.user_id == text(f"'{user_id}'"),
    ).first()

    if not request:
        raise HTTPException(status_code=404, detail="Removal request not found")

    logs = db.query(RequestStatusLog).filter(
        RequestStatusLog.request_id == text(f"'{request_id}'")
    ).order_by(RequestStatusLog.created_at.desc()).limit(limit).all()

    return {
        "data": [RequestStatusLogResponse.model_validate(l) for l in logs],
        "total": len(logs),
    }


# --- List followups ---

@router.get("/{request_id}/followups", response_model=dict)
async def list_followups(
    request_id: str,
    user_id: str = Depends(require_auth),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    """Get followups for a removal request."""
    from models.auth import Household, User

    # Verify ownership
    request = db.query(RemovalRequest).join(
        RemovalRequest.profile
    ).join(
        RemovalRequest.profile.Household
    ).filter(
        RemovalRequest.id == text(f"'{request_id}'"),
        Household.user_id == text(f"'{user_id}'"),
    ).first()

    if not request:
        raise HTTPException(status_code=404, detail="Removal request not found")

    followups = db.query(Followup).filter(
        Followup.request_id == text(f"'{request_id}'")
    ).order_by(Followup.followup_number.desc()).limit(limit).all()

    return {
        "data": [FollowupResponse.model_validate(f) for f in followups],
        "total": len(followups),
    }


# --- Create followup ---

@router.post("/{request_id}/followups", response_model=FollowupResponse)
async def create_followup(
    request_id: str,
    body: FollowupCreate,
    user_id: str = Depends(require_auth),
    db: Session = Depends(get_db),
):
    """Create a followup for a removal request."""
    from models.auth import Household, User
    import uuid

    # Verify ownership
    request = db.query(RemovalRequest).join(
        RemovalRequest.profile
    ).join(
        RemovalRequest.profile.Household
    ).filter(
        RemovalRequest.id == text(f"'{request_id}'"),
        Household.user_id == text(f"'{user_id}'"),
    ).first()

    if not request:
        raise HTTPException(status_code=404, detail="Removal request not found")

    # Get next followup number
    max_followup = db.query(text("SELECT COALESCE(MAX(followup_number), 0) as max_num FROM requests.followups WHERE request_id = :rid")).params(rid=request_id).first()
    next_number = max_followup.max_num + 1

    followup = Followup(
        id=uuid.uuid4(),
        request_id=request_id,
        followup_number=next_number,
        method_used=body.method_used,
        response_received=False,
        response_details=body.response_details,
        scheduled_at=body.scheduled_at or datetime.utcnow(),
    )
    db.add(followup)
    request.followup_count += 1
    db.commit()
    db.refresh(followup)

    return FollowupResponse.model_validate(followup)


# --- List verification scans ---

@router.get("/{request_id}/verification-scans", response_model=dict)
async def list_verification_scans(
    request_id: str,
    user_id: str = Depends(require_auth),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    """Get verification scans for a removal request."""
    from models.auth import Household, User

    # Verify ownership
    request = db.query(RemovalRequest).join(
        RemovalRequest.profile
    ).join(
        RemovalRequest.profile.Household
    ).filter(
        RemovalRequest.id == text(f"'{request_id}'"),
        Household.user_id == text(f"'{user_id}'"),
    ).first()

    if not request:
        raise HTTPException(status_code=404, detail="Removal request not found")

    scans = db.query(VerificationScan).filter(
        VerificationScan.removal_request_id == text(f"'{request_id}'")
    ).order_by(VerificationScan.scheduled_at.desc()).limit(limit).all()

    return {
        "data": [VerificationScanResponse.model_validate(s) for s in scans],
        "total": len(scans),
    }


# --- Create verification scan ---

@router.post("/{request_id}/verification-scans", response_model=VerificationScanResponse)
async def create_verification_scan(
    request_id: str,
    body: VerificationScanCreate,
    user_id: str = Depends(require_auth),
    db: Session = Depends(get_db),
):
    """Create a verification scan for a removal request."""
    from models.auth import Household, User
    import uuid

    # Verify ownership
    request = db.query(RemovalRequest).join(
        RemovalRequest.profile
    ).join(
        RemovalRequest.profile.Household
    ).filter(
        RemovalRequest.id == text(f"'{request_id}'"),
        Household.user_id == text(f"'{user_id}'"),
    ).first()

    if not request:
        raise HTTPException(status_code=404, detail="Removal request not found")

    scan = VerificationScan(
        id=uuid.uuid4(),
        removal_request_id=request_id,
        profile_id=body.profile_id,
        broker_id=body.broker_id,
        scheduled_at=datetime.utcnow(),
    )
    db.add(scan)
    db.commit()
    db.refresh(scan)

    return VerificationScanResponse.model_validate(scan)


# --- Download legal letter PDF ---

@router.get("/{request_id}/pdf")
async def download_legal_letter_pdf(
    request_id: str,
    letter_type: str = Query("ccpa", description="Letter type: ccpa or gdpr"),
    user_id: str = Depends(require_auth),
    db: Session = Depends(get_db),
):
    """Download a legal letter PDF for a removal request."""
    from models.auth import Household, User, HouseholdProfile
    from fastapi.responses import StreamingResponse
    import uuid

    # Verify ownership
    request = db.query(RemovalRequest).join(
        RemovalRequest.profile
    ).join(
        RemovalRequest.profile.Household
    ).filter(
        RemovalRequest.id == text(f"'{request_id}'"),
        Household.user_id == text(f"'{user_id}'"),
    ).first()

    if not request:
        raise HTTPException(status_code=404, detail="Removal request not found")

    # Get profile data
    profile = db.query(HouseholdProfile).filter(
        HouseholdProfile.id == text(f"'{request.profile_id}'")
    ).first()

    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    # Get broker data
    broker = db.query(
        text("SELECT name, domain, address FROM registry.brokers WHERE id = :bid")
    ).params(bid=request.broker_id).first()

    # Get user/household data
    user = db.query(User).filter(User.id == text(f"'{user_id}'")).first()
    household = db.query(Household).filter(Household.id == user.household_id).first() if user else None

    if not household:
        raise HTTPException(status_code=404, detail="Household not found")

    profile_data = {
        "full_name": profile.full_name or "Valued Customer",
        "dob": profile.birth_date or "N/A",
        "emails": [e.value for e in profile.aliases] if hasattr(profile, 'aliases') else [],
        "phones": [p.value for p in profile.fields if hasattr(profile, 'fields')] if hasattr(profile, 'fields') else [],
        "addresses": [f.value for f in profile.fields if hasattr(profile, 'fields')] if hasattr(profile, 'fields') else [],
    }

    # Generate PDF
    from services.pdf_service import generate_ccpa_letter_pdf

    pdf_bytes = generate_ccpa_letter_pdf(
        recipient_name=broker.name if broker else "Unknown Broker",
        recipient_address=broker.address if broker else "",
        broker_name=household.name if household else "HomeGuard User",
        broker_address="",
        profile_data=profile_data,
        request_id=str(request.id),
    )

    filename = f"{letter_type}_letter_{request_id[:8]}.pdf"

    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
