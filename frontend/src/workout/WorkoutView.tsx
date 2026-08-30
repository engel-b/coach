import { useEffect, useMemo, useState } from 'react'

import { abortWorkout, completeWorkout } from '../api/workouts'
import type { DeviceState } from '../devices/types'
import type { Person } from '../persons/types'
import type { Workout, WorkoutPhase} from './types'


interface WorkoutViewProps {
  person: Person
  workout: Workout

  /*
   * Die Gerätedaten gehören App.tsx.
   *
   * WorkoutView konsumiert nur den aktuellen Zustand
   * und muss deshalb keine eigene Datenquelle mehr pollen.
   */
  devices: DeviceState[]

  onComplete: (workout: Workout) => void
}


/**
 * Formatiert Sekunden als MM:SS.
 *
 * Beispiel:
 *   75 -> "01:15"
 */
function formatTime(seconds: number): string {
  const safeSeconds = Math.max(0, seconds)

  const minutes = Math.floor(safeSeconds / 60)
  const remainingSeconds = safeSeconds % 60

  return `${String(minutes).padStart(2, '0')}:${String(
    remainingSeconds,
  ).padStart(2, '0')}`
}


/**
 * Ermittelt anhand der bereits trainierten Sekunden,
 * welche Trainingsphase aktuell aktiv ist.
 */
function getCurrentPhase(
  phases: WorkoutPhase[],
  elapsedSeconds: number,
): {
  phase: WorkoutPhase | null
  phaseElapsedSeconds: number
} {
  let consumedSeconds = 0

  for (const phase of phases) {
    const phaseSeconds = phase.durationMinutes * 60

    if (
      elapsedSeconds <
      consumedSeconds + phaseSeconds
    ) {
      return {
        phase,
        phaseElapsedSeconds:
          elapsedSeconds - consumedSeconds,
      }
    }

    consumedSeconds += phaseSeconds
  }

  /*
   * Keine Phase mehr gefunden:
   * Das geplante Training ist vollständig durchlaufen.
   */
  return {
    phase: null,
    phaseElapsedSeconds: 0,
  }
}


/**
 * Übersetzt den technischen Phase-Type in einen
 * benutzerfreundlichen deutschen Text.
 */
function phaseLabel(
  phaseType: WorkoutPhase['phaseType'],
): string {
  switch (phaseType) {
    case 'warm_up':
      return 'Aufwärmen'

    case 'main':
      return 'Hauptteil'

    case 'cool_down':
      return 'Cool-down'
  }
}


