from features.training.domain.coach_message import CoachMessageContext
from features.training.domain.coach_message_generator import CoachMessageGenerator


class StubCoachMessageGenerator:
    def generate(self, *, context: CoachMessageContext) -> str:
        return f"{context.workout_type.value}:{context.total_duration_minutes}"


def accepts_generator(generator: CoachMessageGenerator) -> CoachMessageGenerator:
    return generator


def test_structural_port_accepts_generator_implementation() -> None:
    generator = StubCoachMessageGenerator()

    assert accepts_generator(generator) is generator
