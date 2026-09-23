export interface WorkoutHeartRateSummary {
  sampleCount: number;
  averageBpm: number;
  maxBpm: number;
  belowTargetPercent: number;
  inTargetPercent: number;
  aboveTargetPercent: number;
}

export interface WorkoutSummary {
  plannedSeconds: number;
  elapsedSeconds: number;
  distanceM: number;
  completionPercent: number;
  status: "running" | "completed" | "aborted";
  heartRateSummary: WorkoutHeartRateSummary | null;
}
