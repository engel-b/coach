import type { AdaptiveWorkoutAdvice } from "./types";

export interface AdaptiveWorkoutPresentation {
  title: string;
  text: string;
  reflectedInPlan: boolean;
  reasons: string[];
  context: string[];
}

const REASON_LABELS: Readonly<Record<string, string>> = {
  recovery_plan_selected: "Regenerative Einheit wurde bereits gewählt.",
  readiness_duration_cap: "Die heutige Tagesform begrenzt die sinnvolle Dauer.",
  heart_rate_history_duration_cap:
    "Die historische Herzfrequenz-Reaktion begrenzt die sinnvolle Dauer.",
  higher_hr_at_similar_load:
    "Bei ähnlicher Bike-Leistung war die Herzfrequenz zuletzt höher.",
  lower_hr_at_similar_load:
    "Bei ähnlicher Bike-Leistung war die Herzfrequenz zuletzt niedriger.",
  no_automatic_progression:
    "Eine günstigere Reaktion führt nicht automatisch zu mehr Belastung.",
  insufficient_comparable_data:
    "Für eine belastbare adaptive Einordnung fehlen noch vergleichbare Workouts.",
};

const HISTORY_STATUS_LABELS: Readonly<Record<string, string>> = {
  insufficient_data: "noch nicht ausreichend Daten",
  mostly_in_target: "überwiegend im Zielbereich",
  mostly_above_target: "häufig oberhalb des Zielbereichs",
  mostly_below_target: "häufig unterhalb des Zielbereichs",
  mixed: "gemischte Reaktion",
};

const LOAD_STATUS_LABELS: Readonly<Record<string, string>> = {
  insufficient_data: "noch nicht ausreichend vergleichbare Belastungsdaten",
  stable: "weitgehend stabile Belastungsreaktion",
  lower_hr_at_similar_load: "niedrigere HF bei ähnlicher Leistung",
  higher_hr_at_similar_load: "höhere HF bei ähnlicher Leistung",
  lower_load: "niedrigere Bike-Belastung",
  higher_load: "höhere Bike-Belastung",
  mixed: "gemischte Belastungsreaktion",
};

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

  const decision = advice.decisionContext;
  const context = [
    `Verfügbare Zeit: ${decision.availableTrainingMinutes} min`,
    `HF-Historie: ${HISTORY_STATUS_LABELS[decision.heartRateHistoryStatus] ?? decision.heartRateHistoryStatus}`,
    `Belastungsreaktion: ${LOAD_STATUS_LABELS[decision.loadResponseStatus] ?? decision.loadResponseStatus}`,
    `Vergleichbare Workouts: ${decision.comparableWorkoutCount}`,
  ];

  if (decision.readinessMaxDurationMinutes !== null) {
    context.push(
      `Readiness-Dauerlimit: ${decision.readinessMaxDurationMinutes} min`,
    );
  }
  if (decision.heartRateHistoryMaxDurationMinutes !== null) {
    context.push(
      `Historisches HF-Dauerlimit: ${decision.heartRateHistoryMaxDurationMinutes} min`,
    );
  }
  if (decision.readinessCaution) {
    context.push("Readiness: heute mit Vorsichtssignal");
  }

  return {
    title: advice.planReflectsAdvice ? "Adaptive Planung" : "Adaptiver Hinweis",
    text,
    reflectedInPlan: advice.planReflectsAdvice,
    reasons: advice.reasonCodes.flatMap((reasonCode) => {
      const label = REASON_LABELS[reasonCode];
      return label === undefined ? [] : [label];
    }),
    context,
  };
}
