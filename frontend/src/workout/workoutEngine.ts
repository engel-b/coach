export type WorkoutExecutionState =
  "running" | "paused" | "finish_window" | "overtime" | "completed" | "aborted";

export type WorkoutPauseReason = "manual" | "bike" | null;

type ActiveWorkoutState = "running" | "finish_window" | "overtime";

export interface WorkoutEngineState {
  state: WorkoutExecutionState;

  /*
   * Tatsächlich gezählte Trainingszeit.
   *
   * Während einer bestätigten Pause wird diese Zeit
   * nicht erhöht.
   */
  elapsedSeconds: number;

  /*
   * Eigener Zähler für das 30-Sekunden-Fenster nach
   * Erreichen der geplanten Trainingsdauer.
   */
  finishWindowElapsedSeconds: number;

  /*
   * Geplante Trainingsdauer.
   *
   * Die Engine entscheidet selbst, wann aus "running"
   * das "finish_window" wird.
   */
  plannedDurationSeconds: number;

  /*
   * Letzter bekannter Bewegungszustand des Bikes.
   *
   * null bedeutet:
   * Es liegen momentan keine verwertbaren Bike-Daten vor.
   */
  bikeMoving: boolean | null;

  /*
   * Anzahl aufeinanderfolgender Sekunden, in denen das
   * Bike als stillstehend gemeldet wurde.
   *
   * Damit entprellen wir kurze cadenceRpm=0-Ausreißer.
   */
  bikeStoppedForSeconds: number;

  /*
   * Nur im Zustand "paused" gesetzt.
   */
  pauseReason: WorkoutPauseReason;

  /*
   * Zustand, in den nach einer Pause zurückgekehrt wird.
   *
   * Beispiel:
   *
   *   overtime
   *      -> bike pause
   *      -> paused
   *      -> bike moves
   *      -> overtime
   */
  pausedFrom: ActiveWorkoutState | null;
}

export type WorkoutEngineEvent =
  | {
      type: "tick";
    }
  | {
      type: "bike_movement_changed";
      moving: boolean | null;
    }
  | {
      type: "manual_pause";
    }
  | {
      type: "manual_resume";
    }
  | {
      type: "abort_requested";
    };

export interface WorkoutEngineEffects {
  /*
   * Einmaliger Effekt beim Eintritt in das
   * 30-Sekunden-Abschlussfenster.
   */
  playFinishSound: boolean;
}

export interface WorkoutEngineTransition {
  state: WorkoutEngineState;
  effects: WorkoutEngineEffects;
}

const FINISH_WINDOW_SECONDS = 30;
const BIKE_STOP_DEBOUNCE_SECONDS = 3;

const NO_EFFECTS: WorkoutEngineEffects = {
  playFinishSound: false,
};

/*
 * Erzeugt den initialen Zustand eines Workouts.
 *
 * Vergleichbar mit einem Java-Konstruktor bzw. einer
 * statischen Factory-Methode.
 */
export function createWorkoutEngine(
  plannedDurationSeconds: number,
): WorkoutEngineState {
  if (
    !Number.isInteger(plannedDurationSeconds) ||
    plannedDurationSeconds <= 0
  ) {
    throw new Error("plannedDurationSeconds must be a positive integer");
  }

  return {
    state: "running",
    elapsedSeconds: 0,
    finishWindowElapsedSeconds: 0,
    plannedDurationSeconds,
    bikeMoving: null,
    bikeStoppedForSeconds: 0,
    pauseReason: null,
    pausedFrom: null,
  };
}

/*
 * Zentraler Einstiegspunkt der Zustandsmaschine.
 *
 * Diese Funktion ist vollständig rein:
 *
 * - kein React
 * - kein Timer
 * - kein Audio
 * - kein HTTP
 * - keine WebSocket-Verbindung
 *
 * Gleicher State + gleiches Event ergeben immer
 * denselben neuen State.
 */
export function applyWorkoutEngineEvent(
  current: WorkoutEngineState,
  event: WorkoutEngineEvent,
): WorkoutEngineTransition {
  if (current.state === "completed" || current.state === "aborted") {
    return unchanged(current);
  }

  switch (event.type) {
    case "bike_movement_changed":
      return handleBikeMovementChanged(current, event.moving);

    case "manual_pause":
      return handleManualPause(current);

    case "manual_resume":
      return handleManualResume(current);

    case "abort_requested":
      return {
        state: {
          ...current,
          state: "aborted",
          pauseReason: null,
          pausedFrom: null,
        },
        effects: NO_EFFECTS,
      };

    case "tick":
      return handleTick(current);
  }
}

