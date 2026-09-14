from features.training.domain.weight_goal_progress import WeightGoalStatus
from features.training.service.weight_goal_progress_service import WeightGoalProgressService


def test_calculates_remaining_weight_above_target() -> None:
    progress = WeightGoalProgressService().calculate(
        current_weight_kg=92.4,
        target_weight_kg=82.0,
    )

    assert progress.status is WeightGoalStatus.ABOVE_TARGET
    assert progress.remaining_kg == 10.4


def test_detects_target_weight() -> None:
    progress = WeightGoalProgressService().calculate(
        current_weight_kg=82.0,
        target_weight_kg=82.0,
    )

    assert progress.status is WeightGoalStatus.AT_TARGET
    assert progress.remaining_kg == 0.0


def test_detects_weight_below_target_without_judgement() -> None:
    progress = WeightGoalProgressService().calculate(
        current_weight_kg=81.3,
        target_weight_kg=82.0,
    )

    assert progress.status is WeightGoalStatus.BELOW_TARGET
    assert progress.remaining_kg == -0.7


def test_handles_missing_current_weight() -> None:
    progress = WeightGoalProgressService().calculate(
        current_weight_kg=None,
        target_weight_kg=82.0,
    )

    assert progress.status is WeightGoalStatus.NO_CURRENT_WEIGHT
    assert progress.remaining_kg is None


def test_handles_missing_goal() -> None:
    progress = WeightGoalProgressService().calculate(
        current_weight_kg=92.4,
        target_weight_kg=None,
    )

    assert progress.status is WeightGoalStatus.NO_GOAL
    assert progress.remaining_kg is None
