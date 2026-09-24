from dataclasses import replace

from features.person.domain.profile import TrainingGoal
from features.training.domain.coach_message import CoachMessageContext
from features.training.domain.coach_message_generator import CoachMessageGenerator
from features.training.domain.heart_rate_history import HeartRateHistoryStatus
from features.training.domain.pre_workout import (
    PreWorkoutCoachingContext,
    RecommendationReasonCode,
)
from features.training.domain.readiness import (
    DailyActivityStatus,
    RecentTrainingLoadStatus,
    SleepStatus,
)
from features.training.domain.recommendation import TrainingRecommendation
from features.training.domain.recommendation_engine import TrainingRecommendationEngine
from features.training.domain.weight_goal_progress import WeightGoalStatus
from features.training.domain.weight_trend import WeightTrendDirection
from features.training.service.pre_workout_reason_builder import PreWorkoutReasonBuilder


class PreWorkoutCoachingPlanner:
    """
    Orchestriert die deterministische Pre-Workout-Empfehlung.

    Der bestehende TrainingRecommendationEngine entscheidet weiterhin
    über Workout-Typ, Dauer und Herzfrequenzphasen. Der Planner ergänzt
    den größeren Coaching-Kontext und strukturierte Begründungen.

    Gewichtstrend und geringe Aktivität dürfen die Trainingslast nicht
    erhöhen. Belastende Readiness-Signale können die verfügbare Dauer
    konservativ begrenzen; subjektive Recovery-Regeln haben Vorrang.
    """

    def __init__(
        self,
        engine: TrainingRecommendationEngine,
        message_generator: CoachMessageGenerator | None = None,
    ) -> None:
        self._engine = engine
        self._message_generator = message_generator or PreWorkoutReasonBuilder()

    def recommend(
        self,
        context: PreWorkoutCoachingContext,
    ) -> TrainingRecommendation:
        effective_check_in = context.check_in
        duration_caps = [
            cap
            for cap in (
                context.readiness.max_duration_minutes,
                context.heart_rate_history.max_duration_minutes,
            )
            if cap is not None
        ]
        duration_cap = min(duration_caps) if duration_caps else None

        if (
            duration_cap is not None
            and effective_check_in.available_training_minutes > duration_cap
        ):
            effective_check_in = replace(
                effective_check_in,
                available_training_minutes=duration_cap,
            )

        recommendation = self._engine.recommend(
            check_in=effective_check_in,
            max_heart_rate=context.max_heart_rate,
            resting_heart_rate=context.resting_heart_rate,
            resting_heart_rate_source=context.resting_heart_rate_source,
            resting_heart_rate_sample_count=context.resting_heart_rate_sample_count,
        )
        reason_codes = self._reason_codes(context)

        return replace(
            recommendation,
            reason=self._message_generator.generate(
                context=CoachMessageContext(
                    workout_type=recommendation.workout_type,
                    total_duration_minutes=recommendation.total_duration_minutes,
                    reason_codes=reason_codes,
                    training_goal=context.training_goal,
                    readiness_max_duration_minutes=context.readiness.max_duration_minutes,
                    weight_trend_direction=context.weight_trend.direction,
                    weight_trend_kg_per_week=context.weight_trend.weekly_change_kg,
                    weight_goal_progress=(
                        context.weight_goal_progress
                        if context.training_goal is TrainingGoal.WEIGHT_LOSS
                        else None
                    ),
                ),
            ),
            reason_codes=reason_codes,
            weight_goal_progress=(
                context.weight_goal_progress
                if context.training_goal is TrainingGoal.WEIGHT_LOSS
                else None
            ),
            heart_rate_history=context.heart_rate_history,
            load_response=context.load_response,
        )

    @staticmethod
    def _reason_codes(
        context: PreWorkoutCoachingContext,
    ) -> tuple[RecommendationReasonCode, ...]:
        check_in = context.check_in
        readiness = context.readiness
        reasons: list[RecommendationReasonCode] = []

        if check_in.energy <= 2:
            reasons.append(RecommendationReasonCode.LOW_ENERGY)
        if check_in.recovery <= 2:
            reasons.append(RecommendationReasonCode.LOW_RECOVERY)
        if check_in.muscle_soreness >= 4:
            reasons.append(RecommendationReasonCode.HIGH_MUSCLE_SORENESS)
        if check_in.stress >= 4:
            reasons.append(RecommendationReasonCode.HIGH_STRESS)
        if readiness.sleep_status is SleepStatus.SHORT:
            reasons.append(RecommendationReasonCode.SHORT_SLEEP)
        if readiness.daily_activity_status is DailyActivityStatus.HIGH:
            reasons.append(RecommendationReasonCode.HIGH_DAILY_ACTIVITY)
        if readiness.recent_training_load_status is RecentTrainingLoadStatus.HIGH:
            reasons.append(RecommendationReasonCode.HIGH_RECENT_TRAINING_LOAD)
        if (
            readiness.max_duration_minutes is not None
            and check_in.available_training_minutes > readiness.max_duration_minutes
        ):
            reasons.append(RecommendationReasonCode.DURATION_REDUCED_FOR_READINESS)

        if (
            context.heart_rate_history.max_duration_minutes is not None
            and check_in.available_training_minutes
            > context.heart_rate_history.max_duration_minutes
        ):
            reasons.append(RecommendationReasonCode.DURATION_REDUCED_FOR_HEART_RATE_HISTORY)

        readiness_warnings = {
            RecommendationReasonCode.LOW_ENERGY,
            RecommendationReasonCode.LOW_RECOVERY,
            RecommendationReasonCode.HIGH_MUSCLE_SORENESS,
            RecommendationReasonCode.HIGH_STRESS,
            RecommendationReasonCode.SHORT_SLEEP,
            RecommendationReasonCode.HIGH_DAILY_ACTIVITY,
            RecommendationReasonCode.HIGH_RECENT_TRAINING_LOAD,
        }
        if not any(reason in readiness_warnings for reason in reasons):
            reasons.append(RecommendationReasonCode.READINESS_GOOD)

        if context.training_goal is TrainingGoal.WEIGHT_LOSS:
            reasons.append(RecommendationReasonCode.WEIGHT_LOSS_GOAL)
            reasons.append(
                {
                    WeightTrendDirection.DOWN: RecommendationReasonCode.WEIGHT_TREND_DOWN,
                    WeightTrendDirection.STABLE: RecommendationReasonCode.WEIGHT_TREND_STABLE,
                    WeightTrendDirection.UP: RecommendationReasonCode.WEIGHT_TREND_UP,
                    WeightTrendDirection.UNKNOWN: RecommendationReasonCode.WEIGHT_TREND_UNKNOWN,
                }[context.weight_trend.direction]
            )
            reasons.append(
                {
                    WeightGoalStatus.NO_GOAL: RecommendationReasonCode.WEIGHT_GOAL_NOT_CONFIGURED,
                    WeightGoalStatus.NO_CURRENT_WEIGHT: RecommendationReasonCode.WEIGHT_GOAL_NO_CURRENT_WEIGHT,
                    WeightGoalStatus.ABOVE_TARGET: RecommendationReasonCode.WEIGHT_GOAL_ABOVE_TARGET,
                    WeightGoalStatus.AT_TARGET: RecommendationReasonCode.WEIGHT_GOAL_AT_TARGET,
                    WeightGoalStatus.BELOW_TARGET: RecommendationReasonCode.WEIGHT_GOAL_BELOW_TARGET,
                }[context.weight_goal_progress.status]
            )

        history_reason = {
            HeartRateHistoryStatus.MOSTLY_IN_TARGET: (
                RecommendationReasonCode.HEART_RATE_HISTORY_IN_TARGET
            ),
            HeartRateHistoryStatus.MOSTLY_ABOVE_TARGET: (
                RecommendationReasonCode.HEART_RATE_HISTORY_ABOVE_TARGET
            ),
            HeartRateHistoryStatus.MOSTLY_BELOW_TARGET: (
                RecommendationReasonCode.HEART_RATE_HISTORY_BELOW_TARGET
            ),
            HeartRateHistoryStatus.MIXED: RecommendationReasonCode.HEART_RATE_HISTORY_MIXED,
        }.get(context.heart_rate_history.status)
        if history_reason is not None:
            reasons.append(history_reason)

        return tuple(reasons)
