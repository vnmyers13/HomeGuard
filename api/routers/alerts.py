"""Alerts router - list, create, and acknowledge alerts."""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from database import get_db
from security import require_auth
from models.scanning import Exposure

router = APIRouter(prefix="/alerts", tags=["alerts"])


# --- List alerts ---

@router.get("", response_model=dict)
async def list_alerts(
    user_id: str = Depends(require_auth),
    severity: Optional[str] = Query(None, description="Filter by severity"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    """List alerts for the authenticated user."""
    query = db.query(Exposure).filter(Exposure.user_id == user_id)

    if severity:
        query = query.filter(Exposure.severity == severity)

    total = query.count()
    alerts = query.order_by(Exposure.created_at.desc()).offset(offset).limit(limit).all()

    return {
        "data": [
            {
                "id": str(a.id),
                "broker_name": a.broker_name or "",
                "severity": a.severity or "medium",
                "status": a.status or "active",
                "created_at": a.created_at.isoformat() if a.created_at else None,
            }
            for a in alerts
        ],
        "total": total,
    }


# --- Alert detail ---

@router.get("/{alert_id}", response_model=dict)
async def get_alert(
    alert_id: str,
    user_id: str = Depends(require_auth),
    db: Session = Depends(get_db),
):
    """Get a single alert by ID."""
    alert = db.query(Exposure).filter(
        Exposure.id == alert_id,
        Exposure.user_id == user_id,
    ).first()

    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    return {
        "data": {
            "id": str(alert.id),
            "broker_name": alert.broker_name or "",
            "severity": alert.severity or "medium",
            "status": alert.status or "active",
            "created_at": alert.created_at.isoformat() if alert.created_at else None,
        }
    }


# --- Acknowledge alert ---

@router.post("/{alert_id}/acknowledge", response_model=dict)
async def acknowledge_alert(
    alert_id: str,
    user_id: str = Depends(require_auth),
    db: Session = Depends(get_db),
):
    """Mark an alert as acknowledged."""
    alert = db.query(Exposure).filter(
        Exposure.id == alert_id,
        Exposure.user_id == user_id,
    ).first()

    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    alert.status = "acknowledged"
    db.commit()
    db.refresh(alert)

    return {"data": {"id": str(alert.id), "status": "acknowledged"}}
