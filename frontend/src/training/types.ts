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

export type LoadAdjustedHeartRateTrend =
  | "insufficient_data"
  | "lower_at_similar_power"
  | "higher_at_similar_power"
  | "stable_at_similar_power"
  | "lower_with_lower_power"
  | "higher_with_higher_power"
  | "load_changed";

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
  loadAdjustedTrend: LoadAdjustedHeartRateTrend;
  medianPowerW: number | null;
  medianCadenceRpm: number | null;
  powerChangePercent: number | null;
}

export type LoadResponseStatus =
  | "insufficient_data"
  | "stable"
  | "lower_hr_at_similar_load"
  | "higher_hr_at_similar_load"
  | "lower_load"
  | "higher_load"
  | "mixed";

export interface LoadResponse {
  status: LoadResponseStatus;
  workoutType: WorkoutType;
  comparableWorkoutCount: number;
  heartRateTrend: HeartRateResponseTrend;
  loadAdjustedHeartRateTrend: LoadAdjustedHeartRateTrend;
  medianPowerW: number | null;
  medianCadenceRpm: number | null;
  readinessCaution: boolean;
}

export type AdaptiveWorkoutAction =
  | "keep_plan"
  | "reduce_duration"
  | "reduce_intensity"
  | "extend_warmup"
  | "prefer_recovery";

export interface AdaptiveWorkoutAdvice {
  action: AdaptiveWorkoutAction;
  reasonCodes: string[];
  planReflectsAdvice: boolean;
  recommendedDurationMinutes: number | null;
}

export interface TrainingRecommendation {
  workoutType: WorkoutType;
  totalDurationMinutes: number;
  reason: string;
  heartRateTargetBasis: HeartRateTargetBasis;
  heartRateHistory: HeartRateHistory | null;
  loadResponse: LoadResponse | null;
  adaptiveWorkoutAdvice: AdaptiveWorkoutAdvice | null;
  reasonCodes: string[];
  weightGoalProgress: WeightGoalProgress | null;
  phases: WorkoutPhase[];
}
