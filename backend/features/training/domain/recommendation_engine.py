from features.check_in.domain.check_in import CheckIn
from features.training.domain.heart_rate_target import HeartRateTargetSource
from features.training.domain.heart_rate_target_policy import HeartRateTargetPolicy
from features.training.domain.recommendation import (
    HeartRateTargetBasis,
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

    def __init__(self, heart_rate_target_policy: HeartRateTargetPolicy | None = None) -> None:
        self._heart_rate_target_policy = heart_rate_target_policy or HeartRateTargetPolicy()

    def recommend(
        self,
        *,
        check_in: CheckIn,
        max_heart_rate: int,
        resting_heart_rate: int | None = None,
        resting_heart_rate_source: HeartRateTargetSource | None = None,
        resting_heart_rate_sample_count: int = 0,
    ) -> TrainingRecommendation:
        target_basis = self._heart_rate_target_policy.describe_basis(
            max_heart_rate_bpm=max_heart_rate,
            resting_heart_rate_bpm=resting_heart_rate,
            resting_heart_rate_source=resting_heart_rate_source,
            resting_heart_rate_sample_count=resting_heart_rate_sample_count,
        )

        if self._needs_recovery(check_in):
            return self._create_recovery(
                check_in,
                max_heart_rate,
                resting_heart_rate,
                target_basis,
            )

        return self._create_base_endurance(
            check_in,
            max_heart_rate,
            resting_heart_rate,
            target_basis,
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
        resting_heart_rate: int | None,
        target_basis: HeartRateTargetBasis,
    ) -> TrainingRecommendation:
        duration = min(
            check_in.available_training_minutes,
            30,
        )

        target = self._heart_rate_target_policy.calculate(
            workout_type=WorkoutType.RECOVERY,
            phase_type=WorkoutPhaseType.MAIN,
            max_heart_rate_bpm=max_heart_rate,
            resting_heart_rate_bpm=resting_heart_rate,
        )

        return TrainingRecommendation(
            workout_type=WorkoutType.RECOVERY,
            total_duration_minutes=duration,
            reason=("Dein heutiger Check-in spricht für eine eher regenerative Einheit."),
            heart_rate_target_basis=target_basis,
            phases=(
                WorkoutPhase(
                    phase_type=WorkoutPhaseType.MAIN,
                    duration_minutes=duration,
                    target_heart_rate_min=target.minimum_bpm,
                    target_heart_rate_max=target.maximum_bpm,
                ),
            ),
        )

    def _create_base_endurance(
        self,
        check_in: CheckIn,
        max_heart_rate: int,
        resting_heart_rate: int | None,
        target_basis: HeartRateTargetBasis,
    ) -> TrainingRecommendation:
        total = check_in.available_training_minutes

        warm_up = min(5, total)
        cool_down = min(5, max(0, total - warm_up))
        main = max(0, total - warm_up - cool_down)

        phases: list[WorkoutPhase] = []

        if warm_up > 0:
            target = self._heart_rate_target_policy.calculate(
                workout_type=WorkoutType.BASE_ENDURANCE,
                phase_type=WorkoutPhaseType.WARM_UP,
                max_heart_rate_bpm=max_heart_rate,
                resting_heart_rate_bpm=resting_heart_rate,
            )
            phases.append(
                WorkoutPhase(
                    phase_type=WorkoutPhaseType.WARM_UP,
                    duration_minutes=warm_up,
                    target_heart_rate_min=target.minimum_bpm,
                    target_heart_rate_max=target.maximum_bpm,
                )
            )

        if main > 0:
            target = self._heart_rate_target_policy.calculate(
                workout_type=WorkoutType.BASE_ENDURANCE,
                phase_type=WorkoutPhaseType.MAIN,
                max_heart_rate_bpm=max_heart_rate,
                resting_heart_rate_bpm=resting_heart_rate,
            )
            phases.append(
                WorkoutPhase(
                    phase_type=WorkoutPhaseType.MAIN,
                    duration_minutes=main,
                    target_heart_rate_min=target.minimum_bpm,
                    target_heart_rate_max=target.maximum_bpm,
                )
            )

        if cool_down > 0:
            target = self._heart_rate_target_policy.calculate(
                workout_type=WorkoutType.BASE_ENDURANCE,
                phase_type=WorkoutPhaseType.COOL_DOWN,
                max_heart_rate_bpm=max_heart_rate,
                resting_heart_rate_bpm=resting_heart_rate,
            )
            phases.append(
                WorkoutPhase(
                    phase_type=WorkoutPhaseType.COOL_DOWN,
                    duration_minutes=cool_down,
                    target_heart_rate_min=target.minimum_bpm,
                    target_heart_rate_max=target.maximum_bpm,
                )
            )

        return TrainingRecommendation(
            workout_type=WorkoutType.BASE_ENDURANCE,
            total_duration_minutes=total,
            reason=("Dein Check-in spricht für eine lockere Grundlagen-Ausdauereinheit."),
            heart_rate_target_basis=target_basis,
            phases=tuple(phases),
        )
