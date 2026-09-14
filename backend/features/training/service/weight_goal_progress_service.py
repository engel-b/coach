from features.training.domain.weight_goal_progress import (
    WeightGoalProgress,
    WeightGoalStatus,
)


class WeightGoalProgressService:
    """Berechnet den rein deskriptiven Abstand zum persönlichen Zielgewicht."""

    def calculate(
        self,
        *,
        current_weight_kg: float | None,
        target_weight_kg: float | None,
    ) -> WeightGoalProgress:
        if target_weight_kg is None:
            return WeightGoalProgress(
                status=WeightGoalStatus.NO_GOAL,
                current_weight_kg=current_weight_kg,
                target_weight_kg=None,
                remaining_kg=None,
            )

        if current_weight_kg is None:
            return WeightGoalProgress(
                status=WeightGoalStatus.NO_CURRENT_WEIGHT,
                current_weight_kg=None,
                target_weight_kg=target_weight_kg,
                remaining_kg=None,
            )

        remaining_kg = round(current_weight_kg - target_weight_kg, 1)
        if remaining_kg > 0:
            status = WeightGoalStatus.ABOVE_TARGET
        elif remaining_kg < 0:
            status = WeightGoalStatus.BELOW_TARGET
        else:
            status = WeightGoalStatus.AT_TARGET

        return WeightGoalProgress(
            status=status,
            current_weight_kg=current_weight_kg,
            target_weight_kg=target_weight_kg,
            remaining_kg=remaining_kg,
        )
