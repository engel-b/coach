const REFERENCE_SPEED_KMH = 20

const MIN_PLAYBACK_RATE = 0.5
const MAX_PLAYBACK_RATE = 2.0


/*
 * Entscheidet, ob das Bike aktuell als aktiv gefahren
 * betrachtet wird.
 *
 * Die Trittfrequenz ist dafür die beste Information:
 *
 *   cadence > 0  -> Fahrer tritt
 *   cadence <= 0 -> Fahrer tritt nicht
 *
 * Falls das Bike keine Trittfrequenz liefert, verwenden
 * wir die Geschwindigkeit als Fallback.
 *
 * Sind noch überhaupt keine Bike-Daten vorhanden, greifen
 * wir nicht automatisch in das Workout ein.
 *
 * Diese Funktion enthält bewusst keine React-Logik.
 * Sie kann später unverändert Teil der WorkoutEngine werden.
 */
export function isBikeMoving(
  cadenceRpm: number | null,
  speedKmh: number | null,
): boolean | null {
  if (cadenceRpm !== null) {
    return cadenceRpm > 0
  }

  if (speedKmh !== null) {
    return speedKmh > 0
  }

  return null
}


/*
 * Berechnet die Wiedergabegeschwindigkeit des Videos
 * aus der aktuellen Fahrgeschwindigkeit.
 *
 * Referenz:
 *
 *   10 km/h -> 0.5x
 *   15 km/h -> 0.75x
 *   20 km/h -> 1.0x
 *   30 km/h -> 1.5x
 *   40 km/h -> 2.0x
 *
 * Werte außerhalb dieses Bereichs werden begrenzt.
 *
 * Falls noch keine Bike-Geschwindigkeit bekannt ist,
 * läuft das Video mit normaler Geschwindigkeit.
 */
export function calculateVideoPlaybackRate(
  speedKmh: number | null,
): number {
  if (speedKmh === null) {
    return 1
  }

  const calculatedRate =
    speedKmh / REFERENCE_SPEED_KMH

  return Math.min(
    MAX_PLAYBACK_RATE,
    Math.max(
      MIN_PLAYBACK_RATE,
      calculatedRate,
    ),
  )
}