function handleBikeMovementChanged(
  current: WorkoutEngineState,
  moving: boolean | null,
): WorkoutEngineTransition {
  /*
   * Sobald wieder Bewegung erkannt wird, ist eine
   * eventuell begonnene Stop-Entprellung hinfällig.
   */
  const bikeStoppedForSeconds =
    moving === false ? current.bikeStoppedForSeconds : 0;

  /*
   * Eine automatische Bike-Pause wird automatisch
   * aufgehoben, sobald wieder getreten wird.
   *
   * Eine manuelle Pause dagegen darf niemals durch
   * Bike-Telemetrie aufgehoben werden.
   */
  if (
    current.state === "paused" &&
    current.pauseReason === "bike" &&
    moving === true &&
    current.pausedFrom !== null
  ) {
    return {
      state: {
        ...current,
        state: current.pausedFrom,
        bikeMoving: moving,
        bikeStoppedForSeconds: 0,
        pauseReason: null,
        pausedFrom: null,
      },
      effects: NO_EFFECTS,
    };
  }

  return {
    state: {
      ...current,
      bikeMoving: moving,
      bikeStoppedForSeconds,
    },
    effects: NO_EFFECTS,
  };
}

function handleManualPause(
  current: WorkoutEngineState,
): WorkoutEngineTransition {
  if (!isActiveState(current.state)) {
    return unchanged(current);
  }

  return {
    state: {
      ...current,
      state: "paused",
      pauseReason: "manual",
      pausedFrom: current.state,
    },
    effects: NO_EFFECTS,
  };
}

function handleManualResume(
  current: WorkoutEngineState,
): WorkoutEngineTransition {
  if (
    current.state !== "paused" ||
    current.pauseReason !== "manual" ||
    current.pausedFrom === null
  ) {
    return unchanged(current);
  }

  return {
    state: {
      ...current,
      state: current.pausedFrom,
      pauseReason: null,
      pausedFrom: null,
      bikeStoppedForSeconds: 0,
    },
    effects: NO_EFFECTS,
  };
}

function handleTick(current: WorkoutEngineState): WorkoutEngineTransition {
  switch (current.state) {
    case "running":
      return tickRunning(current);

    case "finish_window":
      return tickFinishWindow(current);

    case "overtime":
      return tickOvertime(current);

    case "paused":
    case "completed":
    case "aborted":
      return unchanged(current);
  }
}

function tickRunning(current: WorkoutEngineState): WorkoutEngineTransition {
  const bikePause = detectBikePause(current);

  if (bikePause !== null) {
    return bikePause;
  }

  const nextElapsedSeconds = current.elapsedSeconds + 1;

  /*
   * Die Engine kennt die geplante Dauer selbst.
   * WorkoutView muss später also nicht mehr separat
   * "current.phase === null" als Workout-Ende deuten.
   */
  if (nextElapsedSeconds >= current.plannedDurationSeconds) {
    return {
      state: {
        ...current,
        state: "finish_window",
        elapsedSeconds: nextElapsedSeconds,
        finishWindowElapsedSeconds: 0,
        bikeStoppedForSeconds: 0,
      },
      effects: {
        playFinishSound: true,
      },
    };
  }

  return {
    state: {
      ...current,
      elapsedSeconds: nextElapsedSeconds,
    },
    effects: NO_EFFECTS,
  };
}

