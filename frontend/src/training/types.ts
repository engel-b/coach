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

export interface TrainingRecommendation {
  workoutType: WorkoutType;
  totalDurationMinutes: number;
  reason: string;
  reasonCodes: string[];
  weightGoalProgress: WeightGoalProgress | null;
  phases: WorkoutPhase[];
}
