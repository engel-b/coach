from typing import ClassVar

from features.person.domain.profile import TrainingGoal
from features.training.domain.coach_message import CoachMessageContext
from features.training.domain.pre_workout import RecommendationReasonCode
from features.training.domain.weight_goal_progress import WeightGoalStatus
from features.training.domain.weight_trend import WeightTrendDirection


class PreWorkoutReasonBuilder:
    """
    Erzeugt den deterministischen Fallback-Text für eine Pre-Workout-Empfehlung.

    Die fachlichen Entscheidungen bleiben im Planner bzw. in den zugrunde
    liegenden Services. Dieser Builder formuliert nur bereits abgeleitete
    Fakten und Reason Codes. Damit kann er später durch eine LLM-basierte
    Formulierung ergänzt oder ersetzt werden, ohne die Entscheidungshoheit
    aus der deterministischen Coaching-Schicht zu verlagern.
    """

    _RECOVERY_REASONS: ClassVar[frozenset[RecommendationReasonCode]] = frozenset(
        {
            RecommendationReasonCode.LOW_ENERGY,
            RecommendationReasonCode.LOW_RECOVERY,
            RecommendationReasonCode.HIGH_MUSCLE_SORENESS,
            RecommendationReasonCode.HIGH_STRESS,
        }
    )

    def generate(
        self,
        *,
        context: CoachMessageContext,
    ) -> str:
        parts = [self._base_recommendation(context)]

        readiness_text = self._readiness_text(context)
        if readiness_text is not None:
            parts.append(readiness_text)

        if context.training_goal is TrainingGoal.WEIGHT_LOSS:
            weight_text = self._weight_text(context)
            if weight_text is not None:
                parts.append(weight_text)

        return " ".join(parts)

    def build(self, *, context: CoachMessageContext) -> str:
        """Kompatibilitätsalias; neue Aufrufer verwenden generate()."""
        return self.generate(context=context)

    def _base_recommendation(self, context: CoachMessageContext) -> str:
        if any(reason in self._RECOVERY_REASONS for reason in context.reason_codes):
            return "Dein heutiger Check-in spricht für eine eher regenerative Einheit."
        return "Dein heutiger Check-in spricht für eine lockere Grundlagen-Ausdauereinheit."

    @staticmethod
    def _readiness_text(
        context: CoachMessageContext,
    ) -> str | None:
        reason_codes = context.reason_codes

        # Eine konkrete Dauerbegrenzung ist für die Person wichtiger als die
        # einzelnen Signale, die dazu geführt haben. Die Reason Codes bleiben
        # vollständig erhalten und können separat in UI/LLM-Kontext erscheinen.
        if RecommendationReasonCode.DURATION_REDUCED_FOR_READINESS in reason_codes:
            causes: list[str] = []
            if RecommendationReasonCode.SHORT_SLEEP in reason_codes:
                causes.append("kurzem Schlaf")
            if RecommendationReasonCode.HIGH_DAILY_ACTIVITY in reason_codes:
                causes.append("hoher Alltagsaktivität")
            if RecommendationReasonCode.HIGH_RECENT_TRAINING_LOAD in reason_codes:
                causes.append("der Belastung der letzten Tage")

            cause_text = PreWorkoutReasonBuilder._join_causes(causes)
            if cause_text:
                return (
                    f"Wegen {cause_text} begrenzen wir die heutige Einheit auf "
                    f"maximal {context.readiness_max_duration_minutes} Minuten."
                )
            return (
                "Aufgrund deiner aktuellen Readiness begrenzen wir die heutige "
                f"Einheit auf maximal {context.readiness_max_duration_minutes} Minuten."
            )

        if RecommendationReasonCode.SHORT_SLEEP in reason_codes:
            return "Dein Schlaf war kurz, deshalb bleiben wir heute bewusst konservativ."
        if RecommendationReasonCode.HIGH_DAILY_ACTIVITY in reason_codes:
            return "Du warst heute bereits viel auf den Beinen; das berücksichtigen wir bei der Belastung."
        if RecommendationReasonCode.HIGH_RECENT_TRAINING_LOAD in reason_codes:
            return "In den letzten Tagen kam bereits einiges an Trainingszeit zusammen; heute bleiben wir zurückhaltender."
        return None

    @staticmethod
    def _weight_text(context: CoachMessageContext) -> str | None:
        trend_direction = context.weight_trend_direction
        progress = context.weight_goal_progress
        if progress is None:
            return None
        sentences: list[str] = []

        if trend_direction is WeightTrendDirection.DOWN:
            sentences.append("Dein geglätteter Gewichtstrend zeigt aktuell nach unten.")
        elif trend_direction is WeightTrendDirection.STABLE:
            sentences.append("Dein geglätteter Gewichtstrend ist aktuell weitgehend stabil.")
        elif trend_direction is WeightTrendDirection.UP:
            sentences.append(
                "Dein geglätteter Gewichtstrend zeigt aktuell nach oben; "
                "wir erhöhen die heutige Belastung deshalb aber nicht automatisch."
            )
        else:
            sentences.append(
                "Für einen belastbaren Gewichtstrend liegen noch nicht genug Daten vor."
            )

        # Fortschritt ist der motivierendere Langzeitkontext. Wenn er vorliegt,
        # reicht eine kompakte Aussage; die verbleibenden kg zeigt das Frontend
        # zusätzlich strukturiert an.
        if progress.lost_since_start_kg is not None and progress.progress_percent is not None:
            if progress.lost_since_start_kg > 0:
                sentences.append(
                    f"Seit deinem Start hast du {progress.lost_since_start_kg:.1f} kg verloren "
                    f"und {progress.progress_percent:.0f} % deines Weges zum Ziel erreicht."
                )
            elif progress.lost_since_start_kg < 0:
                sentences.append(
                    f"Dein aktuelles Gewicht liegt {abs(progress.lost_since_start_kg):.1f} kg über deinem Startgewicht."
                )

        if progress.status is WeightGoalStatus.AT_TARGET:
            sentences.append("Dein hinterlegtes Zielgewicht ist erreicht.")
        elif progress.status is WeightGoalStatus.BELOW_TARGET:
            sentences.append("Dein aktuelles Gewicht liegt unter deinem hinterlegten Zielgewicht.")
        elif progress.status is WeightGoalStatus.NO_CURRENT_WEIGHT:
            sentences.append("Für den Gewichtsfortschritt fehlt aktuell ein Gewichtswert.")
        elif progress.status is WeightGoalStatus.NO_GOAL:
            sentences.append("Für das Abnehmziel ist aktuell kein Zielgewicht hinterlegt.")

        return " ".join(sentences) if sentences else None

    @staticmethod
    def _join_causes(causes: list[str]) -> str:
        if not causes:
            return ""
        if len(causes) == 1:
            return causes[0]
        if len(causes) == 2:
            return f"{causes[0]} und {causes[1]}"
        return f"{', '.join(causes[:-1])} und {causes[-1]}"
