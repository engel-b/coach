export interface WorkoutDistanceState {
  /*
   * Letzter nativer Total-Distance-Wert des Bikes.
   *
   * Wichtig:
   * Dieser Wert wird auch während einer Workout-Pause aktualisiert.
   * Dadurch zählen wir nach dem Resume nicht versehentlich Strecke,
   * die während der Pause entstanden ist.
   */
  lastNativeDistanceM: number | null

  /*
   * Tatsächlich dem aktuellen Workout zugerechnete Strecke.
   */
  accumulatedDistanceM: number
}

export function createWorkoutDistanceState():
  WorkoutDistanceState {
  return {
    lastNativeDistanceM: null,
    accumulatedDistanceM: 0,
  }
}

export function applyNativeDistanceSample(
  current: WorkoutDistanceState,
  nativeDistanceM: number | null,
  countDistance: boolean,
): WorkoutDistanceState {
  /*
   * Kein verwertbarer FTMS-Wert:
   * Zustand unverändert lassen.
   */
  if (
    nativeDistanceM === null ||
    !Number.isFinite(nativeDistanceM) ||
    nativeDistanceM < 0
  ) {
    return current
  }

  /*
   * Der erste Wert ist ausschließlich unsere Baseline.
   *
   * Beispiel:
   *
   * Bike steht beim Workout-Start bereits bei 406 m.
   *
   * 406 m dürfen nicht als Workout-Distanz gewertet werden.
   */
  if (current.lastNativeDistanceM === null) {
    return {
      ...current,
      lastNativeDistanceM: nativeDistanceM,
    }
  }

  const deltaM =
    nativeDistanceM - current.lastNativeDistanceM

  /*
   * Der Bike-Zähler kann durch Reconnect, Neustart oder
   * Ausschalten wieder bei 0 beginnen.
   *
   * Beispiel:
   *
   * letzter Wert: 1850 m
   * neuer Wert:     12 m
   *
   * Das ist keine negative Fahrstrecke, sondern ein Reset.
   * Wir setzen deshalb nur eine neue Baseline.
   */
  if (deltaM < 0) {
    return {
      ...current,
      lastNativeDistanceM: nativeDistanceM,
    }
  }

  /*
   * lastNativeDistanceM wird IMMER aktualisiert.
   *
   * accumulatedDistanceM wächst aber nur dann, wenn das
   * Workout diesen Abschnitt tatsächlich zählen soll.
   *
   * Genau dadurch funktioniert Pause korrekt:
   *
   *   RUNNING: 1000 -> 1010  => +10 m
   *   PAUSED:  1010 -> 1020  =>  +0 m
   *   RUNNING: 1020 -> 1030  => +10 m
   *
   * und nicht fälschlich +20 m nach dem Resume.
   */
  return {
    lastNativeDistanceM: nativeDistanceM,
    accumulatedDistanceM:
      current.accumulatedDistanceM +
      (countDistance ? deltaM : 0),
  }
}