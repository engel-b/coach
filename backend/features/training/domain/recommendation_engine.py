from features.check_in.domain.check_in import CheckIn
from features.training.domain.recommendation import (
    TrainingRecommendation,
    WorkoutPhase,
    WorkoutPhaseType,
    WorkoutType,
)


class TrainingRecommendationEngine:
    """
    Erste regelbasierte Version unseres Coaches.

    Die Regeln sind bewusst einfach und nachvollziehbar.
    Sie können später schrittweise erweitert werden.

    Wichtig:
    Die Engine erzeugt strukturierte Trainingsentscheidungen.
    Eine spätere KI-/Coach-Schicht kann diese Entscheidungen
    erklären und persönlicher formulieren.
    """

    def recommend(
        self,
        *,
        check_in: CheckIn,
        max_heart_rate: int,
    ) -> TrainingRecommendation:
        if self._needs_recovery(check_in):
            return self._create_recovery(
                check_in,
                max_heart_rate,
            )

        return self._create_base_endurance(
            check_in,
            max_heart_rate,
        )

    @staticmethod
    def _needs_recovery(
        check_in: CheckIn,
    ) -> bool:
        return (
            check_in.energy <= 2
            or check_in.recovery <= 2
            or check_in.muscle_soreness >= 4
            or check_in.stress >= 4
        )

    def _create_recovery(
        self,
        check_in: CheckIn,
        max_heart_rate: int,
    ) -> TrainingRecommendation:
        duration = min(
            check_in.available_training_minutes,
            30,
        )

        minimum = round(max_heart_rate * 0.50)
        maximum = round(max_heart_rate * 0.60)

        return TrainingRecommendation(
            workout_type=WorkoutType.RECOVERY,
            total_duration_minutes=duration,
            reason=("Dein heutiger Check-in spricht für eine eher regenerative Einheit."),
            phases=(
                WorkoutPhase(
                    phase_type=WorkoutPhaseType.MAIN,
                    duration_minutes=duration,
                    target_heart_rate_min=minimum,
                    target_heart_rate_max=maximum,
                ),
            ),
        )

    def _create_base_endurance(
        self,
        check_in: CheckIn,
        max_heart_rate: int,
    ) -> TrainingRecommendation:
        total = check_in.available_training_minutes

        warm_up = min(5, total)
        cool_down = min(5, max(0, total - warm_up))
        main = max(0, total - warm_up - cool_down)

        phases: list[WorkoutPhase] = []

        if warm_up > 0:
            phases.append(
                WorkoutPhase(
                    phase_type=WorkoutPhaseType.WARM_UP,
                    duration_minutes=warm_up,
                    target_heart_rate_min=round(max_heart_rate * 0.50),
                    target_heart_rate_max=round(max_heart_rate * 0.60),
                )
            )

        if main > 0:
            phases.append(
                WorkoutPhase(
                    phase_type=WorkoutPhaseType.MAIN,
                    duration_minutes=main,
                    target_heart_rate_min=round(max_heart_rate * 0.60),
                    target_heart_rate_max=round(max_heart_rate * 0.70),
                )
            )

        if cool_down > 0:
            phases.append(
                WorkoutPhase(
                    phase_type=WorkoutPhaseType.COOL_DOWN,
                    duration_minutes=cool_down,
                    target_heart_rate_min=round(max_heart_rate * 0.50),
                    target_heart_rate_max=round(max_heart_rate * 0.60),
                )
            )

        return TrainingRecommendation(
            workout_type=WorkoutType.BASE_ENDURANCE,
            total_duration_minutes=total,
            reason=("Dein Check-in spricht für eine lockere Grundlagen-Ausdauereinheit."),
            phases=tuple(phases),
        )
