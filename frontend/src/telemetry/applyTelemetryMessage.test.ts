import { describe, expect, it } from 'vitest'

import type { DeviceState } from '../devices/types'
import { applyTelemetryMessage } from './applyTelemetryMessage'
import type { TelemetryMessage } from './types'


describe('applyTelemetryMessage', () => {
  it('creates a heart-rate device from a sample', () => {
    const message: TelemetryMessage = {
      type: 'heart_rate.sample',
      timestamp: '2026-09-03T08:00:00Z',
      deviceId: 'test-heart-rate',
      payload: {
        bpm: 142,
      },
    }

    const result =
      applyTelemetryMessage(
        [],
        message,
      )

    expect(result).toEqual([
      {
        device_id: 'test-heart-rate',
        device_type: 'heart_rate',
        device_name: 'Heart Rate Sensor',
        status: 'connected',
        last_seen: '2026-09-03T08:00:00Z',
        heart_rate_bpm: 142,
        speed_kmh: null,
        cadence_rpm: null,
        power_w: null,
        resistance: null,
      },
    ])
  })


  it('creates a bike device from telemetry', () => {
    const message: TelemetryMessage = {
      type: 'bike.telemetry',
      timestamp: '2026-09-03T08:00:00Z',
      deviceId: 'test-bike',
      payload: {
        speedKmh: 28.4,
        cadenceRpm: 82.5,
        powerW: 175,
        resistance: 12,
      },
    }

    const result =
      applyTelemetryMessage(
        [],
        message,
      )

    expect(result).toEqual([
      {
        device_id: 'test-bike',
        device_type: 'bike',
        device_name: 'FTMS Bike',
        status: 'connected',
        last_seen: '2026-09-03T08:00:00Z',
        heart_rate_bpm: null,
        speed_kmh: 28.4,
        cadence_rpm: 82.5,
        power_w: 175,
        resistance: 12,
      },
    ])
  })


  it('preserves previous bike values for partial telemetry', () => {
    const currentDevices: DeviceState[] = [
      {
        device_id: 'test-bike',
        device_type: 'bike',
        device_name: 'MERACH',
        status: 'connected',
        last_seen: '2026-09-03T08:00:00Z',
        heart_rate_bpm: null,
        speed_kmh: 28.4,
        cadence_rpm: 82.5,
        power_w: 175,
        resistance: 12,
      },
    ]

    const message: TelemetryMessage = {
      type: 'bike.telemetry',
      timestamp: '2026-09-03T08:00:01Z',
      deviceId: 'test-bike',
      payload: {
        powerW: 190,
      },
    }

    const result =
      applyTelemetryMessage(
        currentDevices,
        message,
      )

    expect(result).toEqual([
      {
        device_id: 'test-bike',
        device_type: 'bike',
        device_name: 'MERACH',
        status: 'connected',
        last_seen: '2026-09-03T08:00:01Z',
        heart_rate_bpm: null,
        speed_kmh: 28.4,
        cadence_rpm: 82.5,
        power_w: 190,
        resistance: 12,
      },
    ])
  })


  it('preserves telemetry when a status event arrives later', () => {
    const currentDevices: DeviceState[] = [
      {
        device_id: 'test-bike',
        device_type: 'bike',
        device_name: 'FTMS Bike',
        status: 'connected',
        last_seen: '2026-09-03T08:00:00Z',
        heart_rate_bpm: null,
        speed_kmh: 28.4,
        cadence_rpm: 82.5,
        power_w: 175,
        resistance: 12,
      },
    ]

    const message: TelemetryMessage = {
      type: 'device.status_changed',
      timestamp: '2026-09-03T08:00:01Z',
      deviceId: 'test-bike',
      payload: {
        deviceType: 'bike',
        deviceName: 'MERACH',
        status: 'connected',
      },
    }

    const result =
      applyTelemetryMessage(
        currentDevices,
        message,
      )

    expect(result).toEqual([
      {
        device_id: 'test-bike',
        device_type: 'bike',
        device_name: 'MERACH',
        status: 'connected',
        last_seen: '2026-09-03T08:00:01Z',
        heart_rate_bpm: null,
        speed_kmh: 28.4,
        cadence_rpm: 82.5,
        power_w: 175,
        resistance: 12,
      },
    ])
  })
})