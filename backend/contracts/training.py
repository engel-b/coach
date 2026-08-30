from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


class WorkoutPhaseResponse(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

    phase_type: str
    duration_minutes: int
    target_heart_rate_min: int
    target_heart_rate_max: int


class TrainingRecommendationResponse(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

    workout_type: str
    total_duration_minutes: int
    reason: str
    phases: list[WorkoutPhaseResponse]
