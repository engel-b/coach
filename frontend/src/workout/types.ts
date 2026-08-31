export type WorkoutStatus =
  | 'running'
  | 'completed'
  | 'aborted'

export interface WorkoutPhase {
  phaseType: 'warm_up' | 'main' | 'cool_down'
  durationMinutes: number
  targetHeartRateMin: number
  targetHeartRateMax: number
}

export interface Workout {
  id: string
  personId: number
  startedAt: string
  status: WorkoutStatus
  totalDurationMinutes: number
  elapsedSeconds: number
  completedAt: string | null
  phases: WorkoutPhase[]
}
