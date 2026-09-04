const WORKOUT_FINISH_SOUND = "/sounds/workout-finished.wav";

/*
 * Spielt das akustische Signal ab, wenn die geplante
 * Trainingsdauer erreicht wurde.
 *
 * Die Workout-Logik soll nicht wissen, wie der Ton
 * technisch abgespielt wird. Deshalb bleibt der
 * Browser-spezifische Audio-Code in diesem Adapter.
 */
export async function playWorkoutFinishSound(): Promise<void> {
  const audio = new Audio(WORKOUT_FINISH_SOUND);

  try {
    await audio.play();
  } catch {
    /*
     * Audio darf niemals das Workout blockieren.
     *
     * Browser können Wiedergabe beispielsweise verhindern,
     * wenn noch keine Benutzerinteraktion stattgefunden hat.
     * Das visuelle Abschlussfenster funktioniert trotzdem.
     */
  }
}
