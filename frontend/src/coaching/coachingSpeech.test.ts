import { describe, expect, it } from "vitest";

import {
  coachingSpeechMessage,
  evaluateCoachingSpeech,
  type CoachingSpeechState,
} from "./coachingSpeech";
import type {
  CoachingAction,
  HeartRateCoachingEvent,
  LiveCoachingEvent,
} from "./types";

function decisionEvent(action: CoachingAction): HeartRateCoachingEvent {
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
    outsideTargetSeconds: 21,
    reason: "test",
  };
}

const emptyState: CoachingSpeechState = {
  lastDecisionAction: null,
  lastSpokenAtMs: null,
};

describe("coachingSpeechMessage", () => {
  it("formats heart-rate messages", () => {
    expect(coachingSpeechMessage(decisionEvent("reduce_intensity"))).toBe(
      "Dein Puls ist über dem Zielbereich. Nimm etwas Tempo heraus.",
    );
    expect(coachingSpeechMessage(decisionEvent("increase_intensity"))).toBe(
      "Dein Puls ist unter dem Zielbereich. Erhöhe die Intensität etwas.",
    );
  });

  it("formats pause and resume messages", () => {
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

    expect(coachingSpeechMessage(pause)).toBe("Pause.");
    expect(coachingSpeechMessage(resume)).toBe("Weiter geht's.");
  });

  it("formats phase-started messages", () => {
    const phaseStarted: LiveCoachingEvent = {
      type: "coaching.phase_started",
      timestamp: "2026-09-13T08:35:00Z",
      workoutId: "workout-1",
      phaseIndex: 1,
      phaseType: "main",
      durationMinutes: 20,
      targetMinBpm: 125,
      targetMaxBpm: 145,
      isFinalPhase: false,
    };

    expect(coachingSpeechMessage(phaseStarted)).toBe(
      "Jetzt beginnt die Hauptphase. Fahr gleichmäßig und bleib im Zielbereich.",
    );
  });
});

describe("evaluateCoachingSpeech", () => {
  it("speaks the first heart-rate event", () => {
    const result = evaluateCoachingSpeech(
      decisionEvent("reduce_intensity"),
      emptyState,
      1_000,
    );

    expect(result.speak).toBe(true);
    expect(result.nextState).toEqual({
      lastDecisionAction: "reduce_intensity",
      lastSpokenAtMs: 1_000,
    });
  });

  it("suppresses the same heart-rate action during the repeat cooldown", () => {
    const state: CoachingSpeechState = {
      lastDecisionAction: "reduce_intensity",
      lastSpokenAtMs: 1_000,
    };

    const result = evaluateCoachingSpeech(
      decisionEvent("reduce_intensity"),
      state,
      30_000,
    );

    expect(result.speak).toBe(false);
    expect(result.nextState).toBe(state);
  });

  it("always speaks phase changes immediately", () => {
    const state: CoachingSpeechState = {
      lastDecisionAction: "reduce_intensity",
      lastSpokenAtMs: 1_000,
    };
    const phaseStarted: LiveCoachingEvent = {
      type: "coaching.phase_started",
      timestamp: "2026-09-13T08:35:00Z",
      workoutId: "workout-1",
      phaseIndex: 1,
      phaseType: "main",
      durationMinutes: 20,
      targetMinBpm: 125,
      targetMaxBpm: 145,
      isFinalPhase: false,
    };

    const result = evaluateCoachingSpeech(phaseStarted, state, 1_100);

    expect(result.speak).toBe(true);
    expect(result.nextState.lastDecisionAction).toBeNull();
  });

  it("always speaks pause and resume runtime events", () => {
    const state: CoachingSpeechState = {
      lastDecisionAction: "reduce_intensity",
      lastSpokenAtMs: 1_000,
    };
    const pause: LiveCoachingEvent = {
      type: "coaching.pause_started",
      timestamp: "2026-09-13T08:30:00Z",
      workoutId: "workout-1",
    };

    const result = evaluateCoachingSpeech(pause, state, 1_100);

    expect(result.speak).toBe(true);
    expect(result.nextState.lastDecisionAction).toBeNull();
  });
});

it("speaks workout structure milestones immediately", () => {
  expect(
    coachingSpeechMessage({
      type: "coaching.workout_halfway",
      timestamp: "2026-09-13T08:45:00Z",
      workoutId: "workout-1",
      totalDurationMinutes: 30,
    }),
  ).toBe("Halbzeit. Die Hälfte ist geschafft. Halte deinen Rhythmus.");

  expect(
    coachingSpeechMessage({
      type: "coaching.phase_ending",
      timestamp: "2026-09-13T08:34:00Z",
      workoutId: "workout-1",
      phaseIndex: 0,
      phaseType: "warm_up",
      remainingSeconds: 60,
    }),
  ).toBe("Noch eine Minute in dieser Phase.");
});
