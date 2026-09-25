from features.training.domain.adaptive_workout import (
    AdaptiveWorkoutAction,
    AdaptiveWorkoutAdvice,
    AdaptiveWorkoutDecisionContext,
    AdaptiveWorkoutReasonCode,
)
from features.training.domain.heart_rate_history import (
    HeartRateHistoryContext,
    HeartRateHistoryStatus,
)
from features.training.domain.load_response import LoadResponseContext, LoadResponseStatus
from features.training.domain.readiness import ReadinessContext
from features.training.domain.recommendation import WorkoutType


class AdaptiveWorkoutPolicy:
    """
    Leitet konservative Anpassungsvorschläge aus bereits bewerteten Signalen ab.

    Die Policy darf keine automatische Progression auslösen. Bestehende
    Dauerbegrenzungen aus Readiness und HF-Historie werden als bereits im Plan
    reflektiert ausgewiesen; Änderungen an Intensität oder Warm-up bleiben in
    dieser Ausbaustufe advisory-only.
    """

    def assess(
        self,
        *,
        workout_type: WorkoutType,
        available_training_minutes: int,
        readiness: ReadinessContext,
        heart_rate_history: HeartRateHistoryContext,
        load_response: LoadResponseContext,
    ) -> AdaptiveWorkoutAdvice:
        decision_context = AdaptiveWorkoutDecisionContext(
            workout_type=workout_type,
            available_training_minutes=available_training_minutes,
            readiness_max_duration_minutes=readiness.max_duration_minutes,
            heart_rate_history_status=heart_rate_history.status,
            heart_rate_history_max_duration_minutes=(heart_rate_history.max_duration_minutes),
            load_response_status=load_response.status,
            comparable_workout_count=load_response.comparable_workout_count,
            readiness_caution=load_response.readiness_caution,
        )

        if workout_type is WorkoutType.RECOVERY:
            return AdaptiveWorkoutAdvice(
                action=AdaptiveWorkoutAction.PREFER_RECOVERY,
                reason_codes=(AdaptiveWorkoutReasonCode.RECOVERY_PLAN_SELECTED,),
                plan_reflects_advice=True,
                decision_context=decision_context,
            )

        duration_caps: list[tuple[int, AdaptiveWorkoutReasonCode]] = []
        if readiness.max_duration_minutes is not None:
            duration_caps.append(
                (
                    readiness.max_duration_minutes,
                    AdaptiveWorkoutReasonCode.READINESS_DURATION_CAP,
                )
            )
        if heart_rate_history.max_duration_minutes is not None:
            duration_caps.append(
                (
                    heart_rate_history.max_duration_minutes,
                    AdaptiveWorkoutReasonCode.HEART_RATE_HISTORY_DURATION_CAP,
                )
            )

        if duration_caps:
            duration_cap = min(cap for cap, _ in duration_caps)
            if available_training_minutes > duration_cap:
                reasons = tuple(reason for cap, reason in duration_caps if cap == duration_cap)
                return AdaptiveWorkoutAdvice(
                    action=AdaptiveWorkoutAction.REDUCE_DURATION,
                    reason_codes=reasons,
                    plan_reflects_advice=True,
                    decision_context=decision_context,
                    recommended_duration_minutes=duration_cap,
                )

        if load_response.status is LoadResponseStatus.HIGHER_HR_AT_SIMILAR_LOAD:
            if heart_rate_history.status is HeartRateHistoryStatus.MOSTLY_ABOVE_TARGET:
                return AdaptiveWorkoutAdvice(
                    action=AdaptiveWorkoutAction.REDUCE_INTENSITY,
                    reason_codes=(AdaptiveWorkoutReasonCode.HIGHER_HR_AT_SIMILAR_LOAD,),
                    plan_reflects_advice=False,
                    decision_context=decision_context,
                )

            return AdaptiveWorkoutAdvice(
                action=AdaptiveWorkoutAction.EXTEND_WARMUP,
                reason_codes=(AdaptiveWorkoutReasonCode.HIGHER_HR_AT_SIMILAR_LOAD,),
                plan_reflects_advice=False,
                decision_context=decision_context,
            )

        if load_response.status is LoadResponseStatus.LOWER_HR_AT_SIMILAR_LOAD:
            return AdaptiveWorkoutAdvice(
                action=AdaptiveWorkoutAction.KEEP_PLAN,
                reason_codes=(
                    AdaptiveWorkoutReasonCode.LOWER_HR_AT_SIMILAR_LOAD,
                    AdaptiveWorkoutReasonCode.NO_AUTOMATIC_PROGRESSION,
                ),
                plan_reflects_advice=True,
                decision_context=decision_context,
            )

        if load_response.status is LoadResponseStatus.INSUFFICIENT_DATA:
            return AdaptiveWorkoutAdvice(
                action=AdaptiveWorkoutAction.KEEP_PLAN,
                reason_codes=(AdaptiveWorkoutReasonCode.INSUFFICIENT_COMPARABLE_DATA,),
                plan_reflects_advice=True,
                decision_context=decision_context,
            )

        return AdaptiveWorkoutAdvice(
            action=AdaptiveWorkoutAction.KEEP_PLAN,
            reason_codes=(),
            plan_reflects_advice=True,
            decision_context=decision_context,
        )
