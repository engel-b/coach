from dataclasses import dataclass
from typing import ClassVar

from features.training.domain.heart_rate_target import HeartRateTargetSource
from features.training.domain.recommendation import (
    HeartRateTargetBasis,
    HeartRateTargetMethod,
    WorkoutPhaseType,
    WorkoutType,
)


@dataclass(frozen=True)
class HeartRateTargetRange:
    minimum_bpm: int
    maximum_bpm: int


class HeartRateTargetPolicy:
    """
    Berechnet personalisierte Trainings-Zielbereiche.

    Ist ein Ruhepuls bekannt, wird die Herzfrequenzreserve verwendet.
    Ein auffaellig hoher oder niedriger Ruhepuls wird fuer die Berechnung
    konservativ auf einen Referenzbereich begrenzt. Dadurch kann ein hoher
    Ruhepuls die Trainingszone individualisieren, aber nicht unbegrenzt nach
    oben verschieben.

    Fehlt der Ruhepuls, bleibt das bisherige Prozent-von-HFmax-Verfahren als
    kompatibler Fallback erhalten.
    """

    MIN_REFERENCE_RESTING_HEART_RATE_BPM = 40
    MAX_REFERENCE_RESTING_HEART_RATE_BPM = 90

    _HRR_INTENSITIES: ClassVar[dict[tuple[WorkoutType, WorkoutPhaseType], tuple[float, float]]] = {
        (WorkoutType.RECOVERY, WorkoutPhaseType.MAIN): (0.30, 0.40),
        (WorkoutType.BASE_ENDURANCE, WorkoutPhaseType.WARM_UP): (0.30, 0.40),
        (WorkoutType.BASE_ENDURANCE, WorkoutPhaseType.MAIN): (0.40, 0.55),
        (WorkoutType.BASE_ENDURANCE, WorkoutPhaseType.COOL_DOWN): (0.30, 0.40),
        (WorkoutType.MODERATE, WorkoutPhaseType.WARM_UP): (0.30, 0.40),
        (WorkoutType.MODERATE, WorkoutPhaseType.MAIN): (0.45, 0.60),
        (WorkoutType.MODERATE, WorkoutPhaseType.COOL_DOWN): (0.30, 0.40),
    }

    _MAX_HR_FALLBACK_INTENSITIES: ClassVar[
        dict[tuple[WorkoutType, WorkoutPhaseType], tuple[float, float]]
    ] = {
        (WorkoutType.RECOVERY, WorkoutPhaseType.MAIN): (0.50, 0.60),
        (WorkoutType.BASE_ENDURANCE, WorkoutPhaseType.WARM_UP): (0.50, 0.60),
        (WorkoutType.BASE_ENDURANCE, WorkoutPhaseType.MAIN): (0.60, 0.70),
        (WorkoutType.BASE_ENDURANCE, WorkoutPhaseType.COOL_DOWN): (0.50, 0.60),
        (WorkoutType.MODERATE, WorkoutPhaseType.WARM_UP): (0.50, 0.60),
        (WorkoutType.MODERATE, WorkoutPhaseType.MAIN): (0.65, 0.75),
        (WorkoutType.MODERATE, WorkoutPhaseType.COOL_DOWN): (0.50, 0.60),
    }

    def describe_basis(
        self,
        *,
        max_heart_rate_bpm: int,
        resting_heart_rate_bpm: int | None,
        resting_heart_rate_source: HeartRateTargetSource | None = None,
        resting_heart_rate_sample_count: int = 0,
    ) -> HeartRateTargetBasis:
        if max_heart_rate_bpm <= 0:
            raise ValueError("max_heart_rate_bpm must be positive")

        if resting_heart_rate_bpm is None:
            return HeartRateTargetBasis(
                method=HeartRateTargetMethod.MAX_HEART_RATE_PERCENTAGE,
                max_heart_rate_bpm=max_heart_rate_bpm,
                resting_heart_rate_bpm=None,
                reference_resting_heart_rate_bpm=None,
                resting_heart_rate_source=None,
                resting_heart_rate_sample_count=0,
            )

        if resting_heart_rate_bpm <= 0:
            raise ValueError("resting_heart_rate_bpm must be positive")

        reference_resting = min(
            self.MAX_REFERENCE_RESTING_HEART_RATE_BPM,
            max(self.MIN_REFERENCE_RESTING_HEART_RATE_BPM, resting_heart_rate_bpm),
        )
        if max_heart_rate_bpm <= reference_resting:
            raise ValueError("max_heart_rate_bpm must exceed resting heart rate reference")

        return HeartRateTargetBasis(
            method=HeartRateTargetMethod.HEART_RATE_RESERVE,
            max_heart_rate_bpm=max_heart_rate_bpm,
            resting_heart_rate_bpm=resting_heart_rate_bpm,
            reference_resting_heart_rate_bpm=reference_resting,
            resting_heart_rate_source=resting_heart_rate_source,
            resting_heart_rate_sample_count=resting_heart_rate_sample_count,
        )

    def calculate(
        self,
        *,
        workout_type: WorkoutType,
        phase_type: WorkoutPhaseType,
        max_heart_rate_bpm: int,
        resting_heart_rate_bpm: int | None,
    ) -> HeartRateTargetRange:
        key = (workout_type, phase_type)
        basis = self.describe_basis(
            max_heart_rate_bpm=max_heart_rate_bpm,
            resting_heart_rate_bpm=resting_heart_rate_bpm,
        )

        if basis.method is HeartRateTargetMethod.MAX_HEART_RATE_PERCENTAGE:
            minimum_factor, maximum_factor = self._MAX_HR_FALLBACK_INTENSITIES[key]
            return HeartRateTargetRange(
                minimum_bpm=round(max_heart_rate_bpm * minimum_factor),
                maximum_bpm=round(max_heart_rate_bpm * maximum_factor),
            )

        reference_resting = basis.reference_resting_heart_rate_bpm
        if reference_resting is None:
            raise RuntimeError("heart-rate-reserve basis requires a resting-heart-rate reference")

        reserve = max_heart_rate_bpm - reference_resting
        minimum_factor, maximum_factor = self._HRR_INTENSITIES[key]
        return HeartRateTargetRange(
            minimum_bpm=round(reference_resting + reserve * minimum_factor),
            maximum_bpm=round(reference_resting + reserve * maximum_factor),
        )
