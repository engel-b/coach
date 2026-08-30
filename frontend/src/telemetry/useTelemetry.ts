import { useEffect, useState } from 'react'

import type { TelemetryMessage } from './types'


interface UseTelemetryOptions {
  onMessage: (
    message: TelemetryMessage,
  ) => void
}


export function useTelemetry({
  onMessage,
}: UseTelemetryOptions): boolean {
  const [connected, setConnected] =
    useState(false)

  useEffect(() => {
    const protocol =
      window.location.protocol === 'https:'
        ? 'wss'
        : 'ws'

    const websocket = new WebSocket(
      `${protocol}://${window.location.host}/ws/telemetry`,
    )

    websocket.onopen = () => {
      setConnected(true)
    }

    websocket.onclose = () => {
      setConnected(false)
    }

    websocket.onerror = () => {
      setConnected(false)
    }

    websocket.onmessage = (event) => {
      if (typeof event.data !== 'string') {
        return
      }

      try {
        const message = JSON.parse(
          event.data,
        ) as TelemetryMessage

        onMessage(message)
      } catch {
        // Ungültige Telemetrie-Nachrichten ignorieren.
      }
    }

    return () => {
      websocket.close()
    }
  }, [onMessage])

  return connected
}