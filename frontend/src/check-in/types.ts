export interface CheckInRequest {
  energy: number;
  recovery: number;
  muscleSoreness: number;
  stress: number;
  availableTrainingMinutes: number;
}

export interface CheckIn extends CheckInRequest {
  personId: number;
  timestamp: string;
}
