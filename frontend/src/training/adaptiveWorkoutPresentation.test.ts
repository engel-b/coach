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

    expect(value?.text).toContain("nicht automatisch zu erhöhen");
  });
});
