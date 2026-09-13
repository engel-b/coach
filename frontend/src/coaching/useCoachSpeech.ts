import { useCallback, useEffect, useRef } from "react";

import {
  coachingSpeechMessage,
  evaluateCoachingSpeech,
  type CoachingSpeechState,
} from "./coachingSpeech";
import type { LiveCoachingEvent } from "./types";

const INITIAL_STATE: CoachingSpeechState = {
  lastDecisionAction: null,
  lastSpokenAtMs: null,
};

/**
 * Spricht fachliche Coaching-Events ueber die Web Speech API aus.
 *
 * Der Hook entscheidet nicht ueber Trainingslogik. Er setzt ausschliesslich
 * die akustische Speech Policy um und bleibt damit von der Coaching Engine
 * getrennt.
 */
export function useCoachSpeech(): (event: LiveCoachingEvent) => void {
  const speechStateRef = useRef<CoachingSpeechState>(INITIAL_STATE);

  useEffect(() => {
    return () => {
      if ("speechSynthesis" in window) {
        window.speechSynthesis.cancel();
      }
    };
  }, []);

  return useCallback((event: LiveCoachingEvent): void => {
    if (
      !("speechSynthesis" in window) ||
      !("SpeechSynthesisUtterance" in window)
    ) {
      return;
    }

    const decision = evaluateCoachingSpeech(
      event,
      speechStateRef.current,
      Date.now(),
    );

    speechStateRef.current = decision.nextState;

    if (!decision.speak) {
      return;
    }

    const utterance = new window.SpeechSynthesisUtterance(
      coachingSpeechMessage(event),
    );

    utterance.lang = "de-DE";
    utterance.rate = 1;
    utterance.pitch = 1;
    utterance.volume = 1;

    // Eine neue relevante Coaching-Entscheidung ist wichtiger als eine noch
    // laufende alte Ansage. Deshalb wird die alte Ausgabe nicht aufgestaut.
    window.speechSynthesis.cancel();
    window.speechSynthesis.speak(utterance);
  }, []);
}
