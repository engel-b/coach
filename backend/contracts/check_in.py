from datetime import datetime

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


class CheckInRequest(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

    energy: int
    recovery: int
    muscle_soreness: int
    stress: int
    available_training_minutes: int


class CheckInResponse(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

    person_id: int
    timestamp: datetime

    energy: int
    recovery: int
    muscle_soreness: int
    stress: int

    available_training_minutes: int
