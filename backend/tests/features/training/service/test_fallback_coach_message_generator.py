from features.person.domain.profile import TrainingGoal
from features.training.domain.coach_message import CoachMessageContext
from features.training.domain.pre_workout import RecommendationReasonCode
from features.training.domain.recommendation import WorkoutType
from features.training.domain.weight_trend import WeightTrendDirection
from features.training.service.fallback_coach_message_generator import (
    FallbackCoachMessageGenerator,
)


class StubGenerator:
    def __init__(self, message: str) -> None:
        self.message = message
        self.calls = 0

    def generate(self, *, context: CoachMessageContext) -> str:
        self.calls = 1
        return self.message


class FailingGenerator:
    def __init__(self) -> None:
        self.calls = 0

    def generate(self, *, context: CoachMessageContext) -> str:
        self.calls = 1
        raise RuntimeError("local llm unavailable")


def coach_context() -> CoachMessageContext:
    return CoachMessageContext(
        workout_type=WorkoutType.BASE_ENDURANCE,
        total_duration_minutes=30,
        reason_codes=(RecommendationReasonCode.READINESS_GOOD,),
        training_goal=TrainingGoal.WEIGHT_LOSS,
        readiness_max_duration_minutes=None,
        weight_trend_direction=WeightTrendDirection.UNKNOWN,
        weight_trend_kg_per_week=None,
        weight_goal_progress=None,
    )


def test_primary_message_is_used_without_calling_fallback() -> None:
    primary = StubGenerator("Dynamische Coach-Nachricht")
    fallback = StubGenerator("Deterministischer Fallback")
    generator = FallbackCoachMessageGenerator(primary=primary, fallback=fallback)

    message = generator.generate(context=coach_context())

    assert message == "Dynamische Coach-Nachricht"
    assert primary.calls == 1
    assert fallback.calls == 0


def test_exception_uses_fallback_message() -> None:
    primary = FailingGenerator()
    fallback = StubGenerator("Deterministischer Fallback")
    generator = FallbackCoachMessageGenerator(primary=primary, fallback=fallback)

    message = generator.generate(context=coach_context())

    assert message == "Deterministischer Fallback"
    assert primary.calls == 1
    assert fallback.calls == 1


def test_empty_primary_message_uses_fallback_message() -> None:
    primary = StubGenerator("   ")
    fallback = StubGenerator("Deterministischer Fallback")
    generator = FallbackCoachMessageGenerator(primary=primary, fallback=fallback)

    message = generator.generate(context=coach_context())

    assert message == "Deterministischer Fallback"
    assert primary.calls == 1
    assert fallback.calls == 1
