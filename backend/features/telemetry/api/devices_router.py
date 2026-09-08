from fastapi import APIRouter

from apps.api import wiring
from features.telemetry.api.contracts.device import DeviceResponse

router = APIRouter()


@router.get(
    "/api/devices",
    response_model=list[DeviceResponse],
    response_model_by_alias=True,
    summary="Bekannte Geräte abrufen",
    description=(
        "Liefert den aktuellen Zustand aller dem Backend bekannten "
        "Trainingsgeräte. Dazu gehören Verbindungsstatus, Zeitpunkt "
        "der letzten Meldung und die zuletzt verfügbaren Messwerte.\n\n"
        "Nicht jedes Gerät unterstützt alle Messwerte. Nicht verfügbare "
        "Werte werden als null zurückgegeben. Die Antwort verwendet "
        "camelCase-Feldnamen."
    ),
)
async def devices() -> list[DeviceResponse]:
    """
    Liefert den aktuellen Zustand aller bekannten Geräte.

    Der interne DeviceState verwendet Python-konformes snake_case.
    An der HTTP-Grenze serialisieren wir die Felder als camelCase.
    """

    return [
        DeviceResponse(
            device_id=device.device_id,
            device_type=device.device_type,
            device_name=device.device_name,
            status=device.status,
            last_seen=device.last_seen,
            heart_rate_bpm=device.heart_rate_bpm,
            speed_kmh=device.speed_kmh,
            cadence_rpm=device.cadence_rpm,
            distance_m=device.distance_m,
            power_w=device.power_w,
            resistance=device.resistance,
        )
        for device in wiring.telemetry_service.get_devices()
    ]
