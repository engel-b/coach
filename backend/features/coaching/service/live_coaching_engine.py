from features.coaching.domain.live_coaching import (
    CoachingAction,
    HeartRateDeviationSeverity,
    HeartRateZoneStatus,
    LiveCoachingContext,
    LiveCoachingDecision,
    LiveCoachingRules,
)


class InvalidLiveCoachingContextError(ValueError):
    """Die Eingabedaten für eine Coaching-Entscheidung sind ungültig."""


class LiveCoachingEngine:
    """
    Reine fachliche Entscheidungslogik für den Live Coach.

    Die Engine kennt weder FastAPI noch Bluetooth, WebSockets, React oder TTS.
    Sie bewertet ausschließlich einen bereits aufbereiteten Coaching-Kontext.
    """

    def __init__(self, rules: LiveCoachingRules | None = None) -> None:
        self._rules = rules or LiveCoachingRules()

    @property
    def target_tolerance_bpm(self) -> int:
        return self._rules.target_tolerance_bpm

    def evaluate(self, context: LiveCoachingContext) -> LiveCoachingDecision:
        self._validate(context)

        zone_status = self._zone_status(context)
        deviation_bpm = self._deviation_bpm(context, zone_status)
        severity = self._deviation_severity(zone_status, deviation_bpm)

        if zone_status == HeartRateZoneStatus.IN_TARGET:
            return self._decision(
                context=context,
                zone_status=zone_status,
                action=CoachingAction.NONE,
                deviation_bpm=0,
                deviation_severity=HeartRateDeviationSeverity.NONE,
                reason="heart_rate_in_target",
            )

        required_seconds = (
            self._rules.large_deviation_seconds_before_action
            if severity is HeartRateDeviationSeverity.LARGE
            else self._rules.deviation_seconds_before_action
        )
        if context.outside_target_seconds < required_seconds:
            return self._decision(
                context=context,
                zone_status=zone_status,
                action=CoachingAction.NONE,
                deviation_bpm=deviation_bpm,
                deviation_severity=severity,
                reason=(
                    "large_deviation_too_short"
                    if severity is HeartRateDeviationSeverity.LARGE
                    else "deviation_too_short"
                ),
            )

        if zone_status == HeartRateZoneStatus.BELOW_TARGET:
            return self._decision(
                context=context,
                zone_status=zone_status,
                action=CoachingAction.INCREASE_INTENSITY,
                deviation_bpm=deviation_bpm,
                deviation_severity=severity,
                reason=(
                    "heart_rate_far_below_target"
                    if severity is HeartRateDeviationSeverity.LARGE
                    else "heart_rate_below_target_long_enough"
                ),
            )

        return self._decision(
            context=context,
            zone_status=zone_status,
            action=CoachingAction.REDUCE_INTENSITY,
            deviation_bpm=deviation_bpm,
            deviation_severity=severity,
            reason=(
                "heart_rate_far_above_target"
                if severity is HeartRateDeviationSeverity.LARGE
                else "heart_rate_above_target_long_enough"
            ),
        )

    def _zone_status(self, context: LiveCoachingContext) -> HeartRateZoneStatus:
        if context.heart_rate_bpm < context.target_min_bpm - self._rules.target_tolerance_bpm:
            return HeartRateZoneStatus.BELOW_TARGET

        if context.heart_rate_bpm > context.target_max_bpm + self._rules.target_tolerance_bpm:
            return HeartRateZoneStatus.ABOVE_TARGET

        return HeartRateZoneStatus.IN_TARGET

    def _deviation_severity(
        self,
        zone_status: HeartRateZoneStatus,
        deviation_bpm: int,
    ) -> HeartRateDeviationSeverity:
        if zone_status is HeartRateZoneStatus.IN_TARGET:
            return HeartRateDeviationSeverity.NONE
        if deviation_bpm >= self._rules.large_deviation_bpm:
            return HeartRateDeviationSeverity.LARGE
        return HeartRateDeviationSeverity.MODERATE

    @staticmethod
    def _deviation_bpm(
        context: LiveCoachingContext,
        zone_status: HeartRateZoneStatus,
    ) -> int:
        if zone_status is HeartRateZoneStatus.BELOW_TARGET:
            return max(0, context.target_min_bpm - context.heart_rate_bpm)
        if zone_status is HeartRateZoneStatus.ABOVE_TARGET:
            return max(0, context.heart_rate_bpm - context.target_max_bpm)
        return 0

    @staticmethod
    def _decision(
        *,
        context: LiveCoachingContext,
        zone_status: HeartRateZoneStatus,
        action: CoachingAction,
        deviation_bpm: int,
        deviation_severity: HeartRateDeviationSeverity,
        reason: str,
    ) -> LiveCoachingDecision:
        return LiveCoachingDecision(
            action=action,
            zone_status=zone_status,
            heart_rate_bpm=context.heart_rate_bpm,
            target_min_bpm=context.target_min_bpm,
            target_max_bpm=context.target_max_bpm,
            outside_target_seconds=context.outside_target_seconds,
            deviation_bpm=deviation_bpm,
            deviation_severity=deviation_severity,
            reason=reason,
        )

    def _validate(self, context: LiveCoachingContext) -> None:
        if context.heart_rate_bpm <= 0:
            raise InvalidLiveCoachingContextError("Heart rate must be greater than zero")

        if context.target_min_bpm <= 0 or context.target_max_bpm <= 0:
            raise InvalidLiveCoachingContextError("Target heart rate must be greater than zero")

        if context.target_min_bpm > context.target_max_bpm:
            raise InvalidLiveCoachingContextError(
                "Minimum target heart rate must not exceed maximum target heart rate"
            )

        if context.outside_target_seconds < 0:
            raise InvalidLiveCoachingContextError("Outside-target duration must not be negative")

        if self._rules.deviation_seconds_before_action < 0:
            raise InvalidLiveCoachingContextError("Deviation threshold must not be negative")

        if self._rules.target_tolerance_bpm < 0:
            raise InvalidLiveCoachingContextError("Target tolerance must not be negative")

        if self._rules.large_deviation_bpm <= self._rules.target_tolerance_bpm:
            raise InvalidLiveCoachingContextError(
                "Large-deviation threshold must exceed target tolerance"
            )

        if self._rules.large_deviation_seconds_before_action < 0:
            raise InvalidLiveCoachingContextError(
                "Large-deviation duration threshold must not be negative"
            )
