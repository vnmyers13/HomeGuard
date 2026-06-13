"""WebSocket endpoints for real-time scan progress."""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import text

from database import get_db
from models.scanning import ScanRun

router = APIRouter()


@router.websocket("/ws/scans/{scan_id}")
async def scan_progress_websocket(
    websocket: WebSocket,
    scan_id: str,
    db: Session = Depends(get_db),
):
    """WebSocket endpoint for real-time scan progress updates.

    Connect to get live updates on scan progress including:
    - Status changes (pending -> running -> completed/failed)
    - Broker completion counts
    - Exposure findings
    """
    # Verify scan exists
    scan = db.query(ScanRun).filter(
        ScanRun.id == text(f"'{scan_id}'")
    ).first()

    if not scan:
        await websocket.close(code=4004, reason="Scan not found")
        return

    from services.websocket_manager import ws_manager

    await websocket.accept()
    await ws_manager.connect(scan_id, websocket)

    try:
        # Send initial state
        initial_data = {
            "status": scan.status,
            "total_brokers": scan.total_brokers,
            "completed_brokers": scan.completed_brokers,
            "exposures_found": scan.exposures_found,
            "exposures_removed": scan.exposures_removed,
            "started_at": scan.started_at.isoformat() if scan.started_at else None,
            "completed_at": scan.completed_at.isoformat() if scan.completed_at else None,
        }
        import json
        await websocket.send_text(json.dumps({
            "type": "scan_progress",
            "scan_id": scan_id,
            "data": initial_data,
            "timestamp": scan.started_at.isoformat() if scan.started_at else None,
        }))

        # Keep connection alive and poll for updates
        while True:
            await asyncio.sleep(2)
            # Refresh scan from DB
            db.refresh(scan)
            if scan.status in ("completed", "failed", "cancelled"):
                break

    except WebSocketDisconnect:
        pass
    except Exception:
        pass
    finally:
        await ws_manager.disconnect(scan_id, websocket)
