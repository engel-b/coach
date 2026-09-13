import type {
  CoachingAction,
  HeartRateZoneStatus,
  LiveCoachingEvent,
} from "./types";

const COACHING_DECISION = "coaching.decision";

const COACHING_ACTIONS: readonly CoachingAction[] = [
  "increase_intensity",
  "reduce_intensity",
];

const HEART_RATE_ZONE_STATUSES: readonly HeartRateZoneStatus[] = [
  "below_target",
  "in_target",
  "above_target",
];

/**
 * Validiert eine Nachricht an der WebSocket-Systemgrenze.
 *
 * JSON.parse() liefert nur unknown. Erst nach dieser Prüfung darf
 * die Nachricht als LiveCoachingEvent in die Anwendung gelangen.
 */
export function parseLiveCoachingEvent(
  value: unknown,
): LiveCoachingEvent | null {
  if (!isRecord(value) || value.type !== COACHING_DECISION) {
    return null;
  }

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
    type: COACHING_DECISION,
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
