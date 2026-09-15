from features.training.domain.weight_goal_progress import WeightGoalStatus
from features.training.service.weight_goal_progress_service import WeightGoalProgressService


def calculate(
    *,
    start_weight_kg: float | None = 100.0,
    current_weight_kg: float | None = 92.4,
    target_weight_kg: float | None = 82.0,
):
    return WeightGoalProgressService().calculate(
        start_weight_kg=start_weight_kg,
        current_weight_kg=current_weight_kg,
        target_weight_kg=target_weight_kg,
    )


def test_calculates_remaining_weight_and_progress_above_target() -> None:
    progress = calculate(
        start_weight_kg=100.0,
        current_weight_kg=92.0,
        target_weight_kg=80.0,
    )

    assert progress.status is WeightGoalStatus.ABOVE_TARGET
    assert progress.remaining_kg == 12.0
    assert progress.lost_since_start_kg == 8.0
    assert progress.progress_percent == 40.0


def test_detects_target_weight_and_caps_progress_at_100_percent() -> None:
    progress = calculate(
        start_weight_kg=100.0,
        current_weight_kg=82.0,
        target_weight_kg=82.0,
    )

    assert progress.status is WeightGoalStatus.AT_TARGET
    assert progress.remaining_kg == 0.0
    assert progress.lost_since_start_kg == 18.0
    assert progress.progress_percent == 100.0


def test_detects_weight_below_target_without_progress_above_100_percent() -> None:
    progress = calculate(
        start_weight_kg=100.0,
        current_weight_kg=81.3,
        target_weight_kg=82.0,
    )

    assert progress.status is WeightGoalStatus.BELOW_TARGET
    assert progress.remaining_kg == -0.7
    assert progress.lost_since_start_kg == 18.7
    assert progress.progress_percent == 100.0


def test_weight_above_start_is_described_but_progress_does_not_become_negative() -> None:
    progress = calculate(
        start_weight_kg=100.0,
        current_weight_kg=102.0,
        target_weight_kg=80.0,
    )

    assert progress.lost_since_start_kg == -2.0
    assert progress.progress_percent == 0.0


def test_missing_start_weight_keeps_goal_distance_but_not_progress() -> None:
    progress = calculate(
        start_weight_kg=None,
        current_weight_kg=92.4,
        target_weight_kg=82.0,
    )

    assert progress.status is WeightGoalStatus.ABOVE_TARGET
    assert progress.remaining_kg == 10.4
    assert progress.lost_since_start_kg is None
    assert progress.progress_percent is None


def test_non_decreasing_goal_does_not_calculate_weight_loss_progress() -> None:
    progress = calculate(
        start_weight_kg=82.0,
        current_weight_kg=84.0,
        target_weight_kg=90.0,
    )

    assert progress.status is WeightGoalStatus.BELOW_TARGET
    assert progress.lost_since_start_kg is None
    assert progress.progress_percent is None


def test_handles_missing_current_weight() -> None:
    progress = calculate(current_weight_kg=None)

    assert progress.status is WeightGoalStatus.NO_CURRENT_WEIGHT
    assert progress.remaining_kg is None
    assert progress.lost_since_start_kg is None
    assert progress.progress_percent is None


def test_handles_missing_goal() -> None:
    progress = calculate(target_weight_kg=None)

    assert progress.status is WeightGoalStatus.NO_GOAL
    assert progress.remaining_kg is None
    assert progress.lost_since_start_kg is None
    assert progress.progress_percent is None
