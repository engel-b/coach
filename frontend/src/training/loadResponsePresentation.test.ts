import { describe, expect, it } from "vitest";

import { loadResponsePresentation } from "./loadResponsePresentation";
import type { LoadResponse } from "./types";

function context(overrides: Partial<LoadResponse> = {}): LoadResponse {
  return {
    status: "stable",
    workoutType: "base_endurance",
    comparableWorkoutCount: 5,
    heartRateTrend: "stable",
    loadAdjustedHeartRateTrend: "stable_at_similar_power",
    medianPowerW: 120,
    medianCadenceRpm: 76.5,
    readinessCaution: false,
    ...overrides,
  };
}

describe("loadResponsePresentation", () => {
  it("omits missing and insufficient context", () => {
    expect(loadResponsePresentation(null)).toBeNull();
    expect(
      loadResponsePresentation(context({ status: "insufficient_data" })),
    ).toBeNull();
  });

  it("describes lower HR at similar load without prescribing more intensity", () => {
    const text = loadResponsePresentation(
      context({ status: "lower_hr_at_similar_load" }),
    );

    expect(text).toContain("bei ähnlicher Bike-Leistung niedriger");
    expect(text).toContain("120 W Medianleistung");
    expect(text).toContain("76.5 rpm Mediankadenz");
    expect(text).toContain("rein deskriptiv");
  });

  it("includes a current readiness caution separately", () => {
    expect(
      loadResponsePresentation(context({ readinessCaution: true })),
    ).toContain("heutige Readiness");
  });
});
