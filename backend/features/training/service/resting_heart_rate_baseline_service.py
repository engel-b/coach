from dataclasses import dataclass
from datetime import datetime, timedelta
from statistics import median

from features.check_in.domain.check_in import CheckIn
from features.training.domain.heart_rate_target import HeartRateTargetSource


@dataclass(frozen=True)
class RestingHeartRateBaselineRules:
    minimum_samples: int = 3
    lookback_days: int = 30
    max_samples: int = 14


@dataclass(frozen=True)
class RestingHeartRateBaseline:
    value_bpm: int | None
    source: HeartRateTargetSource | None
    sample_count: int = 0


class RestingHeartRateBaselineService:
    """Ermittelt einen robusten Ruhepuls-Referenzwert fuer die Zielzonen.

    Mehrere explizit im Check-in erfasste Ruhepulswerte haben Vorrang vor dem
    statischen Profilwert. Der Median reduziert den Einfluss einzelner
    Ausreisser. Solange nicht genuegend aktuelle Messungen vorliegen, bleibt
    der Profilwert der Fallback.
    """

    def __init__(self, rules: RestingHeartRateBaselineRules | None = None) -> None:
        self._rules = rules or RestingHeartRateBaselineRules()

    def calculate(
        self,
        *,
        check_ins: list[CheckIn],
        as_of: datetime,
        profile_resting_heart_rate_bpm: int | None,
    ) -> RestingHeartRateBaseline:
        cutoff = as_of - timedelta(days=self._rules.lookback_days)
        values = [
            check_in.resting_heart_rate_bpm
            for check_in in check_ins
            if check_in.timestamp >= cutoff and check_in.resting_heart_rate_bpm is not None
        ][: self._rules.max_samples]

        if len(values) >= self._rules.minimum_samples:
            return RestingHeartRateBaseline(
                value_bpm=round(median(values)),
                source=HeartRateTargetSource.CHECK_IN_BASELINE,
                sample_count=len(values),
            )

        if profile_resting_heart_rate_bpm is not None:
            return RestingHeartRateBaseline(
                value_bpm=profile_resting_heart_rate_bpm,
                source=HeartRateTargetSource.PROFILE,
            )

        return RestingHeartRateBaseline(value_bpm=None, source=None)
