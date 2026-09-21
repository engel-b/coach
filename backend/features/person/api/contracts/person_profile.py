from datetime import date

from pydantic import BaseModel, ConfigDict, Field, model_validator
from pydantic.alias_generators import to_camel

from features.person.domain.profile import TrainingGoal


class PersonProfileRequest(BaseModel):
    """Stammdaten und Trainingsziele einer Person."""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        str_strip_whitespace=True,
    )

    display_name: str = Field(
        min_length=1,
        max_length=100,
        description="Anzeigename der Person, maximal 100 Zeichen.",
        examples=["Person 1"],
    )
    date_of_birth: date = Field(
        description=(
            "Geburtsdatum im ISO-Format YYYY-MM-DD. "
            "Wird unter anderem zur altersabhängigen Pulsberechnung verwendet."
        ),
        examples=["1985-05-10"],
    )
    height_cm: int = Field(
        ge=100,
        le=250,
        description="Körpergröße in Zentimetern.",
        examples=[175],
    )
    training_goal: TrainingGoal = Field(
        description=("Trainingsziel: allgemeine Fitness, Muskelaufbau, Abnehmen oder Ausdauer."),
        examples=["general_fitness"],
    )
    max_heart_rate_bpm: int | None = Field(
        default=None,
        ge=100,
        le=230,
        description=(
            "Optionaler, individuell bekannter Maximalpuls in Schlägen "
            "pro Minute. Ist kein Wert angegeben, kann die Anwendung "
            "einen altersabhängigen Schätzwert verwenden."
        ),
        examples=[190],
    )
    resting_heart_rate_bpm: int | None = Field(
        default=None,
        ge=35,
        le=120,
        description=(
            "Optionaler persoenlicher Ruhepuls in Schlaegen pro Minute. "
            "Er wird fuer individualisierte Trainings-Zielpulsbereiche verwendet."
        ),
        examples=[70],
    )
    start_weight_kg: float | None = Field(
        default=None,
        gt=0,
        le=500,
        description=(
            "Startgewicht in Kilogramm. Beim Trainingsziel Abnehmen "
            "ist dieser Wert erforderlich. Das aktuelle Tagesgewicht "
            "wird dagegen im Check-in erfasst."
        ),
        examples=[92.5],
    )
    target_weight_kg: float | None = Field(
        default=None,
        gt=0,
        le=500,
        description=(
            "Zielgewicht in Kilogramm. Beim Trainingsziel Abnehmen "
            "ist dieser Wert erforderlich und muss unter dem "
            "Startgewicht liegen."
        ),
        examples=[82.0],
    )

    @model_validator(mode="after")
    def validate_weight_goal(self) -> "PersonProfileRequest":
        if self.training_goal == TrainingGoal.WEIGHT_LOSS:
            if self.start_weight_kg is None or self.target_weight_kg is None:
                raise ValueError("Für Abnehmen sind Start- und Zielgewicht erforderlich.")
            if self.target_weight_kg >= self.start_weight_kg:
                raise ValueError("Das Zielgewicht muss unter dem Startgewicht liegen.")
        return self


class PersonProfileResponse(PersonProfileRequest):
    """Vollständiges Personenprofil einschließlich der stabilen ID."""

    person_id: int = Field(
        description="Stabile numerische ID der Person.",
        examples=[1],
    )
