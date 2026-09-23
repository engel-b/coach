import { useCallback, useEffect, useRef } from "react";

import { synthesizeSpeech } from "../api/speech";
import {
  coachingSpeechMessage,
  evaluateCoachingSpeech,
  type CoachingSpeechState,
} from "./coachingSpeech";
import type { LiveCoachingEvent } from "./types";

const INITIAL_STATE: CoachingSpeechState = {
  lastDecisionAction: null,
  lastDecisionSeverity: null,
  lastSpokenAtMs: null,
};

function speakWithBrowserFallback(text: string): void {
  if (
    !("speechSynthesis" in window) ||
    !("SpeechSynthesisUtterance" in window)
  ) {
    return;
  }

  const utterance = new window.SpeechSynthesisUtterance(text);
  utterance.lang = "de-DE";
  utterance.rate = 1;
  utterance.pitch = 1;
  utterance.volume = 1;

  window.speechSynthesis.cancel();
  window.speechSynthesis.speak(utterance);
}

/**
 * Setzt die akustische Speech Policy fuer fachliche Coaching-Events um.
 *
 * Primaer wird Audio durch die lokale Backend-TTS erzeugt. Browser-TTS bleibt
 * nur als technischer Fallback erhalten, falls der lokale Adapter nicht
 * erreichbar oder noch nicht eingerichtet ist.
 */
export function useCoachSpeech(): (event: LiveCoachingEvent) => void {
  const speechStateRef = useRef<CoachingSpeechState>(INITIAL_STATE);
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const requestRef = useRef<AbortController | null>(null);
  const objectUrlRef = useRef<string | null>(null);

  const stopCurrentSpeech = useCallback((): void => {
    requestRef.current?.abort();
    requestRef.current = null;

    if (audioRef.current !== null) {
      audioRef.current.pause();
      audioRef.current.currentTime = 0;
      audioRef.current = null;
    }

    if (objectUrlRef.current !== null) {
      URL.revokeObjectURL(objectUrlRef.current);
      objectUrlRef.current = null;
    }

    if ("speechSynthesis" in window) {
      window.speechSynthesis.cancel();
    }
  }, []);

  useEffect(() => stopCurrentSpeech, [stopCurrentSpeech]);

  return useCallback(
    (event: LiveCoachingEvent): void => {
      const decision = evaluateCoachingSpeech(
        event,
        speechStateRef.current,
        Date.now(),
      );

      speechStateRef.current = decision.nextState;

      if (!decision.speak) {
        return;
      }

      const text = coachingSpeechMessage(event);

      stopCurrentSpeech();

      const controller = new AbortController();
      requestRef.current = controller;

      void synthesizeSpeech(text, controller.signal)
        .then(async (audioBlob) => {
          if (controller.signal.aborted) {
            return;
          }

          const objectUrl = URL.createObjectURL(audioBlob);
          objectUrlRef.current = objectUrl;

          const audio = new Audio(objectUrl);
          audioRef.current = audio;

          const cleanupAudio = (): void => {
            if (audioRef.current === audio) {
              audioRef.current = null;
            }
            if (objectUrlRef.current === objectUrl) {
              URL.revokeObjectURL(objectUrl);
              objectUrlRef.current = null;
            }
          };

          audio.addEventListener("ended", cleanupAudio, { once: true });
          audio.addEventListener("error", cleanupAudio, { once: true });

          try {
            await audio.play();
          } catch (error) {
            cleanupAudio();
            console.warn("Local coach audio playback failed", error);
            speakWithBrowserFallback(text);
          }
        })
        .catch((error: unknown) => {
          if (controller.signal.aborted) {
            return;
          }

          console.warn("Local coach TTS failed; using browser fallback", error);
          speakWithBrowserFallback(text);
        });
    },
    [stopCurrentSpeech],
  );
}
