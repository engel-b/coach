import type { DeviceState } from '../devices/types'
import type { TelemetryMessage } from './types'


/*
 * Wendet genau eine Telemetrie-Nachricht auf den aktuellen
 * Device-State an.
 *
 * Die Funktion ist absichtlich "pure":
 *
 * - kein React
 * - kein WebSocket
 * - kein setState()
 * - keine Seiteneffekte
 *
 * Java-Vergleich:
 *
 *   List<DeviceState> apply(
 *       List<DeviceState> current,
 *       TelemetryMessage message
 *   )
 *
 * Dadurch können wir die fachliche Merge-/Upsert-Logik später
 * unabhängig von React testen.
 */
export function applyTelemetryMessage(
  currentDevices: DeviceState[],
  message: TelemetryMessage,
): DeviceState[] {
  if (message.type === 'device.status_changed') {
    return applyDeviceStatusChanged(
      currentDevices,
      message,
    )
  }

  if (message.type === 'heart_rate.sample') {
    return applyHeartRateSample(
      currentDevices,
      message,
    )
  }

  if (message.type === 'bike.telemetry') {
    return applyBikeTelemetry(
      currentDevices,
      message,
    )
  }

  /*
   * Unbekannte Eventtypen verändern den aktuellen State nicht.
   */
  return currentDevices
}


function applyDeviceStatusChanged(
  currentDevices: DeviceState[],
  message: TelemetryMessage,
): DeviceState[] {
  const deviceType =
    message.payload.deviceType

  const deviceName =
    message.payload.deviceName

  const status =
    message.payload.status

  /*
   * WebSocket-Nachrichten überschreiten eine Prozessgrenze.
   * Deshalb übernehmen wir die Payload nicht ungeprüft.
   */
  if (
    typeof deviceType !== 'string' ||
    typeof deviceName !== 'string' ||
    typeof status !== 'string'
  ) {
    return currentDevices
  }

  const existingDevice =
    findDevice(
      currentDevices,
      message.deviceId,
    )

  const updatedDevice: DeviceState = {
    device_id: message.deviceId,
    device_type:
      deviceType as DeviceState['device_type'],
    device_name: deviceName,
    status:
      status as DeviceState['status'],
    last_seen: message.timestamp,

    /*
     * Ein Status-Event enthält keine Messwerte.
     * Bereits bekannte Telemetrie bleibt deshalb erhalten.
     */
    heart_rate_bpm:
      existingDevice?.heart_rate_bpm ??
      null,

    speed_kmh:
      existingDevice?.speed_kmh ??
      null,

    cadence_rpm:
      existingDevice?.cadence_rpm ??
      null,

    power_w:
      existingDevice?.power_w ??
      null,

    resistance:
      existingDevice?.resistance ??
      null,
  }

  return upsertDevice(
    currentDevices,
    updatedDevice,
  )
}


function applyHeartRateSample(
  currentDevices: DeviceState[],
  message: TelemetryMessage,
): DeviceState[] {
  const bpm =
    message.payload.bpm

  if (typeof bpm !== 'number') {
    return currentDevices
  }

  const existingDevice =
    findDevice(
      currentDevices,
      message.deviceId,
    )

  /*
   * Ein Heart-Rate-Sample kann vor dem Status-Event eintreffen.
   * Deshalb erzeugen wir bei Bedarf direkt einen Device-State.
   */
  const heartRateDevice: DeviceState = {
    device_id: message.deviceId,
    device_type: 'heart_rate',
    device_name:
      existingDevice?.device_name ??
      'Heart Rate Sensor',
    status: 'connected',
    last_seen: message.timestamp,

    heart_rate_bpm: bpm,

    speed_kmh:
      existingDevice?.speed_kmh ??
      null,

    cadence_rpm:
      existingDevice?.cadence_rpm ??
      null,

    power_w:
      existingDevice?.power_w ??
      null,

    resistance:
      existingDevice?.resistance ??
      null,
  }

  return upsertDevice(
    currentDevices,
    heartRateDevice,
  )
}


function applyBikeTelemetry(
  currentDevices: DeviceState[],
  message: TelemetryMessage,
): DeviceState[] {
  const speedKmh =
    message.payload.speedKmh

  const cadenceRpm =
    message.payload.cadenceRpm

  const powerW =
    message.payload.powerW

  const resistance =
    message.payload.resistance

  const existingDevice =
    findDevice(
      currentDevices,
      message.deviceId,
    )

  /*
   * Auch Bike-Telemetrie darf vor einem Status-Event eintreffen.
   */
  const bikeDevice: DeviceState = {
    device_id: message.deviceId,
    device_type: 'bike',
    device_name:
      existingDevice?.device_name ??
      'FTMS Bike',
    status: 'connected',
    last_seen: message.timestamp,

    heart_rate_bpm:
      existingDevice?.heart_rate_bpm ??
      null,

    /*
     * FTMS-Nachrichten können partiell sein.
     * Ein fehlender Wert darf einen bereits bekannten Wert
     * deshalb nicht auf null zurücksetzen.
     */
    speed_kmh:
      typeof speedKmh === 'number'
        ? speedKmh
        : existingDevice?.speed_kmh ?? null,

    cadence_rpm:
      typeof cadenceRpm === 'number'
        ? cadenceRpm
        : existingDevice?.cadence_rpm ?? null,

    power_w:
      typeof powerW === 'number'
        ? powerW
        : existingDevice?.power_w ?? null,

    resistance:
      typeof resistance === 'number'
        ? resistance
        : existingDevice?.resistance ?? null,
  }

  return upsertDevice(
    currentDevices,
    bikeDevice,
  )
}


function findDevice(
  devices: DeviceState[],
  deviceId: string,
): DeviceState | undefined {
  return devices.find(
    (device) =>
      device.device_id === deviceId,
  )
}


function upsertDevice(
  devices: DeviceState[],
  updatedDevice: DeviceState,
): DeviceState[] {
  return [
    ...devices.filter(
      (device) =>
        device.device_id !==
        updatedDevice.device_id,
    ),
    updatedDevice,
  ]
}