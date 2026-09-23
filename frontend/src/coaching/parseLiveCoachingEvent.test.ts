import { describe, expect, it } from "vitest";

import { parseLiveCoachingEvent } from "./parseLiveCoachingEvent";

const validEvent = {
  type: "coaching.decision",
  timestamp: "2026-09-13T08:30:00Z",
  workoutId: "workout-1",
  deviceId: "heart-rate-1",
  action: "reduce_intensity",
  zoneStatus: "above_target",
  heartRateBpm: 149,
  targetMinBpm: 125,
  targetMaxBpm: 145,
  outsideTargetSeconds: 21,
  deviationBpm: 4,
  deviationSeverity: "moderate",
  reason: "heart_rate_above_target_long_enough",
};

describe("parseLiveCoachingEvent", () => {
  it("accepts a valid coaching decision", () => {
    expect(parseLiveCoachingEvent(validEvent)).toEqual(validEvent);
  });

  it("rejects an unknown event type", () => {
    expect(
      parseLiveCoachingEvent({
        ...validEvent,
        type: "coaching.unknown",
      }),
    ).toBeNull();
  });

  it("rejects an unknown coaching action", () => {
    expect(
      parseLiveCoachingEvent({
        ...validEvent,
        action: "go_faster_now",
      }),
    ).toBeNull();
  });

  it("rejects a negative deviation duration", () => {
    expect(
      parseLiveCoachingEvent({
        ...validEvent,
        outsideTargetSeconds: -1,
      }),
    ).toBeNull();
  });

  it("rejects malformed values", () => {
    expect(parseLiveCoachingEvent(null)).toBeNull();
    expect(parseLiveCoachingEvent({ type: "coaching.decision" })).toBeNull();
    expect(
      parseLiveCoachingEvent({
        ...validEvent,
        heartRateBpm: "149",
      }),
    ).toBeNull();
  });
});

it("accepts pause and resume coaching events", () => {
  expect(
    parseLiveCoachingEvent({
      type: "coaching.pause_started",
      timestamp: "2026-09-13T08:30:00Z",
      workoutId: "workout-1",
    }),
  ).toEqual({
    type: "coaching.pause_started",
    timestamp: "2026-09-13T08:30:00Z",
    workoutId: "workout-1",
  });

  expect(
    parseLiveCoachingEvent({
      type: "coaching.pause_ended",
      timestamp: "2026-09-13T08:31:00Z",
      workoutId: "workout-1",
    }),
  ).not.toBeNull();
});

it("accepts phase-started coaching events", () => {
  const event = {
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

  expect(parseLiveCoachingEvent(event)).toEqual(event);
});

it("parses workout structure milestone events", () => {
  const halfway = {
    type: "coaching.workout_halfway",
    timestamp: "2026-09-13T08:45:00Z",
    workoutId: "workout-1",
    totalDurationMinutes: 30,
  };
  expect(parseLiveCoachingEvent(halfway)).toEqual(halfway);

  const ending = {
    type: "coaching.phase_ending",
    timestamp: "2026-09-13T08:34:00Z",
    workoutId: "workout-1",
    phaseIndex: 0,
    phaseType: "warm_up",
    remainingSeconds: 60,
  };
  expect(parseLiveCoachingEvent(ending)).toEqual(ending);
});
