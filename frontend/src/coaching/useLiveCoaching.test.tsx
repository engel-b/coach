// @vitest-environment jsdom

import { act, render } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import type { LiveCoachingEvent } from "./types";
import { useLiveCoaching } from "./useLiveCoaching";

class FakeWebSocket {
  static instances: FakeWebSocket[] = [];

  readonly url: string;

  onopen: (() => void) | null = null;
  onclose: (() => void) | null = null;
  onerror: (() => void) | null = null;
  onmessage: ((event: MessageEvent<string>) => void) | null = null;

  close = vi.fn(() => {
    this.onclose?.();
  });

  constructor(url: string | URL) {
    this.url = url.toString();
    FakeWebSocket.instances.push(this);
  }

  open(): void {
    this.onopen?.();
  }

  disconnect(): void {
    this.onclose?.();
  }

  sendMessage(message: unknown): void {
    this.onmessage?.(
      new MessageEvent("message", {
        data: JSON.stringify(message),
      }),
    );
  }

  static reset(): void {
    FakeWebSocket.instances = [];
  }
}

function TestComponent({
  onMessage,
}: {
  onMessage: (message: LiveCoachingEvent) => void;
}) {
  const connected = useLiveCoaching({ onMessage });

  return <div>{connected ? "connected" : "disconnected"}</div>;
}

const validEvent: LiveCoachingEvent = {
  type: "coaching.decision",
  timestamp: "2026-09-13T08:30:00Z",
  workoutId: "workout-1",
  deviceId: "heart-rate-1",
  action: "reduce_intensity",
  zoneStatus: "above_target",
  heartRateBpm: 149,
  targetMinBpm: 125,
  targetMaxBpm: 145,
  outsideTargetSeconds: 21,
  reason: "heart_rate_above_target_long_enough",
};

describe("useLiveCoaching", () => {
  beforeEach(() => {
    vi.useFakeTimers();
    FakeWebSocket.reset();
    vi.stubGlobal("WebSocket", FakeWebSocket);
  });

  afterEach(() => {
    vi.runOnlyPendingTimers();
    vi.useRealTimers();
    vi.unstubAllGlobals();
  });

  it("connects to the coaching websocket", () => {
    render(<TestComponent onMessage={vi.fn()} />);

    expect(FakeWebSocket.instances).toHaveLength(1);
    expect(FakeWebSocket.instances[0]?.url).toContain("/ws/coaching");
  });

  it("forwards valid coaching events", () => {
    const onMessage = vi.fn();

    render(<TestComponent onMessage={onMessage} />);

    act(() => {
      FakeWebSocket.instances[0]?.sendMessage(validEvent);
    });

    expect(onMessage).toHaveBeenCalledWith(validEvent);
  });

  it("ignores invalid coaching events", () => {
    const onMessage = vi.fn();

    render(<TestComponent onMessage={onMessage} />);

    act(() => {
      FakeWebSocket.instances[0]?.sendMessage({
        ...validEvent,
        action: "invalid",
      });
    });

    expect(onMessage).not.toHaveBeenCalled();
  });

  it("reconnects after the websocket closes", () => {
    render(<TestComponent onMessage={vi.fn()} />);

    const socket = FakeWebSocket.instances[0];

    act(() => {
      socket?.open();
      socket?.disconnect();
      vi.advanceTimersByTime(2_000);
    });

    expect(FakeWebSocket.instances).toHaveLength(2);
  });
});
