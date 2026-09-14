import { describe, expect, it } from "vitest";

import {
  recommendationReasonLabels,
  weightTrendLabel,
  workoutTitle,
} from "./recommendationPresentation";
import type { TrainingRecommendation } from "./types";

function recommendation(reasonCodes: string[]): TrainingRecommendation {
  return {
    workoutType: "base_endurance",
    totalDurationMinutes: 30,
    reason: "Test",
    reasonCodes,
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

  it("ignores unknown future reason codes", () => {
    expect(
      recommendationReasonLabels(recommendation(["future_reason"])),
    ).toEqual([]);
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
