import { act, renderHook } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { synthesizeSpeech } from "../api/speech";
import type { CoachingAction, HeartRateCoachingEvent } from "./types";
import { useCoachSpeech } from "./useCoachSpeech";

vi.mock("../api/speech", () => ({
  synthesizeSpeech: vi.fn(),
}));

const synthesizeSpeechMock = vi.mocked(synthesizeSpeech);

class FakeAudio {
  static instances: FakeAudio[] = [];

  currentTime = 0;
  readonly pause = vi.fn();
  readonly play = vi.fn().mockResolvedValue(undefined);
  private readonly listeners = new Map<string, () => void>();

  constructor() {
    FakeAudio.instances.push(this);
  }

  addEventListener(type: string, listener: () => void): void {
    this.listeners.set(type, listener);
  }

  emit(type: string): void {
    this.listeners.get(type)?.();
  }
}

function event(action: CoachingAction): HeartRateCoachingEvent {
  return {
    type: "coaching.decision",
    timestamp: "2026-09-13T08:30:00Z",
    workoutId: "workout-1",
    deviceId: "heart-rate-1",
    action,
    zoneStatus: action === "reduce_intensity" ? "above_target" : "below_target",
    heartRateBpm: action === "reduce_intensity" ? 149 : 119,
    targetMinBpm: 125,
    targetMaxBpm: 145,
    outsideTargetSeconds: 21,
    deviationBpm: 4,
    deviationSeverity: "moderate",
    reason: "test",
  };
}

async function flushPromises(): Promise<void> {
  await Promise.resolve();
  await Promise.resolve();
}

describe("useCoachSpeech", () => {
  const createObjectURL = vi.fn(() => "blob:coach-audio");
  const revokeObjectURL = vi.fn();

  beforeEach(() => {
    vi.useFakeTimers();
    vi.setSystemTime(new Date("2026-09-13T08:30:00Z"));

    synthesizeSpeechMock.mockResolvedValue(
      new Blob(["wav"], { type: "audio/wav" }),
    );
    FakeAudio.instances = [];

    vi.stubGlobal("Audio", FakeAudio);
    vi.stubGlobal("URL", {
      ...URL,
      createObjectURL,
      revokeObjectURL,
    });
  });

  afterEach(() => {
    vi.useRealTimers();
    vi.unstubAllGlobals();
    vi.clearAllMocks();
  });

  it("synthesizes and plays a relevant coaching event", async () => {
    const { result } = renderHook(() => useCoachSpeech());

    act(() => {
      result.current(event("reduce_intensity"));
    });
    await act(flushPromises);

    expect(synthesizeSpeechMock).toHaveBeenCalledWith(
      "Dein Puls ist über dem Zielbereich. Nimm etwas Tempo heraus.",
      expect.any(AbortSignal),
    );
    expect(FakeAudio.instances).toHaveLength(1);
    expect(FakeAudio.instances[0].play).toHaveBeenCalledOnce();
  });

  it("shows synthesis and playback status and clears it when the audio ends", async () => {
    const onStatus = vi.fn();
    const { result } = renderHook(() => useCoachSpeech(onStatus));

    act(() => result.current(event("reduce_intensity")));
    expect(onStatus).toHaveBeenCalledWith("synthesizing");
    await act(flushPromises);
    expect(onStatus).toHaveBeenLastCalledWith("playing");

    act(() => FakeAudio.instances[0].emit("ended"));
    expect(onStatus).toHaveBeenLastCalledWith("idle");
  });

  it("reports unavailable speech if TTS and the browser voice both fail", async () => {
    const onStatus = vi.fn();
    vi.stubGlobal("speechSynthesis", undefined);
    vi.stubGlobal("SpeechSynthesisUtterance", undefined);
    synthesizeSpeechMock.mockRejectedValue(new Error("Piper unavailable"));
    const { result } = renderHook(() => useCoachSpeech(onStatus));

    act(() => result.current(event("reduce_intensity")));
    await act(flushPromises);

    expect(onStatus).toHaveBeenLastCalledWith("unavailable");
  });

  it("does not repeat the same action during the cooldown", () => {
    const { result } = renderHook(() => useCoachSpeech());

    act(() => {
      result.current(event("reduce_intensity"));
      result.current(event("reduce_intensity"));
    });

    expect(synthesizeSpeechMock).toHaveBeenCalledOnce();
  });

  it("synthesizes an action change immediately", () => {
    const { result } = renderHook(() => useCoachSpeech());

    act(() => {
      result.current(event("reduce_intensity"));
      result.current(event("increase_intensity"));
    });

    expect(synthesizeSpeechMock).toHaveBeenCalledTimes(2);
  });

  it("aborts pending speech when the hook is unmounted", () => {
    const abort = vi.spyOn(AbortController.prototype, "abort");
    const { result, unmount } = renderHook(() => useCoachSpeech());

    act(() => {
      result.current(event("reduce_intensity"));
    });
    unmount();

    expect(abort).toHaveBeenCalled();
  });

  it("forwards structure coaching events to local TTS", async () => {
    const { result } = renderHook(() => useCoachSpeech());

    act(() => {
      result.current({
        type: "coaching.phase_started",
        timestamp: "2026-09-13T08:30:00Z",
        workoutId: "workout-1",
        phaseIndex: 1,
        phaseType: "main",
        durationMinutes: 20,
        targetMinBpm: 125,
        targetMaxBpm: 145,
        isFinalPhase: false,
      });
    });
    await act(flushPromises);

    expect(synthesizeSpeechMock).toHaveBeenCalledWith(
      "Jetzt geht's in die Hauptphase! Finde deinen Rhythmus und bleib dran.",
      expect.any(AbortSignal),
    );
  });

  it("speaks pause events even without a heart-rate decision", async () => {
    const { result } = renderHook(() => useCoachSpeech());

    act(() => {
      result.current({
        type: "coaching.pause_started",
        timestamp: "2026-09-13T08:30:00Z",
        workoutId: "workout-1",
      });
    });
    await act(flushPromises);

    expect(synthesizeSpeechMock).toHaveBeenCalledWith(
      "Pause.",
      expect.any(AbortSignal),
    );
  });
});
