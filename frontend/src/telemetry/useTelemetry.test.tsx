// @vitest-environment jsdom

import {
  act,
  render,
} from '@testing-library/react'
import {
  afterEach,
  beforeEach,
  describe,
  expect,
  it,
  vi,
} from 'vitest'

import { useTelemetry } from './useTelemetry'
import type { TelemetryMessage } from './types'


class FakeWebSocket {
  static instances: FakeWebSocket[] = []

  readonly url: string

  onopen: (() => void) | null = null
  onclose: (() => void) | null = null
  onerror: (() => void) | null = null
  onmessage:
    | ((event: MessageEvent<string>) => void)
    | null = null

  close = vi.fn(() => {
    this.onclose?.()
  })

  constructor(url: string | URL) {
    this.url = url.toString()

    FakeWebSocket.instances.push(this)
  }

  open(): void {
    this.onopen?.()
  }

  disconnect(): void {
    this.onclose?.()
  }

  sendMessage(
    message: TelemetryMessage,
  ): void {
    this.onmessage?.(
      new MessageEvent(
        'message',
        {
          data: JSON.stringify(message),
        },
      ),
    )
  }

  static reset(): void {
    FakeWebSocket.instances = []
  }
}


interface TestComponentProps {
  onMessage: (
    message: TelemetryMessage,
  ) => void
}


function TestComponent({
  onMessage,
}: TestComponentProps) {
  const connected =
    useTelemetry({
      onMessage,
    })

  return (
    <div>
      {connected
        ? 'connected'
        : 'disconnected'}
    </div>
  )
}


describe('useTelemetry', () => {
  beforeEach(() => {
    vi.useFakeTimers()

    FakeWebSocket.reset()

    vi.stubGlobal(
      'WebSocket',
      FakeWebSocket,
    )
  })


  afterEach(() => {
    vi.runOnlyPendingTimers()
    vi.useRealTimers()
    vi.unstubAllGlobals()
  })


  it('connects when mounted', () => {
    const onMessage = vi.fn()

    render(
      <TestComponent
        onMessage={onMessage}
      />,
    )

    expect(
      FakeWebSocket.instances,
    ).toHaveLength(1)

    expect(
      FakeWebSocket.instances[0]?.url,
    ).toContain('/ws/telemetry')
  })


  it('reconnects after the websocket closes', () => {
    const onMessage = vi.fn()

    render(
      <TestComponent
        onMessage={onMessage}
      />,
    )

    const firstSocket =
      FakeWebSocket.instances[0]

    expect(firstSocket).toBeDefined()

    act(() => {
      firstSocket?.open()
    })

    act(() => {
      firstSocket?.disconnect()
    })

    /*
     * Vor Ablauf der Retry-Zeit darf noch kein zweiter
     * WebSocket existieren.
     */
    expect(
      FakeWebSocket.instances,
    ).toHaveLength(1)

    act(() => {
      vi.advanceTimersByTime(1_999)
    })

    expect(
      FakeWebSocket.instances,
    ).toHaveLength(1)

    /*
     * Nach insgesamt 2 Sekunden wird genau ein neuer
     * Verbindungsversuch gestartet.
     */
    act(() => {
      vi.advanceTimersByTime(1)
    })

    expect(
      FakeWebSocket.instances,
    ).toHaveLength(2)
  })


  it('does not reconnect after unmount', () => {
    const onMessage = vi.fn()

    const result = render(
      <TestComponent
        onMessage={onMessage}
      />,
    )

    const firstSocket =
      FakeWebSocket.instances[0]

    expect(firstSocket).toBeDefined()

    result.unmount()

    expect(
      firstSocket?.close,
    ).toHaveBeenCalledOnce()

    act(() => {
      vi.advanceTimersByTime(10_000)
    })

    /*
     * Das Cleanup darf keinen neuen Socket mehr zulassen.
     */
    expect(
      FakeWebSocket.instances,
    ).toHaveLength(1)
  })


  it('forwards telemetry messages', () => {
    const onMessage = vi.fn()

    render(
      <TestComponent
        onMessage={onMessage}
      />,
    )

    const socket =
      FakeWebSocket.instances[0]

    const message: TelemetryMessage = {
      type: 'heart_rate.sample',
      timestamp: '2026-09-03T09:00:00Z',
      deviceId: 'test-heart-rate',
      payload: {
        bpm: 142,
      },
    }

    act(() => {
      socket?.sendMessage(message)
    })

    expect(onMessage).toHaveBeenCalledOnce()

    expect(onMessage).toHaveBeenCalledWith(
      message,
    )
  })
})