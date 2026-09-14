export type WorkoutType = "recovery" | "base_endurance" | "moderate";

export type WorkoutPhaseType = "warm_up" | "main" | "cool_down";

export interface WorkoutPhase {
  phaseType: WorkoutPhaseType;
  durationMinutes: number;
  targetHeartRateMin: number;
  targetHeartRateMax: number;
}

export interface TrainingRecommendation {
  workoutType: WorkoutType;
  totalDurationMinutes: number;
  reason: string;
  reasonCodes: string[];
  phases: WorkoutPhase[];
}
