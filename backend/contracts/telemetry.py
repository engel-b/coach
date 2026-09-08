from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel


class TelemetryMessage(BaseModel):
    """
    Transportformat für Nachrichten zwischen Device Agent und Backend.

    Python-intern verwenden wir snake_case, auf der WebSocket-/JSON-
    Schnittstelle camelCase. Die Umwandlung übernimmt Pydantic über
    den Alias-Generator.

    Der Payload ist bewusst ein allgemeines Dictionary. Die fachliche
    Interpretation erfolgt im TelemetryService und nicht in diesem
    Transport-Contract.
    """

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

    type: str = Field(
        description=(
            "Nachrichtentyp. Er bestimmt, wie der TelemetryService "
            "den Payload fachlich interpretiert."
        ),
    )
    timestamp: datetime = Field(
        description="Zeitpunkt der Telemetriemeldung.",
        examples=["2026-09-08T09:30:00Z"],
    )
    device_id: str = Field(
        description="Eindeutige Kennung des Geräts, auf das sich die Meldung bezieht.",
        examples=["heart-rate-01"],
    )
    payload: dict[str, object] = Field(
        description=(
            "Nachrichtentypspezifische Daten. Die unterstützten Felder "
            "hängen vom Nachrichtentyp und vom jeweiligen Geräteadapter ab."
        ),
    )