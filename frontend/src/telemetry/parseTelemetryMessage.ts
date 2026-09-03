import type {
  BikeTelemetryPayload,
  HeartRateSamplePayload,
  TelemetryMessage,
} from './types'


const DEVICE_STATUS_CHANGED =
  'device.status_changed'

const HEART_RATE_SAMPLE =
  'heart_rate.sample'

const BIKE_TELEMETRY =
  'bike.telemetry'


/*
 * Systemgrenze für eingehende WebSocket-Nachrichten.
 *
 * JSON.parse() liefert Daten aus einer externen Quelle.
 * Deshalb behandeln wir sie zunächst als unknown und
 * erzeugen erst nach erfolgreicher Prüfung ein
 * TelemetryMessage.
 *
 * Das entspricht ungefähr dem Validieren eines externen
 * DTOs, bevor es in die eigentliche Anwendung gelangt.
 */
export function parseTelemetryMessage(
  value: unknown,
): TelemetryMessage | null {
  if (!isRecord(value)) {
    return null
  }

  if (
    typeof value.type !== 'string' ||
    typeof value.timestamp !== 'string' ||
    typeof value.deviceId !== 'string' ||
    !isRecord(value.payload)
  ) {
    return null
  }

  switch (value.type) {
    case DEVICE_STATUS_CHANGED:
      return parseDeviceStatusChanged(value)

    case HEART_RATE_SAMPLE:
      return parseHeartRateSample(value)

    case BIKE_TELEMETRY:
      return parseBikeTelemetry(value)

    default:
      return null
  }
}


function parseDeviceStatusChanged(
  value: Record<string, unknown>,
): TelemetryMessage | null {
  const payload = value.payload

  if (!isRecord(payload)) {
    return null
  }

  if (
    typeof payload.deviceType !== 'string' ||
    typeof payload.deviceName !== 'string' ||
    typeof payload.status !== 'string'
  ) {
    return null
  }

  return createTelemetryMessage(
    value,
    payload,
  )
}


function parseHeartRateSample(
  value: Record<string, unknown>,
): TelemetryMessage | null {
  const payload = value.payload

  if (!isRecord(payload)) {
    return null
  }

  if (!isHeartRateSamplePayload(payload)) {
    return null
  }

  return createTelemetryMessage(
    value,
    payload,
  )
}


function parseBikeTelemetry(
  value: Record<string, unknown>,
): TelemetryMessage | null {
  const payload = value.payload

  if (!isRecord(payload)) {
    return null
  }

  if (!isBikeTelemetryPayload(payload)) {
    return null
  }

  return createTelemetryMessage(
    value,
    payload,
  )
}


function createTelemetryMessage(
  value: Record<string, unknown>,
  payload: Record<string, unknown>,
): TelemetryMessage {
  /*
   * Diese Felder wurden bereits in
   * parseTelemetryMessage() geprüft.
   */
  return {
    type: value.type as string,
    timestamp: value.timestamp as string,
    deviceId: value.deviceId as string,
    payload,
  }
}


function isHeartRateSamplePayload(
  payload: Record<string, unknown>,
): payload is Record<string, unknown> &
  HeartRateSamplePayload {
  return (
    typeof payload.bpm === 'number' &&
    Number.isFinite(payload.bpm)
  )
}


function isBikeTelemetryPayload(
  payload: Record<string, unknown>,
): payload is Record<string, unknown> &
  BikeTelemetryPayload {
  return (
    isOptionalFiniteNumber(
      payload.powerW,
    ) &&
    isOptionalFiniteNumber(
      payload.cadenceRpm,
    ) &&
    isOptionalFiniteNumber(
      payload.speedKmh,
    ) &&
    isOptionalFiniteNumber(
      payload.resistance,
    )
  )
}


function isOptionalFiniteNumber(
  value: unknown,
): boolean {
  /*
   * Optionale Messwerte können über die JSON-Grenze
   * auf zwei Arten fehlen:
   *
   *   undefined
   *     Das Feld ist gar nicht vorhanden.
   *
   *   null
   *     Das Feld ist vorhanden, aber der Device Agent
   *     hat für diesen Messwert keinen Wert geliefert.
   *
   * Beides ist für partielle Bike-Telemetrie gültig.
   */
  return (
    value === undefined ||
    value === null ||
    (
      typeof value === 'number' &&
      Number.isFinite(value)
    )
  )
}


function isRecord(
  value: unknown,
): value is Record<string, unknown> {
  return (
    typeof value === 'object' &&
    value !== null &&
    !Array.isArray(value)
  )
}