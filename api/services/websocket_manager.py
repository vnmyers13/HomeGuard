"""WebSocket manager for real-time scan progress updates."""

import asyncio
from typing import Dict, Set
from datetime import datetime


class WebSocketManager:
    """Manages WebSocket connections and broadcasts scan progress updates."""

    def __init__(self):
        self._connections: Dict[str, Set] = {}  # scan_id -> set of WebSocket instances
        self._lock = asyncio.Lock()

    async def connect(self, scan_id: str, websocket) -> bool:
        """Connect a WebSocket to a scan progress channel."""
        async with self._lock:
            if scan_id not in self._connections:
                self._connections[scan_id] = set()
            self._connections[scan_id].add(websocket)
        return True

    async def disconnect(self, scan_id: str, websocket):
        """Disconnect a WebSocket from a scan progress channel."""
        async with self._lock:
            if scan_id in self._connections:
                self._connections[scan_id].discard(websocket)
                if not self._connections[scan_id]:
                    del self._connections[scan_id]

    async def broadcast_progress(self, scan_id: str, data: dict):
        """Broadcast progress update to all connected WebSockets for a scan."""
        import json
        async with self._lock:
            if scan_id not in self._connections:
                return
            connections = list(self._connections[scan_id])

        message = json.dumps({
            "type": "scan_progress",
            "scan_id": scan_id,
            "data": data,
            "timestamp": datetime.utcnow().isoformat(),
        })

        for ws in connections:
            try:
                await ws.send_text(message)
            except Exception:
                await self.disconnect(scan_id, ws)

    def get_connection_count(self, scan_id: str) -> int:
        """Get the number of connected WebSockets for a scan."""
        return len(self._connections.get(scan_id, set()))


# Global singleton
ws_manager = WebSocketManager()
