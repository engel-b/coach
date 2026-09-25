import { describe, expect, it } from "vitest";

import { adaptiveWorkoutPresentation } from "./adaptiveWorkoutPresentation";
import type { AdaptiveWorkoutAdvice } from "./types";

function advice(
  overrides: Partial<AdaptiveWorkoutAdvice> = {},
): AdaptiveWorkoutAdvice {
  return {
    action: "keep_plan",
    reasonCodes: [],
    planReflectsAdvice: true,
    recommendedDurationMinutes: null,
    decisionContext: {
      workoutType: "base_endurance",
      availableTrainingMinutes: 45,
      readinessMaxDurationMinutes: null,
      heartRateHistoryStatus: "mostly_in_target",
      heartRateHistoryMaxDurationMinutes: null,
      loadResponseStatus: "stable",
      comparableWorkoutCount: 5,
      readinessCaution: false,
    },
    ...overrides,
  };
}

describe("adaptiveWorkoutPresentation", () => {
  it("omits missing advice", () => {
    expect(adaptiveWorkoutPresentation(null)).toBeNull();
  });

  it("shows an already applied duration cap", () => {
    const value = adaptiveWorkoutPresentation(
      advice({
        action: "reduce_duration",
        recommendedDurationMinutes: 30,
      }),
    );

    expect(value?.title).toBe("Adaptive Planung");
    expect(value?.text).toContain("30 Minuten");
    expect(value?.reflectedInPlan).toBe(true);
  });

  it("marks intensity reduction as advisory-only", () => {
    const value = adaptiveWorkoutPresentation(
      advice({
        action: "reduce_intensity",
        planReflectsAdvice: false,
      }),
    );

    expect(value?.title).toBe("Adaptiver Hinweis");
    expect(value?.text).toContain("noch nicht automatisch");
    expect(value?.reflectedInPlan).toBe(false);
  });

  it("does not turn lower HR at similar load into automatic progression", () => {
    const value = adaptiveWorkoutPresentation(
      advice({
        reasonCodes: ["lower_hr_at_similar_load", "no_automatic_progression"],
      }),
    );

    expect(value?.text).toContain("bleibt unverändert");
  });

  it("explains reason codes and exposes the decision context", () => {
    const value = adaptiveWorkoutPresentation(
      advice({
        action: "reduce_duration",
        reasonCodes: ["readiness_duration_cap"],
        recommendedDurationMinutes: 30,
        decisionContext: {
          workoutType: "base_endurance",
          availableTrainingMinutes: 60,
          readinessMaxDurationMinutes: 30,
          heartRateHistoryStatus: "mostly_in_target",
          heartRateHistoryMaxDurationMinutes: null,
          loadResponseStatus: "stable",
          comparableWorkoutCount: 5,
          readinessCaution: true,
        },
      }),
    );

    expect(value?.reasons).toContain(
      "Die heutige Tagesform begrenzt die sinnvolle Dauer.",
    );
    expect(value?.context).toContain("Readiness-Dauerlimit: 30 min");
    expect(value?.context).toContain("Readiness: heute mit Vorsichtssignal");
  });
});
