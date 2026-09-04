export type WorkoutRuntimeState =
  | 'running'
  | 'finish_window'
  | 'overtime'
  | 'completed'


export interface WorkoutRuntime {
  state: WorkoutRuntimeState

  /*
   * Anzahl der Sekunden, die seit dem Erreichen
   * der geplanten Trainingsdauer vergangen sind.
   *
   * Relevant ausschließlich im finish_window.
   */
  finishWindowElapsedSeconds: number
}


export type WorkoutRuntimeEvent =
  | {
      type: 'planned_duration_reached'
    }
  | {
      type: 'tick'
    }
  | {
      type: 'bike_stopped'
    }


const FINISH_WINDOW_SECONDS = 30


/*
 * Reine Zustandsmaschine für das Ende eines Workouts.
 *
 * Keine React-Hooks.
 * Keine Browser-API.
 * Kein Audio.
 * Kein HTTP.
 *
 * Vergleichbar mit einer kleinen Java-Domain-Class:
 *
 *   RuntimeState handle(RuntimeState state, Event event)
 *
 * Damit können wir diese Logik später praktisch
 * unverändert in die WorkoutEngine übernehmen.
 */
export function applyWorkoutRuntimeEvent(
  runtime: WorkoutRuntime,
  event: WorkoutRuntimeEvent,
): WorkoutRuntime {
  switch (runtime.state) {
    case 'running':
      return handleRunning(runtime, event)

    case 'finish_window':
      return handleFinishWindow(
        runtime,
        event,
      )

    case 'overtime':
      return handleOvertime(runtime)

    case 'completed':
      return runtime
  }
}


function handleRunning(
  runtime: WorkoutRuntime,
  event: WorkoutRuntimeEvent,
): WorkoutRuntime {
  if (
    event.type ===
    'planned_duration_reached'
  ) {
    return {
      state: 'finish_window',
      finishWindowElapsedSeconds: 0,
    }
  }

  return runtime
}


function handleFinishWindow(
  runtime: WorkoutRuntime,
  event: WorkoutRuntimeEvent,
): WorkoutRuntime {
  if (event.type === 'bike_stopped') {
    return {
      state: 'completed',
      finishWindowElapsedSeconds:
        runtime.finishWindowElapsedSeconds,
    }
  }

  if (event.type === 'tick') {
    const nextElapsedSeconds =
      runtime.finishWindowElapsedSeconds + 1

    if (
      nextElapsedSeconds >=
      FINISH_WINDOW_SECONDS
    ) {
      return {
        state: 'overtime',
        finishWindowElapsedSeconds:
          FINISH_WINDOW_SECONDS,
      }
    }

    return {
      state: 'finish_window',
      finishWindowElapsedSeconds:
        nextElapsedSeconds,
    }
  }

  return runtime
}


function handleOvertime(
  runtime: WorkoutRuntime,
): WorkoutRuntime {
  /*
   * Bike-Stopp beendet ein Workout nach Ablauf des
   * 30-Sekunden-Fensters ausdrücklich NICHT.
   *
   * In Overtime wird später lediglich normal pausiert.
   */
  return runtime
}


export function createWorkoutRuntime():
  WorkoutRuntime {
  return {
    state: 'running',
    finishWindowElapsedSeconds: 0,
  }
}


export function getFinishWindowRemainingSeconds(
  runtime: WorkoutRuntime,
): number {
  if (runtime.state !== 'finish_window') {
    return 0
  }

  return Math.max(
    0,
    FINISH_WINDOW_SECONDS -
      runtime.finishWindowElapsedSeconds,
  )
}