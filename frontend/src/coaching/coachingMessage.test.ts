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
    deviationBpm: 4,
    deviationSeverity: "moderate",
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

  it("formats phase changes", () => {
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

    expect(coachingMessage(phaseStarted)).toBe(
      "Hauptphase: 20 Minuten gleichmäßig im Zielbereich fahren.",
    );
  });
});

it("shows halfway and phase-ending coaching messages", () => {
  expect(
    coachingMessage({
      type: "coaching.workout_halfway",
      timestamp: "2026-09-13T08:45:00Z",
      workoutId: "workout-1",
      totalDurationMinutes: 30,
    }),
  ).toBe("Halbzeit – die Hälfte des Workouts ist geschafft.");

  expect(
    coachingMessage({
      type: "coaching.phase_ending",
      timestamp: "2026-09-13T08:34:00Z",
      workoutId: "workout-1",
      phaseIndex: 0,
      phaseType: "warm_up",
      remainingSeconds: 60,
    }),
  ).toBe("Noch eine Minute in der Aufwärmphase.");
});

it("marks the last phase explicitly", () => {
  expect(
    coachingMessage({
      type: "coaching.phase_started",
      timestamp: "2026-09-13T08:55:00Z",
      workoutId: "workout-1",
      phaseIndex: 2,
      phaseType: "cool_down",
      durationMinutes: 5,
      targetMinBpm: 95,
      targetMaxBpm: 115,
      isFinalPhase: true,
    }),
  ).toBe("Letzte Phase: Cooldown-Phase für 5 Minuten.");
});
