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
  weight_goal_above_target: "Zielgewicht noch offen",
  weight_goal_at_target: "Zielgewicht erreicht",
  weight_goal_below_target: "Unter Zielgewicht",
  weight_goal_no_current_weight: "Aktuelles Gewicht fehlt",
  weight_goal_not_configured: "Zielgewicht fehlt",
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

export interface WeightGoalProgressPresentation {
  percent: number;
  headline: string;
  detail: string;
}

function formatKg(value: number): string {
  return value.toLocaleString("de-DE", {
    minimumFractionDigits: 1,
    maximumFractionDigits: 1,
  });
}

export function weightGoalProgressPresentation(
  recommendation: TrainingRecommendation,
): WeightGoalProgressPresentation | null {
  const progress = recommendation.weightGoalProgress;

  if (
    progress === null ||
    progress.progressPercent === null ||
    progress.lostSinceStartKg === null
  ) {
    return null;
  }

  const percent = Math.max(0, Math.min(100, progress.progressPercent));
  const headline = `${Math.round(percent)} % des Weges geschafft`;

  if (progress.lostSinceStartKg < 0) {
    return {
      percent,
      headline,
      detail: `Aktuell ${formatKg(Math.abs(progress.lostSinceStartKg))} kg über dem Startgewicht`,
    };
  }

  if (progress.lostSinceStartKg === 0) {
    return {
      percent,
      headline,
      detail: "Aktuell noch auf dem Startgewicht",
    };
  }

  if (progress.status === "at_target") {
    return {
      percent,
      headline: "Zielgewicht erreicht",
      detail: `${formatKg(progress.lostSinceStartKg)} kg seit dem Start`,
    };
  }

  if (progress.status === "below_target") {
    return {
      percent,
      headline: "Zielgewicht erreicht",
      detail: `${formatKg(progress.lostSinceStartKg)} kg seit dem Start`,
    };
  }

  if (progress.remainingKg !== null) {
    return {
      percent,
      headline,
      detail: `${formatKg(progress.lostSinceStartKg)} kg geschafft · ${formatKg(progress.remainingKg)} kg verbleibend`,
    };
  }

  return {
    percent,
    headline,
    detail: `${formatKg(progress.lostSinceStartKg)} kg seit dem Start`,
  };
}
