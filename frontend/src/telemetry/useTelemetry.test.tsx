// @vitest-environment jsdom

import { act, render } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { useTelemetry } from "./useTelemetry";
import type { TelemetryMessage } from "./types";

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

  sendMessage(message: TelemetryMessage): void {
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

interface TestComponentProps {
  onMessage: (message: TelemetryMessage) => void;

  onConnected?: () => void;
}

function TestComponent({ onMessage, onConnected }: TestComponentProps) {
  const connected = useTelemetry({
    onMessage,
    onConnected,
  });

  return <div>{connected ? "connected" : "disconnected"}</div>;
}

describe("useTelemetry", () => {
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

  it("connects when mounted", () => {
    const onMessage = vi.fn();

    render(<TestComponent onMessage={onMessage} />);

    expect(FakeWebSocket.instances).toHaveLength(1);

    expect(FakeWebSocket.instances[0]?.url).toContain("/ws/telemetry");
  });

  it("calls onConnected after the websocket opens", () => {
    const onMessage = vi.fn();
    const onConnected = vi.fn();

    render(<TestComponent onMessage={onMessage} onConnected={onConnected} />);

    const socket = FakeWebSocket.instances[0];

    expect(socket).toBeDefined();

    /*
     * Das bloße Erzeugen des WebSockets bedeutet noch
     * keine erfolgreich hergestellte Verbindung.
     */
    expect(onConnected).not.toHaveBeenCalled();

    act(() => {
      socket?.open();
    });

    expect(onConnected).toHaveBeenCalledOnce();
  });

  it("reconnects after the websocket closes", () => {
    const onMessage = vi.fn();

    render(<TestComponent onMessage={onMessage} />);

    const firstSocket = FakeWebSocket.instances[0];

    expect(firstSocket).toBeDefined();

    act(() => {
      firstSocket?.open();
    });

    act(() => {
      firstSocket?.disconnect();
    });

    /*
     * Vor Ablauf der Retry-Zeit darf noch kein zweiter
     * WebSocket existieren.
     */
    expect(FakeWebSocket.instances).toHaveLength(1);

    act(() => {
      vi.advanceTimersByTime(1_999);
    });

    expect(FakeWebSocket.instances).toHaveLength(1);

    /*
     * Nach insgesamt 2 Sekunden wird genau ein neuer
     * Verbindungsversuch gestartet.
     */
    act(() => {
      vi.advanceTimersByTime(1);
    });

    expect(FakeWebSocket.instances).toHaveLength(2);
  });

  it("calls onConnected again after a successful reconnect", () => {
    const onMessage = vi.fn();
    const onConnected = vi.fn();

    render(<TestComponent onMessage={onMessage} onConnected={onConnected} />);

    const firstSocket = FakeWebSocket.instances[0];

    expect(firstSocket).toBeDefined();

    act(() => {
      firstSocket?.open();
    });

    expect(onConnected).toHaveBeenCalledOnce();

    act(() => {
      firstSocket?.disconnect();
    });

    /*
     * Ein Disconnect allein ist noch kein erfolgreicher
     * Reconnect.
     */
    expect(onConnected).toHaveBeenCalledOnce();

    act(() => {
      vi.advanceTimersByTime(2_000);
    });

    expect(FakeWebSocket.instances).toHaveLength(2);

    const secondSocket = FakeWebSocket.instances[1];

    expect(secondSocket).toBeDefined();

    /*
     * Auch der neue WebSocket zählt erst als verbunden,
     * wenn sein open-Event eintrifft.
     */
    expect(onConnected).toHaveBeenCalledOnce();

    act(() => {
      secondSocket?.open();
    });

    expect(onConnected).toHaveBeenCalledTimes(2);
  });

  it("does not reconnect after unmount", () => {
    const onMessage = vi.fn();

    const result = render(<TestComponent onMessage={onMessage} />);

    const firstSocket = FakeWebSocket.instances[0];

    expect(firstSocket).toBeDefined();

    result.unmount();

    expect(firstSocket?.close).toHaveBeenCalledOnce();

    act(() => {
      vi.advanceTimersByTime(10_000);
    });

    /*
     * Das Cleanup darf keinen neuen Socket mehr zulassen.
     */
    expect(FakeWebSocket.instances).toHaveLength(1);
  });

  it("forwards telemetry messages", () => {
    const onMessage = vi.fn();

    render(<TestComponent onMessage={onMessage} />);

    const socket = FakeWebSocket.instances[0];

    const message: TelemetryMessage = {
      type: "heart_rate.sample",
      timestamp: "2026-09-03T09:00:00Z",
      deviceId: "test-heart-rate",
      payload: {
        bpm: 142,
      },
    };

    act(() => {
      socket?.sendMessage(message);
    });

    expect(onMessage).toHaveBeenCalledOnce();

    expect(onMessage).toHaveBeenCalledWith(message);
  });

  it("does not forward invalid telemetry messages", () => {
    const onMessage = vi.fn();

    render(<TestComponent onMessage={onMessage} />);

    const socket = FakeWebSocket.instances[0];

    /*
     * Syntaktisch korrektes JSON, aber fachlich ungültig:
     * bpm muss eine Zahl sein.
     */
    act(() => {
      socket?.onmessage?.(
        new MessageEvent("message", {
          data: JSON.stringify({
            type: "heart_rate.sample",
            timestamp: "2026-09-03T09:00:00Z",
            deviceId: "test-heart-rate",
            payload: {
              bpm: "invalid",
            },
          }),
        }),
      );
    });

    expect(onMessage).not.toHaveBeenCalled();
  });

  it("does not forward malformed JSON", () => {
    const onMessage = vi.fn();

    render(<TestComponent onMessage={onMessage} />);

    const socket = FakeWebSocket.instances[0];

    /*
     * Hier scheitert bereits JSON.parse().
     * Auch das darf den WebSocket-Handler nicht nach außen
     * durchbrechen lassen.
     */
    act(() => {
      socket?.onmessage?.(
        new MessageEvent("message", {
          data: "{not-valid-json",
        }),
      );
    });

    expect(onMessage).not.toHaveBeenCalled();
  });
});
