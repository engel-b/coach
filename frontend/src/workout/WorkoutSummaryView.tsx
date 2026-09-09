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

function formatDuration(totalSeconds: number): string {
  const minutes = Math.floor(totalSeconds / 60)
  const seconds = Math.floor(totalSeconds % 60)
  return `${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`
}

function formatDistance(meters: number): string {
  return (meters / 1000).toLocaleString('de-DE', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })
}

export function WorkoutSummaryView({
  person,
  workout,
  onDone,
}: WorkoutSummaryViewProps) {
  const [summary, setSummary] = useState<WorkoutSummary | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false

    async function loadSummary(): Promise<void> {
      try {
        setLoading(true)
        setError(null)
        const result = await getWorkoutSummary(workout.id)
        if (!cancelled) setSummary(result)
      } catch (loadError) {
        if (!cancelled) {
          setError(
            loadError instanceof Error
              ? loadError.message
              : 'Die Auswertung konnte nicht geladen werden.',
          )
        }
      } finally {
        if (!cancelled) setLoading(false)
      }
    }

    void loadSummary()
    return () => { cancelled = true }
  }, [workout.id])

  const completed = summary?.status === 'completed'
  const status = completed ? 'Abgeschlossen' : 'Abgebrochen'
  const elapsed = summary?.elapsedSeconds ?? workout.elapsedSeconds
  const planned = summary?.plannedSeconds ?? workout.totalDurationMinutes * 60
  const percent = summary?.completionPercent ?? 0

  return (
    <section className="person-dashboard completion-dashboard">
      <header className="dashboard-header">
        <div>
          <div className="eyebrow">DIGITAL FITNESS COACH</div>
          <h1>{loading ? 'Training wird ausgewertet …' : completed ? 'Workout abgeschlossen' : 'Training beendet'}</h1>
          <p>Deine Trainingszusammenfassung, {person.displayName}.</p>
        </div>
        <div className="dashboard-header-actions">
          <button type="button" className="secondary-action" onClick={onDone}>
            Zur Übersicht
          </button>
        </div>
      </header>

      {error !== null && (
        <div className="error-message" role="alert">{error}</div>
      )}

      <div className="dashboard-main-grid">
        <section className="dashboard-card">
          <div className="dashboard-card-header">
            <div>
              <div className="dashboard-section-label">DEIN WORKOUT</div>
              <h2>Radtraining</h2>
            </div>
            <span className={`dashboard-workout-status ${completed ? 'completed' : 'aborted'}`}>
              {loading ? 'Wird geladen' : status}
            </span>
          </div>
          <div className="completion-duration">
            <strong>{formatDuration(elapsed)}</strong>
            <span>Trainierte Zeit</span>
          </div>
          <div className="completion-progress">
            <div className="completion-progress-label">
              <span>Erfüllung der geplanten Dauer</span>
              <strong>{loading ? '–' : `${percent} %`}</strong>
            </div>
            <div className="completion-progress-track">
              <div style={{ width: `${Math.max(0, Math.min(100, percent))}%` }} />
            </div>
          </div>
          <div className="completion-detail-row">
            <span>Geplante Dauer</span>
            <strong>{formatDuration(planned)}</strong>
          </div>
          <div className="completion-detail-row">
            <span>Tatsächliche Dauer</span>
            <strong>{formatDuration(elapsed)}</strong>
          </div>
        </section>

        <aside className="dashboard-card dashboard-coach-card">
          <div className="dashboard-coach-heading">
            <div className="dashboard-coach-avatar" aria-hidden="true">
              <div className="dashboard-coach-face">DFC</div>
              <span>Coach</span>
            </div>
            <div>
              <div className="dashboard-section-label">DEIN COACH</div>
              <h2>{completed ? 'Gut gemacht!' : 'Dein Training zählt.'}</h2>
            </div>
          </div>
          <p className="dashboard-coach-text">
            {loading
              ? 'Ich werte dein Training aus.'
              : completed
                ? `Du hast ${formatDuration(elapsed)} trainiert und dein Workout abgeschlossen. Die geplante Dauer lag bei ${formatDuration(planned)}.`
                : `Du hast ${formatDuration(elapsed)} trainiert. Das Workout wurde vorzeitig beendet. Auch diese Aktivität gehört zu deinem Trainingsverlauf.`}
          </p>
          <div className="dashboard-coach-recommendation">
            <span>Nächster Schritt</span>
            <strong>
              {completed
                ? 'Gönn dir ausreichend Erholung und erfasse beim nächsten Check-in deine aktuelle Tagesform.'
                : 'Achte auf deine Erholung. Dein nächster Check-in hilft dabei, das folgende Training passend zu planen.'}
            </strong>
          </div>
        </aside>
      </div>

      <section className="dashboard-card completion-results-card">
        <div className="dashboard-card-header">
          <div>
            <div className="dashboard-section-label">TRAININGSERGEBNIS</div>
            <h2>Deine Zahlen</h2>
          </div>
        </div>
        <div className="completion-metrics">
          <div><span>Trainiert</span><strong>{formatDuration(elapsed)}</strong><small>Minuten : Sekunden</small></div>
          <div><span>Geplant</span><strong>{formatDuration(planned)}</strong><small>Minuten : Sekunden</small></div>
          <div><span>Erfüllung</span><strong>{loading ? '–' : `${percent} %`}</strong><small>Der geplanten Dauer</small></div>
          <div><span>Distanz</span><strong>{formatDistance(workout.distanceM)} km</strong><small>Gespeicherter Trainingswert</small></div>
        </div>
      </section>

      <section className="dashboard-card dashboard-badges-card">
        <div className="dashboard-card-header">
          <div>
            <div className="dashboard-section-label">FORTSCHRITT</div>
            <h2>Deine Badges</h2>
          </div>
        </div>
        <div className="completion-badge-placeholder">
          <div className="dashboard-badge-icon" aria-hidden="true">★</div>
          <div>
            <strong>Deine Erfolge werden hier sichtbar.</strong>
            <p>Neue Badges werden angezeigt, sobald die Badge-Auswertung für abgeschlossene Workouts angebunden ist.</p>
          </div>
        </div>
      </section>

      <div className="completion-dashboard-actions">
        <button type="button" className="primary-action" onClick={onDone}>
          Zum Dashboard
        </button>
      </div>
    </section>
  )
}
