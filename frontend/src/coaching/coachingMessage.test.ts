import { describe, expect, it } from "vitest";

import { coachingMessage } from "./coachingMessage";
import type { LiveCoachingEvent } from "./types";

function event(
  action: LiveCoachingEvent["action"],
  outsideTargetSeconds = 21,
): LiveCoachingEvent {
  return {
    type: "coaching.decision",
    timestamp: "2026-09-13T08:30:00Z",
    workoutId: "workout-1",
    deviceId: "heart-rate-1",
    action,
    zoneStatus:
      action === "reduce_intensity" ? "above_target" : "below_target",
    heartRateBpm: action === "reduce_intensity" ? 149 : 119,
    targetMinBpm: 125,
    targetMaxBpm: 145,
    outsideTargetSeconds,
    reason: "test",
  };
}

describe("coachingMessage", () => {
  it("formats a reduce-intensity decision", () => {
    expect(coachingMessage(event("reduce_intensity"))).toBe(
      "Dein Puls liegt seit 21 s über dem Zielbereich. Nimm etwas Tempo heraus.",
    );
  });

  it("formats an increase-intensity decision", () => {
    expect(coachingMessage(event("increase_intensity", 20.6))).toBe(
      "Dein Puls liegt seit 21 s unter dem Zielbereich. Erhöhe die Intensität etwas.",
    );
  });
});
