import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from pydantic import ValidationError

from apps.api import wiring
from contracts.telemetry import TelemetryMessage

logger = logging.getLogger(__name__)

router = APIRouter()


@router.websocket("/ws/device-agent")
async def device_agent_websocket(
    websocket: WebSocket,
) -> None:
    await websocket.accept()

    logger.info("Device Agent connected")

    try:
        while True:
            raw_message = await websocket.receive_text()

            try:
                message = TelemetryMessage.model_validate_json(
                    raw_message,
                )
            except ValidationError as exc:
                logger.warning(
                    "Invalid telemetry message: %s",
                    exc,
                )
                continue

            wiring.telemetry_service.handle(message)

            await wiring.telemetry_broadcaster.broadcast(
                message.model_dump_json(
                    by_alias=True,
                )
            )

            logger.debug(
                "Telemetry: type=%s device=%s",
                message.type,
                message.device_id,
            )

    except WebSocketDisconnect:
        logger.info("Device Agent disconnected")


@router.websocket("/ws/telemetry")
async def telemetry_websocket(
    websocket: WebSocket,
) -> None:
    await wiring.telemetry_broadcaster.connect(websocket)

    logger.info("Frontend telemetry client connected")

    try:
        while True:
            await websocket.receive_text()

    except WebSocketDisconnect:
        wiring.telemetry_broadcaster.disconnect(websocket)

        logger.info("Frontend telemetry client disconnected")
