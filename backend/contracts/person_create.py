from datetime import date
from typing import Self

from pydantic import BaseModel, ConfigDict, Field, model_validator
from pydantic.alias_generators import to_camel

from domains.person.profile import TrainingGoal


class CreatePersonRequest(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        str_strip_whitespace=True,
    )

    display_name: str = Field(min_length=1, max_length=100)
    date_of_birth: date
    height_cm: int = Field(ge=100, le=250)
    training_goal: TrainingGoal

    max_heart_rate_bpm: int | None = Field(
        default=None,
        ge=100,
        le=230,
    )
    start_weight_kg: float | None = Field(
        default=None,
        gt=0,
        le=500,
    )
    target_weight_kg: float | None = Field(
        default=None,
        gt=0,
        le=500,
    )

    @model_validator(mode="after")
    def validate_weight_goal(self) -> Self:
        if self.training_goal == TrainingGoal.WEIGHT_LOSS:
            if self.start_weight_kg is None or self.target_weight_kg is None:
                raise ValueError("Für Abnehmen sind Start- und Zielgewicht erforderlich.")

            if self.target_weight_kg >= self.start_weight_kg:
                raise ValueError("Das Zielgewicht muss unter dem Startgewicht liegen.")

        return self
