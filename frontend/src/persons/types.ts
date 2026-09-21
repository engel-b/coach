/**
 * Eine für den Health Coach auswählbare Person.
 *
 * Die ID ist die technische, stabile Identität.
 * displayName ist ausschließlich für die Darstellung gedacht.
 */
export interface Person {
  id: number;
  displayName: string;
}

export type TrainingGoal =
  "general_fitness" | "muscle_gain" | "weight_loss" | "endurance";

export interface PersonProfile {
  personId: number;
  displayName: string;
  dateOfBirth: string;
  heightCm: number;
  trainingGoal: TrainingGoal;
  maxHeartRateBpm: number | null;
  restingHeartRateBpm: number | null;
  startWeightKg: number | null;
  targetWeightKg: number | null;
}

export interface UpdatePersonProfileRequest {
  displayName: string;
  dateOfBirth: string;
  heightCm: number;
  trainingGoal: TrainingGoal;
  maxHeartRateBpm: number | null;
  restingHeartRateBpm: number | null;
  startWeightKg: number | null;
  targetWeightKg: number | null;
}
