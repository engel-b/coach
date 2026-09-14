from datetime import timedelta

from features.check_in.domain.check_in import CheckIn
from features.training.domain.readiness import (
    DailyActivityStatus,
    ReadinessContext,
    ReadinessRules,
    RecentTrainingLoadStatus,
    RecentTrainingSession,
    SleepStatus,
)


class ReadinessService:
    """
    Normalisiert Schlaf, Tagesaktivität und jüngste Trainingsbelastung.

    Die Schwellwerte kommen aus ReadinessRules. Sie sind explizite,
    konservative Produktregeln und keine medizinischen Grenzwerte.
    Belastende Signale dürfen die heutige Dauer reduzieren;
    fehlende/geringe Aktivität führt nie automatisch zu höherer Belastung.
    """

    def __init__(self, *, rules: ReadinessRules | None = None) -> None:
        self._rules = rules or ReadinessRules()

    def assess(
        self,
        *,
        check_in: CheckIn,
        recent_sessions: list[RecentTrainingSession],
    ) -> ReadinessContext:
        sleep_status = self._sleep_status(check_in.sleep_hours)
        daily_activity_status = self._daily_activity_status(check_in.steps)

        window_start = check_in.timestamp - timedelta(
            days=self._rules.recent_training_window_days,
        )
        sessions_in_window = [
            session
            for session in recent_sessions
            if window_start <= session.started_at < check_in.timestamp
            and session.active_minutes > 0
        ]
        recent_training_minutes = sum(session.active_minutes for session in sessions_in_window)
        recent_workout_count = len(sessions_in_window)
        training_load_status = self._training_load_status(
            active_minutes=recent_training_minutes,
            workout_count=recent_workout_count,
        )

        has_caution_signal = (
            sleep_status is SleepStatus.SHORT
            or daily_activity_status is DailyActivityStatus.HIGH
            or training_load_status is RecentTrainingLoadStatus.HIGH
        )

        return ReadinessContext(
            sleep_status=sleep_status,
            daily_activity_status=daily_activity_status,
            recent_training_load_status=training_load_status,
            recent_training_minutes=round(recent_training_minutes, 1),
            recent_workout_count=recent_workout_count,
            max_duration_minutes=(
                self._rules.caution_duration_cap_minutes if has_caution_signal else None
            ),
        )

    def _sleep_status(self, sleep_hours: float | None) -> SleepStatus:
        if sleep_hours is None:
            return SleepStatus.UNKNOWN
        if sleep_hours < self._rules.short_sleep_hours:
            return SleepStatus.SHORT
        return SleepStatus.ADEQUATE

    def _daily_activity_status(self, steps: int | None) -> DailyActivityStatus:
        if steps is None:
            return DailyActivityStatus.UNKNOWN
        if steps >= self._rules.high_daily_steps:
            return DailyActivityStatus.HIGH
        return DailyActivityStatus.NORMAL

    def _training_load_status(
        self,
        *,
        active_minutes: float,
        workout_count: int,
    ) -> RecentTrainingLoadStatus:
        if (
            active_minutes >= self._rules.high_recent_training_minutes
            or workout_count >= self._rules.high_recent_workout_count
        ):
            return RecentTrainingLoadStatus.HIGH
        if active_minutes > 0:
            return RecentTrainingLoadStatus.MODERATE
        return RecentTrainingLoadStatus.LOW