function tickFinishWindow(
  current: WorkoutEngineState,
): WorkoutEngineTransition {
  /*
   * Im Finish Window hat Bike-Stillstand eine andere
   * Bedeutung als während des normalen Trainings:
   *
   * Nach der Entprellung wird das Workout abgeschlossen,
   * nicht lediglich pausiert.
   *
   * Während der Entprellung läuft der 30-Sekunden-Zähler
   * bewusst nicht weiter. Dadurch gilt auch:
   *
   * Stoppt der Fahrer bei Sekunde 29, wird nach drei
   * bestätigten Stillstandssekunden abgeschlossen und
   * nicht versehentlich Overtime gestartet.
   */
  if (current.bikeMoving === false) {
    const stoppedForSeconds = current.bikeStoppedForSeconds + 1;

    if (stoppedForSeconds >= BIKE_STOP_DEBOUNCE_SECONDS) {
      return {
        state: {
          ...current,
          state: "completed",
          bikeStoppedForSeconds: stoppedForSeconds,
          pauseReason: null,
          pausedFrom: null,
        },
        effects: NO_EFFECTS,
      };
    }

    return {
      state: {
        ...current,
        bikeStoppedForSeconds: stoppedForSeconds,
      },
      effects: NO_EFFECTS,
    };
  }

  const nextFinishWindowSeconds = current.finishWindowElapsedSeconds + 1;

  const nextElapsedSeconds = current.elapsedSeconds + 1;

  if (nextFinishWindowSeconds >= FINISH_WINDOW_SECONDS) {
    return {
      state: {
        ...current,
        state: "overtime",
        elapsedSeconds: nextElapsedSeconds,
        finishWindowElapsedSeconds: FINISH_WINDOW_SECONDS,
        bikeStoppedForSeconds: 0,
      },
      effects: NO_EFFECTS,
    };
  }

  return {
    state: {
      ...current,
      elapsedSeconds: nextElapsedSeconds,
      finishWindowElapsedSeconds: nextFinishWindowSeconds,
      bikeStoppedForSeconds: 0,
    },
    effects: NO_EFFECTS,
  };
}

function tickOvertime(current: WorkoutEngineState): WorkoutEngineTransition {
  const bikePause = detectBikePause(current);

  if (bikePause !== null) {
    return bikePause;
  }

  return {
    state: {
      ...current,
      elapsedSeconds: current.elapsedSeconds + 1,
    },
    effects: NO_EFFECTS,
  };
}

/*
 * Entprellung für normale Bike-Pausen.
 *
 * Erst nach drei aufeinanderfolgenden Sekunden mit
 * bikeMoving=false wird tatsächlich pausiert.
 */
function detectBikePause(
  current: WorkoutEngineState,
): WorkoutEngineTransition | null {
  if (current.bikeMoving !== false) {
    if (current.bikeStoppedForSeconds === 0) {
      return null;
    }

    return {
      state: {
        ...current,
        bikeStoppedForSeconds: 0,
      },
      effects: NO_EFFECTS,
    };
  }

  const stoppedForSeconds = current.bikeStoppedForSeconds + 1;

  if (stoppedForSeconds < BIKE_STOP_DEBOUNCE_SECONDS) {
    return {
      state: {
        ...current,
        elapsedSeconds: current.elapsedSeconds + 1,
        bikeStoppedForSeconds: stoppedForSeconds,
      },
      effects: NO_EFFECTS,
    };
  }

  if (!isActiveState(current.state)) {
    return null;
  }

  return {
    state: {
      ...current,
      state: "paused",
      bikeStoppedForSeconds: stoppedForSeconds,
      pauseReason: "bike",
      pausedFrom: current.state,
    },
    effects: NO_EFFECTS,
  };
}

function isActiveState(
  state: WorkoutExecutionState,
): state is ActiveWorkoutState {
  return (
    state === "running" || state === "finish_window" || state === "overtime"
  );
}

function unchanged(state: WorkoutEngineState): WorkoutEngineTransition {
  return {
    state,
    effects: NO_EFFECTS,
  };
}

/*
 * Abgeleitete Informationen für die UI.
 *
 * Dadurch muss WorkoutView später keine eigenen Regeln
 * darüber besitzen, wann Video und Trainingszeit laufen.
 */
export function shouldPlayWorkoutVideo(state: WorkoutEngineState): boolean {
  return isActiveState(state.state);
}

export function shouldCountWorkoutTime(state: WorkoutEngineState): boolean {
  return isActiveState(state.state);
}

export function shouldShowFinishPrompt(state: WorkoutEngineState): boolean {
  return state.state === "finish_window";
}

export function getFinishWindowRemainingSeconds(
  state: WorkoutEngineState,
): number {
  if (state.state !== "finish_window") {
    return 0;
  }

  return Math.max(0, FINISH_WINDOW_SECONDS - state.finishWindowElapsedSeconds);
}