export function WorkoutView({
  person,
  workout,
  devices,
  onComplete,
}: WorkoutViewProps) {
  /*
   * Tatsächlich absolvierte Trainingszeit.
   *
   * Während einer Pause wird dieser Wert nicht erhöht.
   */
  const [elapsedSeconds, setElapsedSeconds] =
    useState(0)

  /*
   * Lokaler Pausenzustand.
   *
   * Noch nicht im Backend gespeichert.
   */
  const [paused, setPaused] =
    useState(false)

  /*
   * Steuert den Dialog:
   * "Training wirklich beenden?"
   */
  const [
    finishConfirmation,
    setFinishConfirmation,
  ] = useState(false)

  /*
   * Verhindert mehrfaches Absenden des Complete-Requests.
   */
  const [finishing, setFinishing] =
    useState(false)

  /*
   * Ermittelt die aktuelle Phase aus der
   * tatsächlich verstrichenen Trainingszeit.
   */
  const current = getCurrentPhase(
    workout.phases,
    elapsedSeconds,
  )

  /*
   * true, sobald keine Phase mehr aktiv ist.
   */
  const workoutFinished =
    current.phase === null

  /*
   * Workout-Timer.
   *
   * Der Timer läuft NICHT weiter, wenn:
   *
   * - der Benutzer pausiert hat,
   * - der Beenden-Dialog geöffnet ist,
   * - das komplette geplante Training beendet ist.
   */
  useEffect(() => {
    if (
      paused ||
      finishConfirmation ||
      workoutFinished
    ) {
      return
    }

    const timer = window.setInterval(() => {
      setElapsedSeconds((currentSeconds) => {
        return currentSeconds + 1
      })
    }, 1000)

    return () => {
      window.clearInterval(timer)
    }
  }, [
    paused,
    finishConfirmation,
    workoutFinished,
  ])

  /*
   * Wir suchen den aktuell verbundenen Pulsgurt.
   *
   * Später können mehrere HR-Geräte existieren.
   * Für V1 nehmen wir das erste verbundene.
   */
  const heartRateDevice = useMemo(
    () =>
      devices.find(
        (device) =>
          device.device_type === 'heart_rate' &&
          device.status === 'connected',
      ),
    [devices],
  )

  const heartRate =
    heartRateDevice?.heart_rate_bpm ?? null

  const targetMin =
    current.phase?.targetHeartRateMin ?? null

  const targetMax =
    current.phase?.targetHeartRateMax ?? null

  /*
   * Fachlich einfacher Zustand für die Live-Anzeige.
   *
   * Noch keine KI nötig:
   * Der Vergleich ist vollständig deterministisch.
   */
  let heartRateState:
    | 'unknown'
    | 'below'
    | 'target'
    | 'above' = 'unknown'

  if (
    heartRate !== null &&
    targetMin !== null &&
    targetMax !== null
  ) {
    if (heartRate < targetMin) {
      heartRateState = 'below'
    } else if (heartRate > targetMax) {
      heartRateState = 'above'
    } else {
      heartRateState = 'target'
    }
  }

  async function completeCurrentWorkout(): Promise<void> {
    if (finishing) {
      return
    }
  
    try {
      setFinishing(true)
  
      const completed = await completeWorkout(
        workout.id,
        elapsedSeconds,
      )
  
      onComplete(completed)
    } catch (error) {
      console.error(
        'Could not complete workout',
        error,
      )
    } finally {
      setFinishing(false)
    }
  }
  
  
  async function abortCurrentWorkout(): Promise<void> {
    if (finishing) {
      return
    }
  
    try {
      setFinishing(true)
  
      const aborted = await abortWorkout(
        workout.id,
        elapsedSeconds,
      )
  
      onComplete(aborted)
    } catch (error) {
      console.error(
        'Could not abort workout',
        error,
      )
    } finally {
      setFinishing(false)
    }
  }

  /*
   * Globale Tastatursteuerung.
   *
   * Normalbetrieb:
   *   Enter -> Pause / Fortsetzen
   *   Esc   -> Beenden-Dialog
   *
   * Beenden-Dialog:
   *   Enter -> Workout beenden
   *   Esc   -> Dialog schließen
   *
   * Ein späterer Nummernblock kann dieselben
   * KeyboardEvents auslösen.
   */
  useEffect(() => {
    function handleKeyDown(
      event: KeyboardEvent,
    ): void {
      if (finishing) {
        return
      }

      /*
       * Im Bestätigungsdialog haben Enter und Esc
       * eine andere Bedeutung.
       */
      if (finishConfirmation) {
        if (event.key === 'Enter') {
          void abortCurrentWorkout()
          return
        }

        if (event.key === 'Escape') {
          setFinishConfirmation(false)
        }

        return
      }

      /*
       * Nach vollständigem Ablauf des Trainings
       * soll Enter nicht wieder Pause umschalten.
       */
      if (workoutFinished) {
        if (event.key === 'Enter') {
          void completeCurrentWorkout()
        }

        return
      }

      if (event.key === 'Enter') {
        setPaused(
          (currentPaused) => !currentPaused,
        )
        return
      }

      if (event.key === 'Escape') {
        setFinishConfirmation(true)
      }
    }

    window.addEventListener(
      'keydown',
      handleKeyDown,
    )

    return () => {
      window.removeEventListener(
        'keydown',
        handleKeyDown,
      )
    }
  })

  return (
    <section className="workout-view">
      <header className="workout-header">
        <div>
          <div className="eyebrow">
            TRAINING · {person.displayName}
          </div>

          <h1>
            {workoutFinished
              ? 'Training abgeschlossen'
              : current.phase !== null
                ? phaseLabel(
                    current.phase.phaseType,
                  )
                : ''}
          </h1>
        </div>

        <div className="workout-clock">
          {formatTime(elapsedSeconds)}
        </div>
      </header>

      {paused && !workoutFinished && (
        <div className="pause-banner">
          PAUSE
        </div>
      )}

      <div className="workout-main">
        <div className="heart-rate-panel">
          <div className="metric-label">
            HERZFREQUENZ
          </div>

          <div className="live-heart-rate">
            ♥ {heartRate ?? '–'}
            <span>bpm</span>
          </div>

          {current.phase !== null && (
            <>
              <div
                className={
                  `target-state ${heartRateState}`
                }
              >
                Zielbereich:{' '}
                {
                  current.phase
                    .targetHeartRateMin
                }
                {'–'}
                {
                  current.phase
                    .targetHeartRateMax
                }{' '}
                bpm
              </div>

              {heartRateState === 'below' && (
                <p>
                  Du kannst die Intensität etwas erhöhen.
                </p>
              )}

              {heartRateState === 'target' && (
                <p>
                  Perfekt. Genau in diesem Bereich bleiben.
                </p>
              )}

              {heartRateState === 'above' && (
                <p>
                  Etwas Tempo herausnehmen.
                </p>
              )}

              {heartRateState === 'unknown' && (
                <p>
                  Warte auf Herzfrequenzdaten …
                </p>
              )}
            </>
          )}
        </div>

        {current.phase !== null && (
          <div className="phase-panel">
            <div className="metric-label">
              AKTUELLE PHASE
            </div>

            <div className="phase-title">
              {phaseLabel(
                current.phase.phaseType,
              )}
            </div>

            <div className="phase-time">
              {formatTime(
                current.phase.durationMinutes *
                  60 -
                  current.phaseElapsedSeconds,
              )}
            </div>

            <div className="phase-caption">
              verbleibend
            </div>
          </div>
        )}
      </div>

      <footer className="workout-footer">
        {workoutFinished ? (
          <>
            <span>
              Training vollständig absolviert ·
              Enter zum Abschließen
            </span>

            <button
              type="button"
              className="primary-action"
              disabled={finishing}
              onClick={() => {
                void completeCurrentWorkout()
              }}
            >
              {finishing
                ? 'Wird abgeschlossen …'
                : 'Training abschließen'}
            </button>
          </>
        ) : (
          <>
            <span>
              Enter ·{' '}
              {paused
                ? 'Fortsetzen'
                : 'Pause'}
              {' · '}
              Esc · Beenden
            </span>

            <button
              type="button"
              className="secondary-action"
              onClick={() => {
                setPaused(
                  (currentPaused) =>
                    !currentPaused,
                )
              }}
            >
              {paused
                ? 'Training fortsetzen'
                : 'Pause'}
            </button>
          </>
        )}
      </footer>

      {finishConfirmation && (
        <div className="confirmation-backdrop">
          <div className="confirmation-dialog">
            <div className="eyebrow">
              TRAINING BEENDEN
            </div>

            <h2>
              Möchtest du das Training wirklich
              beenden?
            </h2>

            <p>
              Die bisherige Trainingszeit beträgt{' '}
              {formatTime(elapsedSeconds)}.
            </p>

            <div className="confirmation-actions">
              <button
                type="button"
                className="secondary-action"
                disabled={finishing}
                onClick={() => {
                  setFinishConfirmation(false)
                }}
              >
                Weiter trainieren
              </button>

              <button
                type="button"
                className="primary-action"
                disabled={finishing}
                onClick={() => {
                  void abortCurrentWorkout()
                }}
              >
                {finishing
                  ? 'Wird beendet …'
                  : 'Training beenden'}
              </button>
            </div>

            <div className="keyboard-hint">
              Esc · Weiter trainieren
              {' · '}
              Enter · Training beenden
            </div>
          </div>
        </div>
      )}
    </section>
  )
}