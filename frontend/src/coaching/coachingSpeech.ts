import type { LiveCoachingEvent } from "./types";

export interface CoachingSpeechState {
  lastDecisionAction: "increase_intensity" | "reduce_intensity" | null;
  lastDecisionSeverity: "moderate" | "large" | null;
  lastSpokenAtMs: number | null;
}

export interface CoachingSpeechDecision {
  speak: boolean;
  nextState: CoachingSpeechState;
}

const REPEAT_COOLDOWN_MS = 60_000;
const LARGE_REPEAT_COOLDOWN_MS = 30_000;

export function coachingSpeechMessage(event: LiveCoachingEvent): string {
  switch (event.type) {
    case "coaching.pause_started":
      return "Pause.";

    case "coaching.pause_ended":
      return "Weiter geht's!";

    case "coaching.phase_started":
      if (event.isFinalPhase) {
        return "Letzte Phase! Stark bis hierhin. Jetzt sauber zu Ende fahren.";
      }
      switch (event.phaseType) {
        case "warm_up":
          return "Los geht's! Fahr dich locker warm und finde deinen Rhythmus.";
        case "main":
          return "Jetzt geht's in die Hauptphase! Finde deinen Rhythmus und bleib dran.";
        case "cool_down":
          return "Geschafft! Jetzt Tempo rausnehmen und locker ausrollen.";
        default:
          return "";
      }

    case "coaching.phase_ending":
      return "Noch eine Minute! Bleib dran.";

    case "coaching.workout_halfway":
      return "Halbzeit! Die Hälfte ist geschafft. Weiter so.";

    case "coaching.decision":
      switch (event.action) {
        case "increase_intensity":
          return event.deviationSeverity === "large"
            ? "Dein Puls ist deutlich unter dem Zielbereich. Erhöhe die Intensität kontrolliert."
            : "Dein Puls ist unter dem Zielbereich. Erhöhe die Intensität etwas.";

        case "reduce_intensity":
          return event.deviationSeverity === "large"
            ? "Dein Puls ist deutlich über dem Zielbereich. Nimm jetzt Tempo heraus."
            : "Dein Puls ist über dem Zielbereich. Nimm etwas Tempo heraus.";
      }
  }
}

export function evaluateCoachingSpeech(
  event: LiveCoachingEvent,
  state: CoachingSpeechState,
  nowMs: number,
): CoachingSpeechDecision {
  if (event.type !== "coaching.decision") {
    return {
      speak: true,
      nextState: {
        lastDecisionAction: null,
        lastDecisionSeverity: null,
        lastSpokenAtMs: nowMs,
      },
    };
  }

  const isDifferentAction = state.lastDecisionAction !== event.action;
  const severityEscalated =
    state.lastDecisionSeverity === "moderate" &&
    event.deviationSeverity === "large";
  const repeatCooldownMs =
    event.deviationSeverity === "large"
      ? LARGE_REPEAT_COOLDOWN_MS
      : REPEAT_COOLDOWN_MS;
  const cooldownElapsed =
    state.lastSpokenAtMs === null ||
    nowMs - state.lastSpokenAtMs >= repeatCooldownMs;

  if (!isDifferentAction && !severityEscalated && !cooldownElapsed) {
    return {
      speak: false,
      nextState: state,
    };
  }

  return {
    speak: true,
    nextState: {
      lastDecisionAction: event.action,
      lastDecisionSeverity: event.deviationSeverity,
      lastSpokenAtMs: nowMs,
    },
  };
}
