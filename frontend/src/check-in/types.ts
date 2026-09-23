export interface CheckInRequest {
  energy: number;
  recovery: number;
  muscleSoreness: number;
  stress: number;
  availableTrainingMinutes: number;
  currentWeightKg: number | null;
  sleepHours: number | null;
  steps: number | null;
  restingHeartRateBpm: number | null;
}

export interface CheckIn extends CheckInRequest {
  personId: number;
  timestamp: string;
}
