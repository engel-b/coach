export interface WorkoutSummary {
  plannedSeconds: number
  elapsedSeconds: number
  completionPercent: number
  status: 'running' | 'completed' | 'aborted'
}

