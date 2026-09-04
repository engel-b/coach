import { useEffect, useMemo, useState } from 'react'

import { abortWorkout, completeWorkout } from '../api/workouts'
import type { DeviceState } from '../devices/types'
import type { Person } from '../persons/types'
import type { Workout, WorkoutPhase } from './types'
import { calculateVideoPlaybackRate, isBikeMoving } from './videoPlayback'
import { WorkoutVideo } from './WorkoutVideo'

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

  return {
    phase: null,
    phaseElapsedSeconds: 0,
  }
}

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

function heartRateMessage(
  state: 'unknown' | 'below' | 'target' | 'above',
): string {
  switch (state) {
    case 'below':
      return 'Intensität etwas erhöhen'

    case 'target':
      return 'Du bist im Zielbereich'

    case 'above':
      return 'Etwas Tempo herausnehmen'

    case 'unknown':
      return 'Warte auf Herzfrequenzdaten'
  }
}

export function WorkoutView({
  workout,
  devices,
  onComplete,
}: WorkoutViewProps) {
  const [elapsedSeconds, setElapsedSeconds] =
    useState(0)

  /*
  * Manuelle Pause und automatische Bike-Pause sind
  * unterschiedliche Ursachen.
  *
  * Sie dürfen nicht gegenseitig aufgehoben werden.
  */
  const [manualPaused, setManualPaused] = useState(false)

  const [
    finishConfirmation,
    setFinishConfirmation,
  ] = useState(false)

  const [finishing, setFinishing] = useState(false)

  const current = getCurrentPhase(
    workout.phases,
    elapsedSeconds,
  )

  const workoutFinished =
    current.phase === null

  const totalDurationSeconds = useMemo(
    () =>
      workout.phases.reduce(
        (total, phase) =>
          total + phase.durationMinutes * 60,
        0,
      ),
    [workout.phases],
  )

  const workoutProgress =
    totalDurationSeconds > 0
      ? Math.min(
          100,
          Math.round(
            (elapsedSeconds / totalDurationSeconds) *
              100,
          ),
        )
      : 0

  const phaseDurationSeconds =
    current.phase !== null
      ? current.phase.durationMinutes * 60
      : 0

  const phaseRemainingSeconds =
    current.phase !== null
      ? Math.max(
          0,
          phaseDurationSeconds -
            current.phaseElapsedSeconds,
        )
      : 0

  const phaseProgress =
    phaseDurationSeconds > 0
      ? Math.min(
          100,
          Math.round(
            (current.phaseElapsedSeconds /
              phaseDurationSeconds) *
              100,
          ),
        )
      : 100

  /*
   * Wir suchen den aktuell verbundenen Pulsgurt.
   *
   * Für V1 verwenden wir das erste verbundene HR-Gerät.
   */
  const heartRateDevice = useMemo(
    () =>
      devices.find(
        (device) =>
          device.deviceType === 'heart_rate' &&
          device.status === 'connected',
      ),
    [devices],
  )

  const heartRate =
    heartRateDevice?.heartRateBpm ?? null

  const targetMin =
    current.phase?.targetHeartRateMin ?? null

  const targetMax =
    current.phase?.targetHeartRateMax ?? null

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
  
  const bikeDevice = useMemo(
    () =>
      devices.find(
        (device) =>
          device.deviceType === 'bike' &&
          device.status === 'connected',
      ),
    [devices],
  )
  
  const speedKmh = bikeDevice?.speedKmh ?? null
  
  const cadenceRpm = bikeDevice?.cadenceRpm ?? null
  
  const powerW = bikeDevice?.powerW ?? null
    
  /*
  * Die Trittfrequenz entscheidet bevorzugt darüber,
  * ob tatsächlich gefahren wird.
  *
  * Liefert das Bike keine Cadence, verwendet
  * isBikeMoving() die Geschwindigkeit als Fallback.
  */
  const bikeMoving =
    isBikeMoving(
      cadenceRpm,
      speedKmh,
    )

  /*
  * null bedeutet:
  * Es gibt noch keine verwertbare Bike-Telemetrie.
  *
  * In diesem Fall darf das Workout nicht automatisch
  * pausiert werden.
  */
  const autoPaused =
    bikeMoving === false

  /*
  * Die effektive Pause ergibt sich aus beiden Ursachen.
  *
  * Wichtig:
  * Ein wieder fahrendes Bike kann manualPaused nicht
  * aufheben.
  */
  const workoutPaused =
    manualPaused || autoPaused

  /*
  * Während der Fahrt folgt die Geschwindigkeit des
  * Trainingsvideos der gemessenen Bike-Geschwindigkeit.
  */
  const videoPlaybackRate = calculateVideoPlaybackRate(speedKmh)


  useEffect(() => {
    if (
      workoutPaused ||
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
    workoutPaused,
    finishConfirmation,
    workoutFinished,
  ])

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

  useEffect(() => {
    function handleKeyDown(
      event: KeyboardEvent,
    ): void {
      if (finishing) {
        return
      }

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

      if (workoutFinished) {
        if (event.key === 'Enter') {
          void completeCurrentWorkout()
        }

        return
      }

      if (event.key === 'Enter') {
        setManualPaused(
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
      <header className="workout-stage-header">
        <button
          type="button"
          className="workout-exit-button"
          disabled={finishing}
          onClick={() => {
            setFinishConfirmation(true)
          }}
        >
          ← Workout beenden
        </button>

        <div className="workout-stage-title">
          <strong>
            Cycling Basic Endurance
          </strong>

          <span>
            {current.phase !== null
              ? phaseLabel(
                  current.phase.phaseType,
                )
              : 'Abgeschlossen'}
          </span>
        </div>

        <div className="workout-stage-status">
          <span
            className={
              heartRateDevice !== undefined
                ? 'device-dot connected'
                : 'device-dot'
            }
          />

          {heartRateDevice !== undefined
            ? heartRateDevice.deviceName
            : 'Pulsgurt nicht verbunden'}
        </div>
      </header>

      <div className="workout-stage">
        <WorkoutVideo
          src="/videos/cycling/alpen.mp4"
          paused={
            workoutPaused ||
            finishConfirmation ||
            workoutFinished
          }
          playbackRate={videoPlaybackRate}
        />
        <div className="workout-stage-shade" />

        <div className="workout-phase-overlay workout-overlay-card">
          <div className="workout-overlay-label">
            NÄCHSTES / AKTUELL
          </div>

          <div className="workout-overlay-title">
            {current.phase !== null
              ? phaseLabel(
                  current.phase.phaseType,
                )
              : 'Training abgeschlossen'}
          </div>

          {current.phase !== null && (
            <>
              <div className="workout-overlay-meta">
                <strong>
                  {formatTime(
                    phaseRemainingSeconds,
                  )}
                </strong>

                <span>
                  {targetMin ?? '–'}–{targetMax ?? '–'} bpm
                </span>
              </div>

              <div className="workout-progress-track">
                <div
                  className="workout-progress-value"
                  style={{
                    width: `${phaseProgress}%`,
                  }}
                />
              </div>
            </>
          )}
        </div>

        <div className="workout-total-overlay workout-overlay-card">
          <div className="workout-overlay-label">
            FORTSCHRITT
          </div>

          <div className="workout-overlay-meta">
            <strong>
              {formatTime(elapsedSeconds)}
            </strong>

            <span>
              / {formatTime(totalDurationSeconds)}
            </span>
          </div>

          <div className="workout-progress-track">
            <div
              className="workout-progress-value"
              style={{
                width: `${workoutProgress}%`,
              }}
            />
          </div>
        </div>

        <div
          className={
            `workout-target-overlay workout-overlay-card ${heartRateState}`
          }
        >
          <div className="workout-overlay-label">
            ♥ ZIELPULS
          </div>

          <div className="workout-target-range">
            {targetMin ?? '–'}–{targetMax ?? '–'}
            <span>bpm</span>
          </div>

          <div className="workout-target-message">
            {heartRateMessage(heartRateState)}
          </div>
        </div>

        <div className="workout-total-percent workout-overlay-card">
          <div
            className="workout-progress-ring"
            style={{
              background: `conic-gradient(
                #73d55b ${workoutProgress}%,
                rgba(255, 255, 255, 0.14) 0
              )`,
            }}
          >
            <div className="workout-progress-ring-inner" />
          </div>

          <div>
            <div className="workout-overlay-label">
              GESAMT
            </div>

            <strong>
              {workoutProgress}%
            </strong>
          </div>
        </div>

        <div className="coach-avatar">
          <div className="coach-avatar-face">
            <span>HC</span>
          </div>

          <div className="coach-avatar-status">
            Coach
          </div>
        </div>

        {workoutPaused && !workoutFinished && (
          <div className="workout-pause-overlay">
            <strong>PAUSE</strong>

            <span>
              {manualPaused
                ? 'Training manuell pausiert'
                : 'Weiter treten zum Fortsetzen'}
            </span>
          </div>
        )}

        {workoutFinished && (
          <div className="workout-pause-overlay workout-complete-overlay">
            <strong>
              Training abgeschlossen
            </strong>
            <span>
              Enter zum Speichern
            </span>
          </div>
        )}

        <div className="workout-telemetry-bar">
          <div className="workout-telemetry-metrics">
            <div className="telemetry-metric heart-rate-metric">
              <div className="telemetry-label">
                ♥ PULS
              </div>

              <div className="telemetry-value">
                {heartRate ?? '–'}
                <span>bpm</span>
              </div>

              <div
                className={
                  `telemetry-caption ${heartRateState}`
                }
              >
                {targetMin !== null &&
                targetMax !== null
                  ? `${targetMin}–${targetMax} bpm`
                  : 'Kein Zielbereich'}
              </div>
            </div>

            <div className="telemetry-metric">
              <div className="telemetry-label">
                ◷ ZEIT
              </div>

              <div className="telemetry-value">
                {formatTime(elapsedSeconds)}
              </div>

              <div className="telemetry-caption">
                / {formatTime(totalDurationSeconds)}
              </div>
            </div>

            <div className="telemetry-metric">
              <div className="telemetry-label">
                ◉ GESCHWINDIGKEIT
              </div>

              <div className="telemetry-value">
                <strong>{speedKmh !== null ? speedKmh.toFixed(1) : '–'}</strong>
                <span>km/h</span>
              </div>

              <div className="telemetry-caption">
                {speedKmh !== null ? '' : 'Bike noch nicht verbunden'}
              </div>
            </div>

            <div className="telemetry-metric">
              <div className="telemetry-label">
                ⚡ LEISTUNG
              </div>

              <div className="telemetry-value">
                <strong>{powerW !== null ? Math.round(powerW) : '–'}</strong>
                <span>W</span>
              </div>

              <div className="telemetry-caption">
                {powerW !== null ? '' : 'Bike noch nicht verbunden'}
              </div>
            </div>

            <div className="telemetry-metric">
              <div className="telemetry-label">
                ◌ TRITTFREQUENZ
              </div>

              <div className="telemetry-value">
                <strong>{cadenceRpm !== null ? Math.round(cadenceRpm) : '–'}</strong>
                <span>rpm</span>
              </div>

              <div className="telemetry-caption">
                {cadenceRpm !== null ? '' : 'Bike noch nicht verbunden'}
              </div>
            </div>
          </div>

          <div className="workout-telemetry-actions">
            {workoutFinished ? (
              <button
                type="button"
                className="workout-complete-button"
                disabled={finishing}
                onClick={() => {
                  void completeCurrentWorkout()
                }}
              >
                {finishing
                  ? 'Wird gespeichert …'
                  : 'Training speichern'}
              </button>
            ) : (
              <>
                <button
                  type="button"
                  className="workout-pause-button"
                  disabled={finishing}
                  onClick={() => {
                    setManualPaused(
                      (currentPaused) =>
                        !currentPaused,
                    )
                  }}
                >
                  {manualPaused
                    ? '▶ Fortsetzen'
                    : 'Ⅱ Pause'}
                </button>

                <button
                  type="button"
                  className="workout-stop-button"
                  disabled={finishing}
                  onClick={() => {
                    setFinishConfirmation(true)
                  }}
                >
                  □ Workout beenden
                </button>
              </>
            )}
          </div>
        </div>
      </div>

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
