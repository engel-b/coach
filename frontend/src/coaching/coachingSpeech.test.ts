import { describe, expect, it } from "vitest";

import {
  coachingSpeechMessage,
  evaluateCoachingSpeech,
  type CoachingSpeechState,
} from "./coachingSpeech";
import type { LiveCoachingEvent } from "./types";

function event(action: LiveCoachingEvent["action"]): LiveCoachingEvent {
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
    outsideTargetSeconds: 21,
    reason: "test",
  };
}

const emptyState: CoachingSpeechState = {
  lastAction: null,
  lastSpokenAtMs: null,
};

describe("coachingSpeechMessage", () => {
  it("formats a short reduce-intensity message", () => {
    expect(coachingSpeechMessage(event("reduce_intensity"))).toBe(
      "Dein Puls ist über dem Zielbereich. Nimm etwas Tempo heraus.",
    );
  });

  it("formats a short increase-intensity message", () => {
    expect(coachingSpeechMessage(event("increase_intensity"))).toBe(
      "Dein Puls ist unter dem Zielbereich. Erhöhe die Intensität etwas.",
    );
  });
});

describe("evaluateCoachingSpeech", () => {
  it("speaks the first coaching event", () => {
    const decision = evaluateCoachingSpeech(
      event("reduce_intensity"),
      emptyState,
      1_000,
    );

    expect(decision.speak).toBe(true);
    expect(decision.nextState).toEqual({
      lastAction: "reduce_intensity",
      lastSpokenAtMs: 1_000,
    });
  });

  it("suppresses the same action during the repeat cooldown", () => {
    const state: CoachingSpeechState = {
      lastAction: "reduce_intensity",
      lastSpokenAtMs: 1_000,
    };

    const decision = evaluateCoachingSpeech(
      event("reduce_intensity"),
      state,
      30_000,
    );

    expect(decision.speak).toBe(false);
    expect(decision.nextState).toBe(state);
  });

  it("allows the same action after the repeat cooldown", () => {
    const state: CoachingSpeechState = {
      lastAction: "reduce_intensity",
      lastSpokenAtMs: 1_000,
    };

    const decision = evaluateCoachingSpeech(
      event("reduce_intensity"),
      state,
      61_000,
    );

    expect(decision.speak).toBe(true);
  });

  it("speaks an action change immediately", () => {
    const state: CoachingSpeechState = {
      lastAction: "reduce_intensity",
      lastSpokenAtMs: 10_000,
    };

    const decision = evaluateCoachingSpeech(
      event("increase_intensity"),
      state,
      11_000,
    );

    expect(decision.speak).toBe(true);
    expect(decision.nextState.lastAction).toBe("increase_intensity");
  });
});
