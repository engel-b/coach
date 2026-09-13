import type { LiveCoachingEvent } from "./types";

export interface CoachingSpeechState {
  lastAction: LiveCoachingEvent["action"] | null;
  lastSpokenAtMs: number | null;
}

export interface CoachingSpeechDecision {
  speak: boolean;
  nextState: CoachingSpeechState;
}

const REPEAT_COOLDOWN_MS = 60_000;

/**
 * Kurze Formulierung fuer die Sprachausgabe.
 *
 * Die sichtbare UI-Nachricht bleibt davon getrennt: Gesprochene Hinweise
 * sollen kuerzer sein und beim Training schnell verstanden werden.
 */
export function coachingSpeechMessage(event: LiveCoachingEvent): string {
  switch (event.action) {
    case "increase_intensity":
      return "Dein Puls ist unter dem Zielbereich. Erhöhe die Intensität etwas.";

    case "reduce_intensity":
      return "Dein Puls ist über dem Zielbereich. Nimm etwas Tempo heraus.";
  }
}

/**
 * Entscheidet, ob ein Coaching-Event gesprochen werden soll.
 *
 * - Ein Wechsel der Aktion wird sofort gesprochen.
 * - Dieselbe Aktion wird innerhalb einer Minute nicht erneut gesprochen.
 *
 * Das Backend entprellt bereits fachliche Entscheidungen. Diese Policy ist
 * eine zweite, rein akustische Schutzschicht gegen zu haeufige Ansagen.
 */
export function evaluateCoachingSpeech(
  event: LiveCoachingEvent,
  state: CoachingSpeechState,
  nowMs: number,
): CoachingSpeechDecision {
  const isDifferentAction = state.lastAction !== event.action;
  const cooldownElapsed =
    state.lastSpokenAtMs === null ||
    nowMs - state.lastSpokenAtMs >= REPEAT_COOLDOWN_MS;

  if (!isDifferentAction && !cooldownElapsed) {
    return {
      speak: false,
      nextState: state,
    };
  }

  return {
    speak: true,
    nextState: {
      lastAction: event.action,
      lastSpokenAtMs: nowMs,
    },
  };
}
