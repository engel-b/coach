from dataclasses import dataclass

from features.training.domain.load_response import LoadResponseStatus
from features.training.domain.recommendation import WorkoutType
from features.workout.domain.bike_summary import WorkoutBikeSummary
from features.workout.domain.heart_rate_summary import WorkoutHeartRateSummary


@dataclass(frozen=True)
class WorkoutExpectation:
    """At workout start, freeze the historical baseline (never use later workouts)."""

    workout_type: WorkoutType
    historical_response: LoadResponseStatus
    comparable_workout_count: int
    median_target_position_percent: int | None
    median_power_w: int | None


@dataclass(frozen=True)
class AdaptiveEvaluation:
    heart_rate_response: str
    power_response: str
    expectation_match: str
    observed_response: str


def evaluate_workout(
    expectation: WorkoutExpectation | None,
    heart_rate: WorkoutHeartRateSummary | None,
    bike: WorkoutBikeSummary | None,
) -> AdaptiveEvaluation | None:
    if expectation is None:
        return None

    power = "insufficient_data"
    if (
        bike is not None
        and bike.power_sample_count >= 30
        and bike.average_power_w is not None
        and expectation.median_power_w is not None
        and expectation.median_power_w > 0
    ):
        change = (bike.average_power_w - expectation.median_power_w) / expectation.median_power_w
        power = "similar" if abs(change) <= 0.10 else ("higher" if change > 0 else "lower")

    hr = "insufficient_data"
    if (
        heart_rate is not None
        and heart_rate.sample_count >= 30
        and expectation.comparable_workout_count >= 3
        and expectation.median_target_position_percent is not None
    ):
        position = heart_rate.above_target_percent - heart_rate.below_target_percent
        delta = position - expectation.median_target_position_percent
        hr = "higher" if delta >= 15 else ("lower" if delta <= -15 else "similar")

    observed = "insufficient_data"
    if power == "similar" and hr != "insufficient_data":
        observed = {
            "higher": "higher_hr_at_similar_load",
            "lower": "lower_hr_at_similar_load",
            "similar": "stable",
        }[hr]
    elif power in ("higher", "lower"):
        observed = "load_changed"

    expected = expectation.historical_response.value
    match = "insufficient_data"
    if observed not in ("insufficient_data", "load_changed") and expected in (
        "stable",
        "higher_hr_at_similar_load",
        "lower_hr_at_similar_load",
    ):
        match = "matched" if observed == expected else "different"
    elif observed == "load_changed":
        match = "not_comparable"

    return AdaptiveEvaluation(hr, power, match, observed)
