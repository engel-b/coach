export interface WorkoutHeartRateSummary {
  sampleCount: number;
  averageBpm: number;
  maxBpm: number;
  belowTargetPercent: number;
  inTargetPercent: number;
  aboveTargetPercent: number;
}

export interface WorkoutBikeSummary {
  powerSampleCount: number;
  averagePowerW: number | null;
  cadenceSampleCount: number;
  averageCadenceRpm: number | null;
}

export interface WorkoutSummary {
  plannedSeconds: number;
  elapsedSeconds: number;
  distanceM: number;
  completionPercent: number;
  status: "running" | "completed" | "aborted";
  heartRateSummary: WorkoutHeartRateSummary | null;
  bikeSummary: WorkoutBikeSummary | null;
}
