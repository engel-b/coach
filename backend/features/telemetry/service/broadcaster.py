from fastapi import WebSocket, WebSocketDisconnect


class TelemetryBroadcaster:
    """
    Verteilt Telemetrie an alle verbundenen Frontend-Clients.

    Der Broadcaster kennt keine fachlichen Telemetriedaten.
    Für ihn ist jede Nachricht lediglich ein String, der an
    die verbundenen WebSockets weitergereicht wird.
    """

    def __init__(self) -> None:
        self._connections: set[WebSocket] = set()

    async def connect(
        self,
        websocket: WebSocket,
    ) -> None:
        await websocket.accept()
        self._connections.add(websocket)

    def disconnect(
        self,
        websocket: WebSocket,
    ) -> None:
        self._connections.discard(websocket)

    async def broadcast(
        self,
        message: str,
    ) -> None:
        disconnected: list[WebSocket] = []

        for websocket in self._connections:
            try:
                await websocket.send_text(message)
            except (
                WebSocketDisconnect,
                RuntimeError,
            ):
                disconnected.append(websocket)

        for websocket in disconnected:
            self.disconnect(websocket)
