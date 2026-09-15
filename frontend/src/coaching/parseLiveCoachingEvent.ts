import type {
  CoachingAction,
  HeartRateCoachingEvent,
  HeartRateZoneStatus,
  LiveCoachingEvent,
  WorkoutPhaseType,
} from "./types";

const COACHING_ACTIONS: readonly CoachingAction[] = [
  "increase_intensity",
  "reduce_intensity",
];

const WORKOUT_PHASE_TYPES: readonly WorkoutPhaseType[] = [
  "warm_up",
  "main",
  "cool_down",
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

  if (
    value.type === "coaching.phase_started" &&
    typeof value.timestamp === "string" &&
    typeof value.workoutId === "string" &&
    Number.isInteger(value.phaseIndex) &&
    (value.phaseIndex as number) >= 0 &&
    isWorkoutPhaseType(value.phaseType) &&
    isFiniteNumber(value.durationMinutes) &&
    value.durationMinutes > 0 &&
    isFiniteNumber(value.targetMinBpm) &&
    isFiniteNumber(value.targetMaxBpm) &&
    typeof value.isFinalPhase === "boolean"
  ) {
    return {
      type: "coaching.phase_started",
      timestamp: value.timestamp,
      workoutId: value.workoutId,
      phaseIndex: value.phaseIndex as number,
      phaseType: value.phaseType,
      durationMinutes: value.durationMinutes,
      targetMinBpm: value.targetMinBpm,
      targetMaxBpm: value.targetMaxBpm,
      isFinalPhase: value.isFinalPhase,
    };
  }

  if (
    value.type === "coaching.phase_ending" &&
    typeof value.timestamp === "string" &&
    typeof value.workoutId === "string" &&
    Number.isInteger(value.phaseIndex) &&
    (value.phaseIndex as number) >= 0 &&
    isWorkoutPhaseType(value.phaseType) &&
    isFiniteNumber(value.remainingSeconds) &&
    value.remainingSeconds > 0
  ) {
    return {
      type: "coaching.phase_ending",
      timestamp: value.timestamp,
      workoutId: value.workoutId,
      phaseIndex: value.phaseIndex as number,
      phaseType: value.phaseType,
      remainingSeconds: value.remainingSeconds,
    };
  }

  if (
    value.type === "coaching.workout_halfway" &&
    typeof value.timestamp === "string" &&
    typeof value.workoutId === "string" &&
    isFiniteNumber(value.totalDurationMinutes) &&
    value.totalDurationMinutes > 0
  ) {
    return {
      type: "coaching.workout_halfway",
      timestamp: value.timestamp,
      workoutId: value.workoutId,
      totalDurationMinutes: value.totalDurationMinutes,
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

function isWorkoutPhaseType(value: unknown): value is WorkoutPhaseType {
  return (
    typeof value === "string" &&
    WORKOUT_PHASE_TYPES.includes(value as WorkoutPhaseType)
  );
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
