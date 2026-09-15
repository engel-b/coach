import json
from io import BytesIO
from typing import Any, Self

import pytest

from adapters.llm import local_llm_coach_message_generator as adapter_module
from adapters.llm.local_llm_coach_message_generator import LocalLlmCoachMessageGenerator
from features.person.domain.profile import TrainingGoal
from features.training.domain.coach_message import CoachMessageContext
from features.training.domain.pre_workout import RecommendationReasonCode
from features.training.domain.recommendation import WorkoutType
from features.training.domain.weight_goal_progress import WeightGoalProgress, WeightGoalStatus
from features.training.domain.weight_trend import WeightTrendDirection


class FakeResponse:
    def __init__(self, payload: dict[str, Any]) -> None:
        self._body = json.dumps(payload).encode("utf-8")

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *args: object) -> None:
        return None

    def read(self) -> bytes:
        return BytesIO(self._body).read()


def context() -> CoachMessageContext:
    return CoachMessageContext(
        workout_type=WorkoutType.BASE_ENDURANCE,
        total_duration_minutes=30,
        reason_codes=(
            RecommendationReasonCode.SHORT_SLEEP,
            RecommendationReasonCode.DURATION_REDUCED_FOR_READINESS,
        ),
        training_goal=TrainingGoal.WEIGHT_LOSS,
        readiness_max_duration_minutes=30,
        weight_trend_direction=WeightTrendDirection.DOWN,
        weight_trend_kg_per_week=-0.3,
        weight_goal_progress=WeightGoalProgress(
            status=WeightGoalStatus.ABOVE_TARGET,
            start_weight_kg=100.0,
            current_weight_kg=92.0,
            target_weight_kg=80.0,
            remaining_kg=12.0,
            lost_since_start_kg=8.0,
            progress_percent=40.0,
        ),
    )


def test_generate_calls_openai_compatible_endpoint(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, object] = {}

    def fake_urlopen(request: object, timeout: float) -> FakeResponse:
        captured["request"] = request
        captured["timeout"] = timeout
        return FakeResponse(
            {"choices": [{"message": {"content": " Heute trainieren wir bewusst etwas kürzer. "}}]}
        )

    monkeypatch.setattr(adapter_module, "urlopen", fake_urlopen)
    generator = LocalLlmCoachMessageGenerator(
        base_url="http://127.0.0.1:8080/",
        model="local-coach",
        timeout_seconds=2.5,
    )

    message = generator.generate(context=context())

    assert message == "Heute trainieren wir bewusst etwas kürzer."
    assert captured["timeout"] == 2.5

    request = captured["request"]
    assert request.full_url == "http://127.0.0.1:8080/v1/chat/completions"
    body = json.loads(request.data.decode("utf-8"))
    assert body["model"] == "local-coach"
    assert body["messages"][1]["content"].find('"total_duration_minutes":30') >= 0
    assert body["messages"][1]["content"].find('"progress_percent":40.0') >= 0


def test_invalid_response_is_raised_for_fallback(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_urlopen(request: object, timeout: float) -> FakeResponse:
        return FakeResponse({"choices": []})

    monkeypatch.setattr(adapter_module, "urlopen", fake_urlopen)
    generator = LocalLlmCoachMessageGenerator(
        base_url="http://127.0.0.1:8080",
        model="local-coach",
    )

    with pytest.raises(TypeError, match="contains no choices"):
        generator.generate(context=context())


def test_configuration_is_validated() -> None:
    with pytest.raises(ValueError, match="base_url"):
        LocalLlmCoachMessageGenerator(base_url=" ", model="local-coach")
    with pytest.raises(ValueError, match="model"):
        LocalLlmCoachMessageGenerator(base_url="http://localhost:8080", model=" ")
    with pytest.raises(ValueError, match="timeout_seconds"):
        LocalLlmCoachMessageGenerator(
            base_url="http://localhost:8080",
            model="local-coach",
            timeout_seconds=0,
        )
