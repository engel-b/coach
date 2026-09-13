export type CoachingAction = "increase_intensity" | "reduce_intensity";

export type HeartRateZoneStatus =
  | "below_target"
  | "in_target"
  | "above_target";

export interface LiveCoachingEvent {
  type: "coaching.decision";
  timestamp: string;
  workoutId: string;
  deviceId: string;
  action: CoachingAction;
  zoneStatus: HeartRateZoneStatus;
  heartRateBpm: number;
  targetMinBpm: number;
  targetMaxBpm: number;
  outsideTargetSeconds: number;
  reason: string;
}
