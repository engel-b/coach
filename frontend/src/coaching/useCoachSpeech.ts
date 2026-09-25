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

export type CoachSpeechStatus =
  "idle" | "synthesizing" | "playing" | "browser_fallback" | "unavailable";

function speakWithBrowserFallback(text: string): boolean {
  try {
    if (!window.speechSynthesis || !window.SpeechSynthesisUtterance) {
      return false;
    }
    const utterance = new window.SpeechSynthesisUtterance(text);
    utterance.lang = "de-DE";
    utterance.rate = 1;
    utterance.pitch = 1;
    utterance.volume = 1;
    window.speechSynthesis.cancel();
    window.speechSynthesis.speak(utterance);
    return true;
  } catch (error) {
    console.warn("Browser coach speech failed", error);
    return false;
  }
}

/**
 * Setzt die akustische Speech Policy fuer fachliche Coaching-Events um.
 *
 * Primaer wird Audio durch die lokale Backend-TTS erzeugt. Browser-TTS bleibt
 * nur als technischer Fallback erhalten, falls der lokale Adapter nicht
 * erreichbar oder noch nicht eingerichtet ist.
 */
export function useCoachSpeech(
  onStatus?: (status: CoachSpeechStatus) => void,
): (event: LiveCoachingEvent) => void {
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

    window.speechSynthesis?.cancel();
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
      onStatus?.("synthesizing");

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

          audio.addEventListener(
            "ended",
            () => {
              if (audioRef.current === audio) onStatus?.("idle");
              cleanupAudio();
            },
            { once: true },
          );
          audio.addEventListener(
            "error",
            () => {
              const active = audioRef.current === audio;
              cleanupAudio();
              if (active && !controller.signal.aborted) {
                onStatus?.(
                  speakWithBrowserFallback(text)
                    ? "browser_fallback"
                    : "unavailable",
                );
              }
            },
            { once: true },
          );

          try {
            await audio.play();
            if (!controller.signal.aborted) onStatus?.("playing");
          } catch (error) {
            const active = audioRef.current === audio;
            cleanupAudio();
            if (active && !controller.signal.aborted) {
              console.warn("Local coach audio playback failed", error);
              onStatus?.(
                speakWithBrowserFallback(text)
                  ? "browser_fallback"
                  : "unavailable",
              );
            }
          }
        })
        .catch((error: unknown) => {
          if (controller.signal.aborted) {
            return;
          }

          console.warn("Local coach TTS failed; using browser fallback", error);
          onStatus?.(
            speakWithBrowserFallback(text) ? "browser_fallback" : "unavailable",
          );
        });
    },
    [onStatus, stopCurrentSpeech],
  );
}
