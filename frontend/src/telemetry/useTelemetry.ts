import { useEffect, useState } from 'react'

import type { TelemetryMessage } from './types'


interface UseTelemetryOptions {
  onMessage: (
    message: TelemetryMessage,
  ) => void

  onConnected?: () => void
}


const RECONNECT_DELAY_MS = 2_000


export function useTelemetry({
  onMessage,
  onConnected,
}: UseTelemetryOptions): boolean {
  const [connected, setConnected] =
    useState(false)

  useEffect(() => {
    let websocket: WebSocket | null = null
    let reconnectTimer:
      ReturnType<typeof setTimeout> | null = null

    let stopped = false


    function scheduleReconnect(): void {
      if (
        stopped ||
        reconnectTimer !== null
      ) {
        return
      }

      reconnectTimer = setTimeout(
        () => {
          reconnectTimer = null

          if (!stopped) {
            connect()
          }
        },
        RECONNECT_DELAY_MS,
      )
    }


    function connect(): void {
      if (stopped) {
        return
      }

      const protocol =
        window.location.protocol === 'https:'
          ? 'wss'
          : 'ws'

      const socket = new WebSocket(
        `${protocol}://${window.location.host}/ws/telemetry`,
      )

      websocket = socket

      socket.onopen = () => {
        if (
          stopped ||
          websocket !== socket
        ) {
          return
        }

        setConnected(true)

        /*
         * Bei jeder erfolgreich hergestellten Verbindung
         * darf der Aufrufer seinen Zustand synchronisieren.
         *
         * Das gilt sowohl für den ersten Connect als auch
         * für spätere Reconnects.
         */
        onConnected?.()
      }

      socket.onmessage = (event) => {
        if (
          stopped ||
          websocket !== socket ||
          typeof event.data !== 'string'
        ) {
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

      socket.onerror = () => {
        if (
          stopped ||
          websocket !== socket
        ) {
          return
        }

        setConnected(false)

        /*
         * onclose ist der einzige Pfad, der einen
         * Reconnect plant.
         */
        socket.close()
      }

      socket.onclose = () => {
        if (
          stopped ||
          websocket !== socket
        ) {
          return
        }

        websocket = null
        setConnected(false)

        scheduleReconnect()
      }
    }


    connect()

    return () => {
      stopped = true

      if (reconnectTimer !== null) {
        clearTimeout(reconnectTimer)
        reconnectTimer = null
      }

      if (websocket !== null) {
        const socket = websocket
        websocket = null

        socket.close()
      }
    }
  }, [onConnected, onMessage])

  return connected
}