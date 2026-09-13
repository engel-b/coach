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
