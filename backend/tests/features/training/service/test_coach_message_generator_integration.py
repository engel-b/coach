from datetime import UTC, datetime

from features.check_in.domain.check_in import CheckIn
from features.person.domain.profile import TrainingGoal
from features.training.domain.coach_message import CoachMessageContext
from features.training.domain.pre_workout import PreWorkoutCoachingContext
from features.training.domain.readiness import (
    DailyActivityStatus,
    ReadinessContext,
    RecentTrainingLoadStatus,
    SleepStatus,
)
from features.training.domain.recommendation_engine import TrainingRecommendationEngine
from features.training.domain.weight_goal_progress import WeightGoalProgress, WeightGoalStatus
from features.training.domain.weight_trend import WeightTrend, WeightTrendDirection
from features.training.service.pre_workout_coaching_planner import PreWorkoutCoachingPlanner


class StubMessageGenerator:
    def __init__(self) -> None:
        self.context: CoachMessageContext | None = None

    def generate(self, *, context: CoachMessageContext) -> str:
        self.context = context
        return "stub-coach-message"


def test_planner_uses_injected_message_generator() -> None:
    generator = StubMessageGenerator()
    planner = PreWorkoutCoachingPlanner(
        TrainingRecommendationEngine(),
        message_generator=generator,
    )
    context = PreWorkoutCoachingContext(
        check_in=CheckIn(
            person_id=1,
            timestamp=datetime(2026, 9, 15, 7, 0, tzinfo=UTC),
            energy=4,
            recovery=4,
            muscle_soreness=1,
            stress=2,
            available_training_minutes=30,
            current_weight_kg=92.0,
        ),
        max_heart_rate=180,
        training_goal=TrainingGoal.WEIGHT_LOSS,
        weight_trend=WeightTrend(
            direction=WeightTrendDirection.DOWN,
            weekly_change_kg=-0.4,
            sample_count=5,
            span_days=28.0,
        ),
        weight_goal_progress=WeightGoalProgress(
            status=WeightGoalStatus.ABOVE_TARGET,
            start_weight_kg=100.0,
            current_weight_kg=92.0,
            target_weight_kg=80.0,
            remaining_kg=12.0,
            lost_since_start_kg=8.0,
            progress_percent=40.0,
        ),
        readiness=ReadinessContext(
            sleep_status=SleepStatus.ADEQUATE,
            daily_activity_status=DailyActivityStatus.NORMAL,
            recent_training_load_status=RecentTrainingLoadStatus.LOW,
            recent_training_minutes=0.0,
            recent_workout_count=0,
            max_duration_minutes=None,
        ),
    )

    recommendation = planner.recommend(context)

    assert recommendation.reason == "stub-coach-message"
    assert generator.context is not None
    assert generator.context.total_duration_minutes == recommendation.total_duration_minutes
    assert generator.context.reason_codes == recommendation.reason_codes
    assert generator.context.weight_goal_progress == recommendation.weight_goal_progress
