from features.training.domain.weight_goal_progress import (
    WeightGoalProgress,
    WeightGoalStatus,
)


class WeightGoalProgressService:
    """Berechnet den deskriptiven Fortschritt zum persönlichen Zielgewicht."""

    def calculate(
        self,
        *,
        start_weight_kg: float | None,
        current_weight_kg: float | None,
        target_weight_kg: float | None,
    ) -> WeightGoalProgress:
        if target_weight_kg is None:
            return WeightGoalProgress(
                status=WeightGoalStatus.NO_GOAL,
                start_weight_kg=start_weight_kg,
                current_weight_kg=current_weight_kg,
                target_weight_kg=None,
                remaining_kg=None,
                lost_since_start_kg=None,
                progress_percent=None,
            )

        if current_weight_kg is None:
            return WeightGoalProgress(
                status=WeightGoalStatus.NO_CURRENT_WEIGHT,
                start_weight_kg=start_weight_kg,
                current_weight_kg=None,
                target_weight_kg=target_weight_kg,
                remaining_kg=None,
                lost_since_start_kg=None,
                progress_percent=None,
            )

        remaining_kg = round(current_weight_kg - target_weight_kg, 1)
        if remaining_kg > 0:
            status = WeightGoalStatus.ABOVE_TARGET
        elif remaining_kg < 0:
            status = WeightGoalStatus.BELOW_TARGET
        else:
            status = WeightGoalStatus.AT_TARGET

        lost_since_start_kg: float | None = None
        progress_percent: float | None = None
        if start_weight_kg is not None and start_weight_kg > target_weight_kg:
            planned_loss_kg = start_weight_kg - target_weight_kg
            lost_since_start_kg = round(start_weight_kg - current_weight_kg, 1)
            raw_progress_percent = (start_weight_kg - current_weight_kg) / planned_loss_kg * 100.0
            progress_percent = round(
                min(100.0, max(0.0, raw_progress_percent)),
                1,
            )

        return WeightGoalProgress(
            status=status,
            start_weight_kg=start_weight_kg,
            current_weight_kg=current_weight_kg,
            target_weight_kg=target_weight_kg,
            remaining_kg=remaining_kg,
            lost_since_start_kg=lost_since_start_kg,
            progress_percent=progress_percent,
        )
