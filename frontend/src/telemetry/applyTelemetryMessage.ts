import type { DeviceState } from '../devices/types'
import type { TelemetryMessage } from './types'


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

  return currentDevices
}


function applyDeviceStatusChanged(
  currentDevices: DeviceState[],
  message: TelemetryMessage,
): DeviceState[] {
  const deviceType = message.payload.deviceType
  const deviceName = message.payload.deviceName
  const status = message.payload.status

  if (
    typeof deviceType !== 'string' ||
    typeof deviceName !== 'string' ||
    typeof status !== 'string'
  ) {
    return currentDevices
  }

  const existingDevice =
    findDevice(currentDevices, message.deviceId)

  const updatedDevice: DeviceState = {
    deviceId: message.deviceId,
    deviceType:
      deviceType as DeviceState['deviceType'],
    deviceName,
    status:
      status as DeviceState['status'],
    lastSeen: message.timestamp,
    heartRateBpm:
      existingDevice?.heartRateBpm ?? null,
    speedKmh:
      existingDevice?.speedKmh ?? null,
    cadenceRpm:
      existingDevice?.cadenceRpm ?? null,
    powerW:
      existingDevice?.powerW ?? null,
    resistance:
      existingDevice?.resistance ?? null,
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
  const bpm = message.payload.bpm

  if (typeof bpm !== 'number') {
    return currentDevices
  }

  const existingDevice =
    findDevice(currentDevices, message.deviceId)

  const heartRateDevice: DeviceState = {
    deviceId: message.deviceId,
    deviceType: 'heart_rate',
    deviceName:
      existingDevice?.deviceName ??
      'Heart Rate Sensor',
    status: 'connected',
    lastSeen: message.timestamp,
    heartRateBpm: bpm,
    speedKmh:
      existingDevice?.speedKmh ?? null,
    cadenceRpm:
      existingDevice?.cadenceRpm ?? null,
    powerW:
      existingDevice?.powerW ?? null,
    resistance:
      existingDevice?.resistance ?? null,
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
  const speedKmh = message.payload.speedKmh
  const cadenceRpm = message.payload.cadenceRpm
  const powerW = message.payload.powerW
  const resistance = message.payload.resistance

  const existingDevice =
    findDevice(currentDevices, message.deviceId)

  const bikeDevice: DeviceState = {
    deviceId: message.deviceId,
    deviceType: 'bike',
    deviceName:
      existingDevice?.deviceName ??
      'FTMS Bike',
    status: 'connected',
    lastSeen: message.timestamp,
    heartRateBpm:
      existingDevice?.heartRateBpm ?? null,
    speedKmh:
      typeof speedKmh === 'number'
        ? speedKmh
        : existingDevice?.speedKmh ?? null,
    cadenceRpm:
      typeof cadenceRpm === 'number'
        ? cadenceRpm
        : existingDevice?.cadenceRpm ?? null,
    powerW:
      typeof powerW === 'number'
        ? powerW
        : existingDevice?.powerW ?? null,
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
    (device) => device.deviceId === deviceId,
  )
}


function upsertDevice(
  devices: DeviceState[],
  updatedDevice: DeviceState,
): DeviceState[] {
  return [
    ...devices.filter(
      (device) =>
        device.deviceId !== updatedDevice.deviceId,
    ),
    updatedDevice,
  ]
}