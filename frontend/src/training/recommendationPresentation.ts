import type { TrainingRecommendation, WorkoutType } from "./types";

const REASON_LABELS: Readonly<Record<string, string>> = {
  low_energy: "Energie niedrig",
  low_recovery: "Erholung niedrig",
  high_muscle_soreness: "Muskelkater erhöht",
  high_stress: "Stress erhöht",
  short_sleep: "Schlaf kurz",
  high_daily_activity: "Heute bereits viel bewegt",
  high_recent_training_load: "Zuletzt viel trainiert",
  duration_reduced_for_readiness: "Dauer angepasst",
  readiness_good: "Tagesform gut",
  weight_loss_goal: "Ziel: Gewicht reduzieren",
  weight_trend_down: "Gewichtstrend sinkt",
  weight_trend_stable: "Gewichtstrend stabil",
  weight_trend_up: "Gewichtstrend steigt",
  weight_trend_unknown: "Gewichtstrend noch offen",
};

export function workoutTitle(type: WorkoutType): string {
  switch (type) {
    case "recovery":
      return "Regeneration";
    case "base_endurance":
      return "Grundlagenausdauer";
    case "moderate":
      return "Moderates Training";
  }
}

export function recommendationReasonLabels(
  recommendation: TrainingRecommendation,
): string[] {
  return recommendation.reasonCodes.flatMap((reasonCode) => {
    const label = REASON_LABELS[reasonCode];
    return label === undefined ? [] : [label];
  });
}

export function weightTrendLabel(
  recommendation: TrainingRecommendation,
): string | null {
  if (recommendation.reasonCodes.includes("weight_trend_down")) {
    return "sinkt";
  }
  if (recommendation.reasonCodes.includes("weight_trend_stable")) {
    return "stabil";
  }
  if (recommendation.reasonCodes.includes("weight_trend_up")) {
    return "steigt";
  }
  if (recommendation.reasonCodes.includes("weight_trend_unknown")) {
    return "noch nicht belastbar";
  }

  return null;
}
