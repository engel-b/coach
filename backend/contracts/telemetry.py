from datetime import datetime

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


class TelemetryMessage(BaseModel):
    """
    Transportformat für Nachrichten zwischen Device Agent und Backend.

    Python-intern verwenden wir snake_case:

        device_id

    Auf der WebSocket-/JSON-Schnittstelle verwenden wir camelCase:

        deviceId

    Die Umwandlung übernimmt Pydantic automatisch über `to_camel`.

    Java-Vergleich:
    Das ist ähnlich zu einer Jackson-Konfiguration mit einer
    PropertyNamingStrategy für camelCase/snake_case.
    """

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

    type: str
    timestamp: datetime
    device_id: str
    payload: dict[str, object]
