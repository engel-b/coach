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
 *
 * Diese Logik liegt bewusst außerhalb der React-Komponente,
 * weil wir hier im nächsten Schritt auch die variable
 * Wiedergabegeschwindigkeit ergänzen werden.
 */
export function shouldPauseVideoForBike(
  speedKmh: number | null,
): boolean {
  return (
    speedKmh !== null &&
    speedKmh <= 0
  )
}
