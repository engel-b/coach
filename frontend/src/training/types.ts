export type WorkoutType = "recovery" | "base_endurance" | "moderate";

export type WorkoutPhaseType = "warm_up" | "main" | "cool_down";

export interface WorkoutPhase {
  phaseType: WorkoutPhaseType;
  durationMinutes: number;
  targetHeartRateMin: number;
  targetHeartRateMax: number;
}

export type WeightGoalStatus =
  | "no_goal"
  | "no_current_weight"
  | "above_target"
  | "at_target"
  | "below_target";

export interface WeightGoalProgress {
  status: WeightGoalStatus;
  startWeightKg: number | null;
  currentWeightKg: number | null;
  targetWeightKg: number | null;
  remainingKg: number | null;
  lostSinceStartKg: number | null;
  progressPercent: number | null;
}

export type HeartRateTargetMethod =
  "heart_rate_reserve" | "max_heart_rate_percentage";

export type HeartRateTargetSource = "profile" | "check_in_baseline";

export interface HeartRateTargetBasis {
  method: HeartRateTargetMethod;
  maxHeartRateBpm: number;
  restingHeartRateBpm: number | null;
  referenceRestingHeartRateBpm: number | null;
  restingHeartRateSource: HeartRateTargetSource | null;
  restingHeartRateSampleCount: number;
}

export type HeartRateHistoryStatus =
  | "insufficient_data"
  | "mostly_in_target"
  | "mostly_above_target"
  | "mostly_below_target"
  | "mixed";

export type HeartRateResponseTrend =
  "insufficient_data" | "lower" | "stable" | "higher";

export interface HeartRateHistory {
  status: HeartRateHistoryStatus;
  workoutCount: number;
  workoutType: WorkoutType | null;
  medianInTargetPercent: number | null;
  medianAboveTargetPercent: number | null;
  medianBelowTargetPercent: number | null;
  maxDurationMinutes: number | null;
  responseTrend: HeartRateResponseTrend;
  medianTargetPositionPercent: number | null;
  targetPositionChangePoints: number | null;
}

export interface TrainingRecommendation {
  workoutType: WorkoutType;
  totalDurationMinutes: number;
  reason: string;
  heartRateTargetBasis: HeartRateTargetBasis;
  heartRateHistory: HeartRateHistory | null;
  reasonCodes: string[];
  weightGoalProgress: WeightGoalProgress | null;
  phases: WorkoutPhase[];
}
