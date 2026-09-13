import { act, renderHook } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import type { LiveCoachingEvent } from "./types";
import { useCoachSpeech } from "./useCoachSpeech";

class FakeSpeechSynthesisUtterance {
  text: string;
  lang = "";
  rate = 1;
  pitch = 1;
  volume = 1;

  constructor(text: string) {
    this.text = text;
  }
}

function event(action: LiveCoachingEvent["action"]): LiveCoachingEvent {
  return {
    type: "coaching.decision",
    timestamp: "2026-09-13T08:30:00Z",
    workoutId: "workout-1",
    deviceId: "heart-rate-1",
    action,
    zoneStatus:
      action === "reduce_intensity" ? "above_target" : "below_target",
    heartRateBpm: action === "reduce_intensity" ? 149 : 119,
    targetMinBpm: 125,
    targetMaxBpm: 145,
    outsideTargetSeconds: 21,
    reason: "test",
  };
}

describe("useCoachSpeech", () => {
  const speak = vi.fn();
  const cancel = vi.fn();

  beforeEach(() => {
    vi.useFakeTimers();
    vi.setSystemTime(new Date("2026-09-13T08:30:00Z"));

    Object.defineProperty(window, "speechSynthesis", {
      configurable: true,
      value: {
        speak,
        cancel,
      },
    });

    Object.defineProperty(window, "SpeechSynthesisUtterance", {
      configurable: true,
      value: FakeSpeechSynthesisUtterance,
    });
  });

  afterEach(() => {
    vi.useRealTimers();
    speak.mockReset();
    cancel.mockReset();
  });

  it("speaks a relevant coaching event in German", () => {
    const { result } = renderHook(() => useCoachSpeech());

    act(() => {
      result.current(event("reduce_intensity"));
    });

    expect(cancel).toHaveBeenCalledOnce();
    expect(speak).toHaveBeenCalledOnce();

    const utterance = speak.mock.calls[0][0] as FakeSpeechSynthesisUtterance;

    expect(utterance.text).toBe(
      "Dein Puls ist über dem Zielbereich. Nimm etwas Tempo heraus.",
    );
    expect(utterance.lang).toBe("de-DE");
  });

  it("does not repeat the same action during the cooldown", () => {
    const { result } = renderHook(() => useCoachSpeech());

    act(() => {
      result.current(event("reduce_intensity"));
      result.current(event("reduce_intensity"));
    });

    expect(speak).toHaveBeenCalledOnce();
  });

  it("speaks an action change immediately", () => {
    const { result } = renderHook(() => useCoachSpeech());

    act(() => {
      result.current(event("reduce_intensity"));
      result.current(event("increase_intensity"));
    });

    expect(speak).toHaveBeenCalledTimes(2);
  });

  it("cancels pending speech when the hook is unmounted", () => {
    const { unmount } = renderHook(() => useCoachSpeech());

    unmount();

    expect(cancel).toHaveBeenCalledOnce();
  });
});
