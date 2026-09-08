from datetime import date
from typing import Self

from pydantic import BaseModel, ConfigDict, Field, model_validator
from pydantic.alias_generators import to_camel

from domains.person.profile import TrainingGoal


class CreatePersonRequest(BaseModel):
    """Daten zum Anlegen einer Person und ihres Trainingsprofils."""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        str_strip_whitespace=True,
    )

    display_name: str = Field(
        min_length=1,
        max_length=100,
        description="Anzeigename der neuen Person.",
        examples=["Person 5"],
    )
    date_of_birth: date = Field(
        description="Geburtsdatum im ISO-Format YYYY-MM-DD.",
        examples=["1990-03-15"],
    )
    height_cm: int = Field(
        ge=100,
        le=250,
        description="Körpergröße in Zentimetern.",
        examples=[172],
    )
    training_goal: TrainingGoal = Field(
        description=("Trainingsziel: allgemeine Fitness, Muskelaufbau, Abnehmen oder Ausdauer."),
        examples=["general_fitness"],
    )
    max_heart_rate_bpm: int | None = Field(
        default=None,
        ge=100,
        le=230,
        description=("Optionaler, individuell bekannter Maximalpuls in Schlägen pro Minute."),
        examples=[190],
    )
    start_weight_kg: float | None = Field(
        default=None,
        gt=0,
        le=500,
        description=("Startgewicht in Kilogramm. Für das Trainingsziel Abnehmen erforderlich."),
        examples=[92.5],
    )
    target_weight_kg: float | None = Field(
        default=None,
        gt=0,
        le=500,
        description=(
            "Zielgewicht in Kilogramm. Für Abnehmen erforderlich und kleiner als das Startgewicht."
        ),
        examples=[82.0],
    )

    @model_validator(mode="after")
    def validate_weight_goal(self) -> Self:
        if self.training_goal == TrainingGoal.WEIGHT_LOSS:
            if self.start_weight_kg is None or self.target_weight_kg is None:
                raise ValueError("Für Abnehmen sind Start- und Zielgewicht erforderlich.")

            if self.target_weight_kg >= self.start_weight_kg:
                raise ValueError("Das Zielgewicht muss unter dem Startgewicht liegen.")

        return self
