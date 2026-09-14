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
