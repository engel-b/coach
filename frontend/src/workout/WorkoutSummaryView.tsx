import { useEffect, useState } from 'react'

import { getWorkoutSummary } from '../api/workouts'
import type { Person } from '../persons/types'
import type { Workout } from './types'
import type { WorkoutSummary } from './summary-types'


interface WorkoutSummaryViewProps {
  person: Person
  workout: Workout
  onDone: () => void
}


function formatDuration(
  totalSeconds: number,
): string {
  const minutes = Math.floor(
    totalSeconds / 60,
  )

  const seconds =
    totalSeconds % 60

  return `${String(minutes).padStart(2, '0')}:${String(
    seconds,
  ).padStart(2, '0')}`
}


export function WorkoutSummaryView({
  person,
  workout,
  onDone,
}: WorkoutSummaryViewProps) {
  const [summary, setSummary] =
    useState<WorkoutSummary | null>(null)

  const [loading, setLoading] =
    useState(true)

  const [error, setError] =
    useState<string | null>(null)

  useEffect(() => {
    async function loadSummary(): Promise<void> {
      try {
        setLoading(true)

        const result =
          await getWorkoutSummary(
            workout.id,
          )

        setSummary(result)
        setError(null)
      } catch (loadError) {
        const message =
          loadError instanceof Error
            ? loadError.message
            : 'Unknown error'

        setError(message)
      } finally {
        setLoading(false)
      }
    }

    void loadSummary()
  }, [workout.id])

  if (loading) {
    return (
      <section className="completion-view">
        <div className="loading-state">
          Training wird ausgewertet …
        </div>
      </section>
    )
  }

  if (
    error !== null ||
    summary === null
  ) {
    return (
      <section className="completion-view">
        <div className="error-message">
          {error ?? 'Auswertung nicht verfügbar.'}
        </div>

        <button
          type="button"
          className="primary-action"
          onClick={onDone}
        >
          Zur Übersicht
        </button>
      </section>
    )
  }

  const completed =
    summary.status === 'completed'

  return (
    <section className="completion-view">
      <div className="eyebrow">
        {completed
          ? 'TRAINING ABGESCHLOSSEN'
          : 'TRAINING BEENDET'}
      </div>

      <h1>
        {completed
          ? `Geschafft, ${person.displayName}.`
          : 'Training beendet.'}
      </h1>

      <div className="workout-summary">
        <div className="workout-summary-row">
          <span>Geplant</span>

          <strong>
            {formatDuration(
              summary.plannedSeconds,
            )}
          </strong>
        </div>

        <div className="workout-summary-row">
          <span>Trainiert</span>

          <strong>
            {formatDuration(
              summary.elapsedSeconds,
            )}
          </strong>
        </div>

        <div className="workout-summary-row">
          <span>Erfüllung</span>

          <strong>
            {summary.completionPercent} %
          </strong>
        </div>
      </div>

      <button
        type="button"
        className="primary-action"
        onClick={onDone}
      >
        Zur Übersicht
      </button>
    </section>
  )
}

