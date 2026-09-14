from dataclasses import replace

from features.person.domain.profile import TrainingGoal
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

    def __init__(self, engine: TrainingRecommendationEngine) -> None:
        self._engine = engine

    def recommend(
        self,
        context: PreWorkoutCoachingContext,
    ) -> TrainingRecommendation:
        effective_check_in = context.check_in
        duration_cap = context.readiness.max_duration_minutes

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
        )
        reason_codes = self._reason_codes(context)

        return replace(
            recommendation,
            reason=self._reason_text(context, reason_codes),
            reason_codes=reason_codes,
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

        return tuple(reasons)

    @staticmethod
    def _reason_text(
        context: PreWorkoutCoachingContext,
        reason_codes: tuple[RecommendationReasonCode, ...],
    ) -> str:
        recovery_reasons = {
            RecommendationReasonCode.LOW_ENERGY,
            RecommendationReasonCode.LOW_RECOVERY,
            RecommendationReasonCode.HIGH_MUSCLE_SORENESS,
            RecommendationReasonCode.HIGH_STRESS,
        }

        parts: list[str] = []
        if any(reason in recovery_reasons for reason in reason_codes):
            parts.append("Dein heutiger Check-in spricht für eine eher regenerative Einheit.")
        else:
            parts.append("Dein heutiger Check-in spricht für eine lockere Grundlagen-Ausdauereinheit.")

        if RecommendationReasonCode.SHORT_SLEEP in reason_codes:
            parts.append("Dein Schlaf war kurz, deshalb bleiben wir heute bewusst konservativ.")
        if RecommendationReasonCode.HIGH_DAILY_ACTIVITY in reason_codes:
            parts.append(
                "Du warst heute bereits viel auf den Beinen; diese Aktivität berücksichtigen wir bei der Trainingsdauer."
            )
        if RecommendationReasonCode.HIGH_RECENT_TRAINING_LOAD in reason_codes:
            parts.append(
                "In den letzten Tagen kam bereits einiges an Trainingszeit zusammen; deshalb planen wir heute zurückhaltender."
            )
        if RecommendationReasonCode.DURATION_REDUCED_FOR_READINESS in reason_codes:
            parts.append(
                f"Die heutige Einheit wird deshalb auf maximal {context.readiness.max_duration_minutes} Minuten begrenzt."
            )

        if context.training_goal is TrainingGoal.WEIGHT_LOSS:
            trend = context.weight_trend
            if trend.direction is WeightTrendDirection.DOWN:
                parts.append("Dein geglätteter Gewichtstrend zeigt aktuell nach unten.")
            elif trend.direction is WeightTrendDirection.STABLE:
                parts.append("Dein geglätteter Gewichtstrend ist aktuell weitgehend stabil.")
            elif trend.direction is WeightTrendDirection.UP:
                parts.append(
                    "Dein geglätteter Gewichtstrend zeigt aktuell nach oben; "
                    "wir erhöhen die heutige Belastung deshalb aber nicht automatisch."
                )
            else:
                parts.append("Für einen belastbaren Gewichtstrend liegen noch nicht genug Daten vor.")

            goal_progress = context.weight_goal_progress
            if goal_progress.status is WeightGoalStatus.ABOVE_TARGET:
                parts.append(
                    f"Bis zu deinem hinterlegten Zielgewicht sind es aktuell noch {goal_progress.remaining_kg:.1f} kg."
                )
            elif goal_progress.status is WeightGoalStatus.AT_TARGET:
                parts.append("Dein aktuelles Gewicht entspricht deinem hinterlegten Zielgewicht.")
            elif goal_progress.status is WeightGoalStatus.BELOW_TARGET:
                parts.append(
                    f"Dein aktuelles Gewicht liegt {abs(goal_progress.remaining_kg or 0.0):.1f} kg unter deinem hinterlegten Zielgewicht."
                )
            elif goal_progress.status is WeightGoalStatus.NO_CURRENT_WEIGHT:
                parts.append("Für den Abstand zum Zielgewicht fehlt aktuell ein Gewichtswert.")
            else:
                parts.append("Für das Abnehmziel ist aktuell kein Zielgewicht hinterlegt.")

        return " ".join(parts)
