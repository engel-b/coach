import { describe, expect, it } from "vitest";

import { coachingMessage } from "./coachingMessage";
import type {
  CoachingAction,
  HeartRateCoachingEvent,
  LiveCoachingEvent,
} from "./types";

function event(
  action: CoachingAction,
  outsideTargetSeconds = 21,
): HeartRateCoachingEvent {
  return {
    type: "coaching.decision",
    timestamp: "2026-09-13T08:30:00Z",
    workoutId: "workout-1",
    deviceId: "heart-rate-1",
    action,
    zoneStatus: action === "reduce_intensity" ? "above_target" : "below_target",
    heartRateBpm: action === "reduce_intensity" ? 149 : 119,
    targetMinBpm: 125,
    targetMaxBpm: 145,
    outsideTargetSeconds,
    reason: "test",
  };
}

describe("coachingMessage", () => {
  it("formats heart-rate decisions", () => {
    expect(coachingMessage(event("reduce_intensity"))).toBe(
      "Dein Puls liegt seit 21 s über dem Zielbereich. Nimm etwas Tempo heraus.",
    );
    expect(coachingMessage(event("increase_intensity", 20.6))).toBe(
      "Dein Puls liegt seit 21 s unter dem Zielbereich. Erhöhe die Intensität etwas.",
    );
  });

  it("formats pause and resume events", () => {
    const pause: LiveCoachingEvent = {
      type: "coaching.pause_started",
      timestamp: "2026-09-13T08:30:00Z",
      workoutId: "workout-1",
    };
    const resume: LiveCoachingEvent = {
      type: "coaching.pause_ended",
      timestamp: "2026-09-13T08:31:00Z",
      workoutId: "workout-1",
    };

    expect(coachingMessage(pause)).toBe("Pause");
    expect(coachingMessage(resume)).toBe("Weiter geht's");
  });
});
