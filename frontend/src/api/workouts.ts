import type { Workout } from '../workout/types'
import type { WorkoutSummary } from '../workout/summary-types'

export async function startWorkout(
  personId: number,
): Promise<Workout> {
  const response = await fetch(
    `/api/persons/${personId}/workouts`,
    {
      method: 'POST',
    },
  )

  if (!response.ok) {
    throw new Error(
      `Could not start workout: HTTP ${response.status}`,
    )
  }

  return (await response.json()) as Workout
}


export async function completeWorkout(
  workoutId: string,
  elapsedSeconds: number,
): Promise<Workout> {
  const response = await fetch(
    `/api/workouts/${workoutId}/complete`,
    {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        elapsedSeconds,
      }),
    },
  )

  if (!response.ok) {
    throw new Error(
      `Could not complete workout: HTTP ${response.status}`,
    )
  }

  return (await response.json()) as Workout
}


export async function abortWorkout(
  workoutId: string,
  elapsedSeconds: number,
): Promise<Workout> {
  const response = await fetch(
    `/api/workouts/${workoutId}/abort`,
    {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        elapsedSeconds,
      }),
    },
  )

  if (!response.ok) {
    throw new Error(
      `Could not abort workout: HTTP ${response.status}`,
    )
  }

  return (await response.json()) as Workout
}

export async function getWorkoutHistory(
  personId: number,
  limit = 20,
): Promise<Workout[]> {
  const response = await fetch(
    `/api/persons/${personId}/workouts?limit=${limit}`,
  )

  if (!response.ok) {
    throw new Error(
      `Could not load workout history: HTTP ${response.status}`,
    )
  }

  return (await response.json()) as Workout[]
}

export async function getWorkoutSummary(
  workoutId: string,
): Promise<WorkoutSummary> {
  const response = await fetch(
    `/api/workouts/${workoutId}/summary`,
  )

  if (!response.ok) {
    throw new Error(
      `Could not load workout summary: HTTP ${response.status}`,
    )
  }

  return (await response.json()) as WorkoutSummary
}
