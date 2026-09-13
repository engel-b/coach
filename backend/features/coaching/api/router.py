import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from apps.api import wiring

logger = logging.getLogger(__name__)

router = APIRouter()


@router.websocket("/ws/coaching")
async def live_coaching_websocket(websocket: WebSocket) -> None:
    """
    Ausgehender Event-Stream für relevante Live-Coaching-Entscheidungen.

    Der Client empfängt nur Coaching-Events, bei denen eine konkrete
    Trainingsaktion empfohlen wird. Rohtelemetrie bleibt auf /ws/telemetry.
    """

    await wiring.live_coaching_broadcaster.connect(websocket)
    logger.info("Frontend live coaching client connected")

    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        wiring.live_coaching_broadcaster.disconnect(websocket)
        logger.info("Frontend live coaching client disconnected")
