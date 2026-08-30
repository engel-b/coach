import type { DeviceState } from './types'

interface DeviceCardProps {
  device: DeviceState
}

/**
 * React Function Component.
 *
 * Java-Vergleich ist nicht wirklich direkt möglich.
 * Vereinfacht kann man sagen:
 *
 *   Input (Props)
 *       ↓
 *   Funktion
 *       ↓
 *   UI-Baum
 *
 * Das Component verändert DeviceState nicht.
 */
export function DeviceCard({
  device,
}: DeviceCardProps) {
  const connected = device.status === 'connected'

  return (
    <article className="device-card">
      <div className="device-header">
        <div>
          <div className="device-kind">
            ♥ Pulsgurt
          </div>

          <div className="device-name">
            {device.device_name}
          </div>
        </div>

        <div
          className={
            connected
              ? 'status connected'
              : 'status disconnected'
          }
        >
          {connected ? 'Verbunden' : 'Nicht verbunden'}
        </div>
      </div>

      <div className="heart-rate">
        {device.heart_rate_bpm ?? '–'}
        <span>bpm</span>
      </div>
    </article>
  )
}

