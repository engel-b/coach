from features.coaching.domain.live_coaching import (
    CoachingAction,
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

        if zone_status == HeartRateZoneStatus.IN_TARGET:
            return self._decision(
                context=context,
                zone_status=zone_status,
                action=CoachingAction.NONE,
                reason="heart_rate_in_target",
            )

        if context.outside_target_seconds < self._rules.deviation_seconds_before_action:
            return self._decision(
                context=context,
                zone_status=zone_status,
                action=CoachingAction.NONE,
                reason="deviation_too_short",
            )

        if zone_status == HeartRateZoneStatus.BELOW_TARGET:
            return self._decision(
                context=context,
                zone_status=zone_status,
                action=CoachingAction.INCREASE_INTENSITY,
                reason="heart_rate_below_target_long_enough",
            )

        return self._decision(
            context=context,
            zone_status=zone_status,
            action=CoachingAction.REDUCE_INTENSITY,
            reason="heart_rate_above_target_long_enough",
        )

    def _zone_status(self, context: LiveCoachingContext) -> HeartRateZoneStatus:
        if context.heart_rate_bpm < context.target_min_bpm - self._rules.target_tolerance_bpm:
            return HeartRateZoneStatus.BELOW_TARGET

        if context.heart_rate_bpm > context.target_max_bpm + self._rules.target_tolerance_bpm:
            return HeartRateZoneStatus.ABOVE_TARGET

        return HeartRateZoneStatus.IN_TARGET

    @staticmethod
    def _decision(
        *,
        context: LiveCoachingContext,
        zone_status: HeartRateZoneStatus,
        action: CoachingAction,
        reason: str,
    ) -> LiveCoachingDecision:
        return LiveCoachingDecision(
            action=action,
            zone_status=zone_status,
            heart_rate_bpm=context.heart_rate_bpm,
            target_min_bpm=context.target_min_bpm,
            target_max_bpm=context.target_max_bpm,
            outside_target_seconds=context.outside_target_seconds,
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
