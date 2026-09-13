import type {
  CoachingAction,
  HeartRateCoachingEvent,
  HeartRateZoneStatus,
  LiveCoachingEvent,
} from "./types";

const COACHING_ACTIONS: readonly CoachingAction[] = [
  "increase_intensity",
  "reduce_intensity",
];

const HEART_RATE_ZONE_STATUSES: readonly HeartRateZoneStatus[] = [
  "below_target",
  "in_target",
  "above_target",
];

export function parseLiveCoachingEvent(
  value: unknown,
): LiveCoachingEvent | null {
  if (!isRecord(value)) {
    return null;
  }

  if (
    (value.type === "coaching.pause_started" ||
      value.type === "coaching.pause_ended") &&
    typeof value.timestamp === "string" &&
    typeof value.workoutId === "string"
  ) {
    return {
      type: value.type,
      timestamp: value.timestamp,
      workoutId: value.workoutId,
    };
  }

  if (value.type !== "coaching.decision") {
    return null;
  }

  return parseHeartRateDecision(value);
}

function parseHeartRateDecision(
  value: Record<string, unknown>,
): HeartRateCoachingEvent | null {
  if (
    typeof value.timestamp !== "string" ||
    typeof value.workoutId !== "string" ||
    typeof value.deviceId !== "string" ||
    !isCoachingAction(value.action) ||
    !isHeartRateZoneStatus(value.zoneStatus) ||
    !isFiniteNumber(value.heartRateBpm) ||
    !isFiniteNumber(value.targetMinBpm) ||
    !isFiniteNumber(value.targetMaxBpm) ||
    !isFiniteNumber(value.outsideTargetSeconds) ||
    value.outsideTargetSeconds < 0 ||
    typeof value.reason !== "string"
  ) {
    return null;
  }

  return {
    type: "coaching.decision",
    timestamp: value.timestamp,
    workoutId: value.workoutId,
    deviceId: value.deviceId,
    action: value.action,
    zoneStatus: value.zoneStatus,
    heartRateBpm: value.heartRateBpm,
    targetMinBpm: value.targetMinBpm,
    targetMaxBpm: value.targetMaxBpm,
    outsideTargetSeconds: value.outsideTargetSeconds,
    reason: value.reason,
  };
}

function isCoachingAction(value: unknown): value is CoachingAction {
  return (
    typeof value === "string" &&
    COACHING_ACTIONS.includes(value as CoachingAction)
  );
}

function isHeartRateZoneStatus(value: unknown): value is HeartRateZoneStatus {
  return (
    typeof value === "string" &&
    HEART_RATE_ZONE_STATUSES.includes(value as HeartRateZoneStatus)
  );
}

function isFiniteNumber(value: unknown): value is number {
  return typeof value === "number" && Number.isFinite(value);
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}
