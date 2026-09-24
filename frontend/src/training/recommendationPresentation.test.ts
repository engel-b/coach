import { describe, expect, it } from "vitest";

import {
  recommendationReasonLabels,
  weightTrendLabel,
  workoutTitle,
  weightGoalProgressPresentation,
} from "./recommendationPresentation";
import type { TrainingRecommendation } from "./types";

function recommendation(reasonCodes: string[]): TrainingRecommendation {
  return {
    workoutType: "base_endurance",
    totalDurationMinutes: 30,
    reason: "Test",
    heartRateTargetBasis: {
      method: "max_heart_rate_percentage",
      maxHeartRateBpm: 180,
      restingHeartRateBpm: null,
      referenceRestingHeartRateBpm: null,
      restingHeartRateSource: null,
      restingHeartRateSampleCount: 0,
    },
    heartRateHistory: null,
    loadResponse: null,
    adaptiveWorkoutAdvice: null,
    reasonCodes,
    weightGoalProgress: null,
    phases: [],
  };
}

describe("recommendationPresentation", () => {
  it("formats workout types for display", () => {
    expect(workoutTitle("recovery")).toBe("Regeneration");
    expect(workoutTitle("base_endurance")).toBe("Grundlagenausdauer");
    expect(workoutTitle("moderate")).toBe("Moderates Training");
  });

  it("maps stable reason codes to German labels", () => {
    expect(
      recommendationReasonLabels(
        recommendation(["readiness_good", "weight_trend_down"]),
      ),
    ).toEqual(["Tagesform gut", "Gewichtstrend sinkt"]);
  });

  it("maps readiness adjustment reasons", () => {
    expect(
      recommendationReasonLabels(
        recommendation([
          "short_sleep",
          "high_recent_training_load",
          "duration_reduced_for_readiness",
        ]),
      ),
    ).toEqual(["Schlaf kurz", "Zuletzt viel trainiert", "Dauer angepasst"]);
  });

  it("ignores unknown future reason codes", () => {
    expect(
      recommendationReasonLabels(recommendation(["future_reason"])),
    ).toEqual([]);
  });

  it("formats structured weight-goal progress", () => {
    const value = recommendation(["weight_loss_goal"]);
    value.weightGoalProgress = {
      status: "above_target",
      startWeightKg: 100,
      currentWeightKg: 92,
      targetWeightKg: 80,
      remainingKg: 12,
      lostSinceStartKg: 8,
      progressPercent: 40,
    };

    expect(weightGoalProgressPresentation(value)).toEqual({
      percent: 40,
      headline: "40 % des Weges geschafft",
      detail: "8,0 kg geschafft · 12,0 kg verbleibend",
    });
  });

  it("does not describe weight above the start as accomplished loss", () => {
    const value = recommendation(["weight_loss_goal"]);
    value.weightGoalProgress = {
      status: "above_target",
      startWeightKg: 100,
      currentWeightKg: 102,
      targetWeightKg: 80,
      remainingKg: 22,
      lostSinceStartKg: -2,
      progressPercent: 0,
    };

    expect(weightGoalProgressPresentation(value)?.detail).toBe(
      "Aktuell 2,0 kg über dem Startgewicht",
    );
  });

  it("omits incomplete weight-goal progress", () => {
    expect(weightGoalProgressPresentation(recommendation([]))).toBeNull();
  });

  it("derives the qualitative weight trend from backend reason codes", () => {
    expect(weightTrendLabel(recommendation(["weight_trend_down"]))).toBe(
      "sinkt",
    );
    expect(weightTrendLabel(recommendation(["weight_trend_unknown"]))).toBe(
      "noch nicht belastbar",
    );
    expect(weightTrendLabel(recommendation(["readiness_good"]))).toBeNull();
  });
});
