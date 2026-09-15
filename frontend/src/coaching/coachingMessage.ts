import type { LiveCoachingEvent } from "./types";

export function coachingMessage(event: LiveCoachingEvent): string {
  switch (event.type) {
    case "coaching.pause_started":
      return "Pause";

    case "coaching.pause_ended":
      return "Weiter geht's";

    case "coaching.phase_started":
      return phaseStartedMessage(event.phaseType, event.durationMinutes);

    case "coaching.decision": {
      const seconds = Math.round(event.outsideTargetSeconds);

      switch (event.action) {
        case "increase_intensity":
          return `Dein Puls liegt seit ${seconds} s unter dem Zielbereich. Erhöhe die Intensität etwas.`;

        case "reduce_intensity":
          return `Dein Puls liegt seit ${seconds} s über dem Zielbereich. Nimm etwas Tempo heraus.`;
      }
    }
  }
}

function phaseStartedMessage(
  phaseType: "warm_up" | "main" | "cool_down",
  durationMinutes: number,
): string {
  switch (phaseType) {
    case "warm_up":
      return `Aufwärmen: ${durationMinutes} Minuten locker einrollen.`;
    case "main":
      return `Hauptphase: ${durationMinutes} Minuten gleichmäßig im Zielbereich fahren.`;
    case "cool_down":
      return `Cooldown: ${durationMinutes} Minuten Tempo herausnehmen und locker ausrollen.`;
  }
}
