import type { LiveCoachingEvent } from "./types";

/**
 * Formuliert die fachliche Coaching-Entscheidung zunächst als kurzen
 * sichtbaren UI-Text. Eine spätere Speech Policy kann denselben Eventstrom
 * für TTS verwenden, ohne diese Darstellung wiederverwenden zu müssen.
 */
export function coachingMessage(event: LiveCoachingEvent): string {
  const seconds = Math.round(event.outsideTargetSeconds);

  switch (event.action) {
    case "increase_intensity":
      return `Dein Puls liegt seit ${seconds} s unter dem Zielbereich. Erhöhe die Intensität etwas.`;

    case "reduce_intensity":
      return `Dein Puls liegt seit ${seconds} s über dem Zielbereich. Nimm etwas Tempo heraus.`;
  }
}
