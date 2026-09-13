import { useEffect, useState } from "react";

import { parseLiveCoachingEvent } from "./parseLiveCoachingEvent";
import type { LiveCoachingEvent } from "./types";

interface UseLiveCoachingOptions {
  onMessage: (message: LiveCoachingEvent) => void;
}

const RECONNECT_DELAY_MS = 2_000;

/**
 * Hält die WebSocket-Verbindung zum fachlichen Live-Coaching-Stream.
 *
 * Der Stream ist bewusst von /ws/telemetry getrennt: Telemetrie enthält
 * Rohdaten, während dieser Stream nur relevante Coaching-Entscheidungen
 * transportiert.
 */
export function useLiveCoaching({
  onMessage,
}: UseLiveCoachingOptions): boolean {
  const [connected, setConnected] = useState(false);

  useEffect(() => {
    let websocket: WebSocket | null = null;
    let reconnectTimer: ReturnType<typeof setTimeout> | null = null;
    let stopped = false;

    function scheduleReconnect(): void {
      if (stopped || reconnectTimer !== null) {
        return;
      }

      reconnectTimer = setTimeout(() => {
        reconnectTimer = null;

        if (!stopped) {
          connect();
        }
      }, RECONNECT_DELAY_MS);
    }

    function connect(): void {
      if (stopped) {
        return;
      }

      const protocol = window.location.protocol === "https:" ? "wss" : "ws";
      const socket = new WebSocket(
        `${protocol}://${window.location.host}/ws/coaching`,
      );

      websocket = socket;

      socket.onopen = () => {
        if (stopped || websocket !== socket) {
          return;
        }

        setConnected(true);
      };

      socket.onmessage = (event) => {
        if (stopped || websocket !== socket || typeof event.data !== "string") {
          return;
        }

        try {
          const parsed: unknown = JSON.parse(event.data);
          const message = parseLiveCoachingEvent(parsed);

          if (message !== null) {
            onMessage(message);
          }
        } catch {
          // Ungültiges JSON wird an der Systemgrenze verworfen.
        }
      };

      socket.onerror = () => {
        if (stopped || websocket !== socket) {
          return;
        }

        setConnected(false);
        socket.close();
      };

      socket.onclose = () => {
        if (stopped || websocket !== socket) {
          return;
        }

        websocket = null;
        setConnected(false);
        scheduleReconnect();
      };
    }

    connect();

    return () => {
      stopped = true;

      if (reconnectTimer !== null) {
        clearTimeout(reconnectTimer);
        reconnectTimer = null;
      }

      if (websocket !== null) {
        const socket = websocket;
        websocket = null;
        socket.close();
      }
    };
  }, [onMessage]);

  return connected;
}
