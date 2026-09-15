from dataclasses import dataclass

from features.person.domain.profile import TrainingGoal
from features.training.domain.pre_workout import RecommendationReasonCode
from features.training.domain.recommendation import WorkoutType
from features.training.domain.weight_goal_progress import WeightGoalProgress
from features.training.domain.weight_trend import WeightTrendDirection


@dataclass(frozen=True)
class CoachMessageContext:
    """
    Formulierungs-Kontext für den Pre-Workout-Coach.

    Enthält nur bereits deterministisch abgeleitete Fakten. Der Context darf
    von Text-Templates oder später einem lokalen LLM verwendet werden, ohne
    dass die Formulierungsschicht Trainingsentscheidungen selbst treffen muss.
    """

    workout_type: WorkoutType
    total_duration_minutes: int
    reason_codes: tuple[RecommendationReasonCode, ...]
    training_goal: TrainingGoal
    readiness_max_duration_minutes: int | None
    weight_trend_direction: WeightTrendDirection
    weight_trend_kg_per_week: float | None
    weight_goal_progress: WeightGoalProgress | None
