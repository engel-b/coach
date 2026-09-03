import { useEffect, useState } from 'react'

import type { TelemetryMessage } from './types'


interface UseTelemetryOptions {
  onMessage: (
    message: TelemetryMessage,
  ) => void
}


/*
 * Wartezeit nach einem Verbindungsabbruch.
 *
 * Für unseren lokalen Kiosk ist ein kurzer konstanter Retry sinnvoll:
 * Das Backend läuft auf derselben Maschine und sollte normalerweise
 * innerhalb weniger Sekunden wieder erreichbar sein.
 */
const RECONNECT_DELAY_MS = 2_000


export function useTelemetry({
  onMessage,
}: UseTelemetryOptions): boolean {
  const [connected, setConnected] =
    useState(false)

  useEffect(() => {
    let websocket: WebSocket | null = null
    let reconnectTimer:
      ReturnType<typeof setTimeout> | null = null

    /*
     * Verhindert, dass nach dem Unmount des React-Components
     * noch ein Reconnect gestartet wird.
     */
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
        /*
         * Nur der aktuell gültige Socket darf den State verändern.
         */
        if (
          stopped ||
          websocket !== socket
        ) {
          return
        }

        setConnected(true)
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
         * close() sorgt dafür, dass der normale onclose-Pfad
         * den Reconnect plant.
         *
         * Dadurch haben wir nur eine Stelle, die tatsächlich
         * einen Retry-Timer erzeugt.
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
        /*
         * Referenz zuerst entfernen.
         *
         * Falls close() anschließend synchron/asynchron onclose
         * auslöst, erkennt der Handler den Socket als veraltet
         * und plant keinen neuen Reconnect.
         */
        const socket = websocket
        websocket = null

        socket.close()
      }
    }
  }, [onMessage])

  return connected
}