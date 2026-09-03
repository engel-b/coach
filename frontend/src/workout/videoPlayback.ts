const REFERENCE_SPEED_KMH = 20

const MIN_PLAYBACK_RATE = 0.5
const MAX_PLAYBACK_RATE = 2.0


/*
 * Entscheidet, ob das Trainingsvideo wegen eines
 * stillstehenden Bikes pausieren soll.
 *
 * null bedeutet:
 * Es liegt noch keine Geschwindigkeit vor.
 * In diesem Fall greifen wir nicht automatisch ein.
 *
 * Erst eine tatsächlich gemessene Geschwindigkeit von
 * 0 km/h oder weniger bedeutet "Bike steht".
 */
export function shouldPauseVideoForBike(
  speedKmh: number | null,
): boolean {
  return (
    speedKmh !== null &&
    speedKmh <= 0
  )
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
 *
 * Stillstand wird separat über
 * shouldPauseVideoForBike() behandelt.
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

