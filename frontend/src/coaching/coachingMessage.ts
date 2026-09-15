import type { LiveCoachingEvent, WorkoutPhaseType } from "./types";

export function coachingMessage(event: LiveCoachingEvent): string {
  switch (event.type) {
    case "coaching.pause_started":
      return "Pause";

    case "coaching.pause_ended":
      return "Weiter geht's";

    case "coaching.phase_started":
      if (event.isFinalPhase) {
        return `Letzte Phase: ${phaseLabel(event.phaseType)} für ${event.durationMinutes} Minuten.`;
      }
      return phaseStartedMessage(event.phaseType, event.durationMinutes);

    case "coaching.phase_ending":
      return `Noch eine Minute in der ${phaseLabel(event.phaseType)}.`;

    case "coaching.workout_halfway":
      return "Halbzeit – die Hälfte des Workouts ist geschafft.";

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
  phaseType: WorkoutPhaseType,
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

function phaseLabel(phaseType: WorkoutPhaseType): string {
  switch (phaseType) {
    case "warm_up":
      return "Aufwärmphase";
    case "main":
      return "Hauptphase";
    case "cool_down":
      return "Cooldown-Phase";
  }
}
