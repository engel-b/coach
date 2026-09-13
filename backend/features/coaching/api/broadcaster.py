from fastapi import WebSocket, WebSocketDisconnect


class LiveCoachingBroadcaster:
    """Verteilt Live-Coaching-Events an verbundene Frontend-Clients."""

    def __init__(self) -> None:
        self._connections: set[WebSocket] = set()

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self._connections.add(websocket)

    def disconnect(self, websocket: WebSocket) -> None:
        self._connections.discard(websocket)

    async def broadcast(self, message: str) -> None:
        disconnected: list[WebSocket] = []

        for websocket in self._connections:
            try:
                await websocket.send_text(message)
            except (WebSocketDisconnect, RuntimeError):
                disconnected.append(websocket)

        for websocket in disconnected:
            self.disconnect(websocket)
