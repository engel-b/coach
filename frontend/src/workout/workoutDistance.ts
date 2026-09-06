export interface WorkoutDistanceState {
  lastNativeDistanceM: number | null;
  accumulatedDistanceM: number;
}

/*
 * Erzeugt den Distanzzustand eines neuen Workouts.
 *
 * Wenn beim Start bereits ein nativer FTMS-Distanzwert
 * bekannt ist, verwenden wir ihn sofort als Baseline.
 *
 * Beispiel:
 *
 *   Bike zeigt beim Workout-Start bereits 1240 m.
 *
 * Das Workout startet trotzdem bei 0 m.
 * Erst die Differenz zu folgenden Samples zählt.
 */
export function createWorkoutDistanceState(
  initialNativeDistanceM: number | null = null,
): WorkoutDistanceState {
  return {
    lastNativeDistanceM: isValidNativeDistance(initialNativeDistanceM)
      ? initialNativeDistanceM
      : null,
    accumulatedDistanceM: 0,
  };
}

/*
 * Übernimmt ein neues FTMS-Total-Distance-Sample.
 *
 * Wichtig:
 * Die vom Bike gelieferte Distanz ist ein absoluter
 * Geräte-/Session-Zähler. Für das Workout speichern wir
 * ausschließlich die Differenzen zwischen den Samples.
 */
export function applyNativeDistanceSample(
  current: WorkoutDistanceState,
  nativeDistanceM: number | null,
  countDistance: boolean,
): WorkoutDistanceState {
  if (!isValidNativeDistance(nativeDistanceM)) {
    return current;
  }

  /*
   * Erstes Sample:
   * Nur Baseline setzen, noch nichts zum Workout addieren.
   */
  if (current.lastNativeDistanceM === null) {
    return {
      ...current,
      lastNativeDistanceM: nativeDistanceM,
    };
  }

  const deltaM = nativeDistanceM - current.lastNativeDistanceM;

  /*
   * Der native FTMS-Zähler kann bei Reconnect oder
   * neuer Bike-Session zurückspringen.
   *
   * Beispiel:
   *
   *   1050 -> 5
   *
   * Das ist keine negative Workout-Distanz.
   * Wir setzen lediglich eine neue Baseline.
   */
  if (deltaM < 0) {
    return {
      ...current,
      lastNativeDistanceM: nativeDistanceM,
    };
  }

  /*
   * Auch während einer Pause aktualisieren wir immer die
   * Baseline.
   *
   * Dadurch wird beispielsweise die durch das ausrollende
   * Schwungrad entstandene Distanz nach dem Fortsetzen
   * nicht nachträglich zum Workout addiert.
   */
  return {
    lastNativeDistanceM: nativeDistanceM,
    accumulatedDistanceM:
      current.accumulatedDistanceM + (countDistance ? deltaM : 0),
  };
}

function isValidNativeDistance(value: number | null): value is number {
  return value !== null && Number.isFinite(value) && value >= 0;
}
