import type { LiveCoachingEvent } from "./types";

export interface CoachingSpeechState {
  lastDecisionAction: "increase_intensity" | "reduce_intensity" | null;
  lastSpokenAtMs: number | null;
}

export interface CoachingSpeechDecision {
  speak: boolean;
  nextState: CoachingSpeechState;
}

const REPEAT_COOLDOWN_MS = 60_000;

export function coachingSpeechMessage(event: LiveCoachingEvent): string {
  switch (event.type) {
    case "coaching.pause_started":
      return "Pause.";

    case "coaching.pause_ended":
      return "Weiter geht's.";

    case "coaching.decision":
      switch (event.action) {
        case "increase_intensity":
          return "Dein Puls ist unter dem Zielbereich. Erhöhe die Intensität etwas.";

        case "reduce_intensity":
          return "Dein Puls ist über dem Zielbereich. Nimm etwas Tempo heraus.";
      }
  }
}

export function evaluateCoachingSpeech(
  event: LiveCoachingEvent,
  state: CoachingSpeechState,
  nowMs: number,
): CoachingSpeechDecision {
  // Pause und Resume sind seltene Zustandswechsel und sollen immer sofort
  // gesprochen werden. Sie unterliegen keinem HR-Wiederholungs-Cooldown.
  if (event.type !== "coaching.decision") {
    return {
      speak: true,
      nextState: {
        lastDecisionAction: null,
        lastSpokenAtMs: nowMs,
      },
    };
  }

  const isDifferentAction = state.lastDecisionAction !== event.action;
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
      lastDecisionAction: event.action,
      lastSpokenAtMs: nowMs,
    },
  };
}
