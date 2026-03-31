from collections import defaultdict
from uuid import UUID

from fastapi import WebSocket


class ConnectionManager:
    def __init__(self) -> None:
        self.active_connections: dict[UUID, set[WebSocket]] = defaultdict(set)

    async def connect(self, *, session_id: UUID, websocket: WebSocket) -> None:
        await websocket.accept()
        self.active_connections[session_id].add(websocket)

    def disconnect(self, *, session_id: UUID, websocket: WebSocket) -> None:
        if session_id in self.active_connections:
            self.active_connections[session_id].discard(websocket)
            if not self.active_connections[session_id]:
                self.active_connections.pop(session_id, None)

    async def send_json(self, *, session_id: UUID, websocket: WebSocket, payload: dict) -> None:
        await websocket.send_json(payload)

