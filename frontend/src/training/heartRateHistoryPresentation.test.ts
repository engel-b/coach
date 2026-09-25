import { describe, expect, it } from "vitest";

import { heartRateHistoryPresentation } from "./heartRateHistoryPresentation";
import type { HeartRateHistory } from "./types";

function history(overrides: Partial<HeartRateHistory> = {}): HeartRateHistory {
  return {
    status: "mostly_in_target",
    workoutCount: 4,
    workoutType: "base_endurance",
    medianInTargetPercent: 65,
    medianAboveTargetPercent: 20,
    medianBelowTargetPercent: 15,
    maxDurationMinutes: null,
    responseTrend: "stable",
    medianTargetPositionPercent: 55,
    targetPositionChangePoints: 3,
    loadAdjustedTrend: "stable_at_similar_power",
    medianPowerW: 120,
    medianCadenceRpm: 76.5,
    powerChangePercent: 2,
    ...overrides,
  };
}

describe("heartRateHistoryPresentation", () => {
  it("omits missing history", () => {
    expect(heartRateHistoryPresentation(null)).toBeNull();
  });

  it("omits history with insufficient data", () => {
    expect(
      heartRateHistoryPresentation(
        history({
          status: "insufficient_data",
          workoutCount: 2,
          responseTrend: "insufficient_data",
          loadAdjustedTrend: "insufficient_data",
        }),
      ),
    ).toBeNull();
  });

  it("explains comparable workout scope and conservative high-HR handling", () => {
    const presentation = heartRateHistoryPresentation(
      history({
        status: "mostly_above_target",
        workoutCount: 5,
        workoutType: "base_endurance",
      }),
    );

    expect(presentation?.scope).toBe(
      "Auswertung nur für Grundlagen-Einheiten.",
    );
    expect(presentation?.statusText).toContain(
      "häufig oberhalb des Zielbereichs",
    );
    expect(presentation?.statusText).toContain(
      "Zielpuls- und Safety-Grenzen werden nicht angehoben",
    );
  });

  it("describes lower heart rate at similar power without prescribing more load", () => {
    const presentation = heartRateHistoryPresentation(
      history({
        responseTrend: "lower",
        targetPositionChangePoints: -20,
        loadAdjustedTrend: "lower_at_similar_power",
        medianPowerW: 121,
        powerChangePercent: 1,
      }),
    );

    expect(presentation?.responseTrendText).toContain(
      "niedriger als bei den älteren",
    );
    expect(presentation?.responseTrendText).toContain("-20 Prozentpunkte");
    expect(presentation?.loadAdjustedTrendText).toContain(
      "obwohl die durchschnittliche Bike-Leistung ähnlich blieb",
    );
    expect(presentation?.loadAdjustedTrendText).toContain(
      "verändert die Trainingsintensität nicht automatisch",
    );
  });

  it("does not interpret lower HR with lower power as improvement", () => {
    const presentation = heartRateHistoryPresentation(
      history({
        loadAdjustedTrend: "lower_with_lower_power",
        powerChangePercent: -24,
      }),
    );

    expect(presentation?.loadAdjustedTrendText).toContain(
      "niedrigeren durchschnittlichen Bike-Leistung",
    );
    expect(presentation?.loadAdjustedTrendText).toContain(
      "nicht als günstigere Reaktion interpretiert",
    );
    expect(presentation?.loadAdjustedTrendText).toContain(
      "Leistungsänderung: -24 %",
    );
  });

  it("separates a higher HR response from a simultaneous higher power load", () => {
    const presentation = heartRateHistoryPresentation(
      history({
        loadAdjustedTrend: "higher_with_higher_power",
        powerChangePercent: 18,
      }),
    );

    expect(presentation?.loadAdjustedTrendText).toContain(
      "höheren durchschnittlichen Bike-Leistung",
    );
    expect(presentation?.loadAdjustedTrendText).toContain(
      "Belastung war also nicht vergleichbar",
    );
    expect(presentation?.loadAdjustedTrendText).toContain(
      "Leistungsänderung: +18 %",
    );
  });

  it("describes the remaining load-adjusted states without turning them into prescriptions", () => {
    const cases = [
      [
        "higher_at_similar_power",
        "höher, obwohl die durchschnittliche Bike-Leistung ähnlich blieb",
      ],
      [
        "stable_at_similar_power",
        "Bike-Leistung blieben über die vergleichbaren Einheiten weitgehend stabil",
      ],
      [
        "load_changed",
        "Bike-Leistung hat sich zwischen älteren und neueren Einheiten deutlich verändert",
      ],
    ] as const;

    for (const [loadAdjustedTrend, expectedText] of cases) {
      const presentation = heartRateHistoryPresentation(
        history({ loadAdjustedTrend }),
      );

      expect(presentation?.loadAdjustedTrendText).toContain(expectedText);
      expect(presentation?.loadAdjustedTrendText).toContain(
        "verändert die Trainingsintensität nicht automatisch",
      );
    }
  });

  it("omits trend paragraphs independently when their data is insufficient", () => {
    const presentation = heartRateHistoryPresentation(
      history({
        responseTrend: "insufficient_data",
        targetPositionChangePoints: null,
        loadAdjustedTrend: "insufficient_data",
        medianPowerW: null,
        powerChangePercent: null,
      }),
    );

    expect(presentation?.responseTrendText).toBeNull();
    expect(presentation?.loadAdjustedTrendText).toBeNull();
  });
});
