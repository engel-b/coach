import type { AdaptiveWorkoutAdvice } from "./types";

export interface AdaptiveWorkoutPresentation {
  title: string;
  text: string;
  reflectedInPlan: boolean;
}

export function adaptiveWorkoutPresentation(
  advice: AdaptiveWorkoutAdvice | null,
): AdaptiveWorkoutPresentation | null {
  if (advice === null) {
    return null;
  }

  const text = {
    keep_plan: advice.reasonCodes.includes("no_automatic_progression")
      ? "Die bisherigen Daten geben keinen Grund, die heutige Belastung automatisch zu erhöhen. Der aktuelle Plan bleibt unverändert."
      : "Der aktuelle Trainingsplan kann unverändert bleiben.",
    reduce_duration:
      advice.recommendedDurationMinutes === null
        ? "Eine kürzere Einheit ist heute die konservative Anpassung."
        : `Die heutige Einheit wird konservativ auf ${advice.recommendedDurationMinutes} Minuten begrenzt.`,
    reduce_intensity:
      "Die historischen Daten sprechen dafür, die Belastung eher etwas niedriger zu halten. Dieser Hinweis wird noch nicht automatisch auf Zielpuls oder Bike-Widerstand angewendet.",
    extend_warmup:
      "Eine längere, ruhige Aufwärmphase wäre eine konservative Option. Der aktuelle Plan wird dadurch noch nicht automatisch verändert.",
    prefer_recovery:
      "Der heutige Plan berücksichtigt bereits eine regenerative Ausrichtung.",
  }[advice.action];

  return {
    title: advice.planReflectsAdvice ? "Adaptive Planung" : "Adaptiver Hinweis",
    text,
    reflectedInPlan: advice.planReflectsAdvice,
  };
}
