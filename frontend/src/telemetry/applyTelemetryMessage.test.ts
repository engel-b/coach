import { describe, expect, it } from "vitest";

import type { DeviceState } from "../devices/types";
import { applyTelemetryMessage } from "./applyTelemetryMessage";
import type { TelemetryMessage } from "./types";

describe("applyTelemetryMessage", () => {
  it("creates a heart-rate device from a sample", () => {
    const message: TelemetryMessage = {
      type: "heart_rate.sample",
      timestamp: "2026-09-03T08:00:00Z",
      deviceId: "test-heart-rate",
      payload: {
        bpm: 142,
      },
    };

    const result = applyTelemetryMessage([], message);

    expect(result).toEqual([
      {
        deviceId: "test-heart-rate",
        deviceType: "heart_rate",
        deviceName: "Heart Rate Sensor",
        status: "connected",
        lastSeen: "2026-09-03T08:00:00Z",
        heartRateBpm: 142,
        speedKmh: null,
        cadenceRpm: null,
        powerW: null,
        resistance: null,
      },
    ]);
  });

  it("creates a bike device from telemetry", () => {
    const message: TelemetryMessage = {
      type: "bike.telemetry",
      timestamp: "2026-09-03T08:00:00Z",
      deviceId: "test-bike",
      payload: {
        speedKmh: 28.4,
        cadenceRpm: 82.5,
        powerW: 175,
        resistance: 12,
      },
    };

    const result = applyTelemetryMessage([], message);

    expect(result).toEqual([
      {
        deviceId: "test-bike",
        deviceType: "bike",
        deviceName: "FTMS Bike",
        status: "connected",
        lastSeen: "2026-09-03T08:00:00Z",
        heartRateBpm: null,
        speedKmh: 28.4,
        cadenceRpm: 82.5,
        powerW: 175,
        resistance: 12,
      },
    ]);
  });

  it("preserves previous bike values for partial telemetry", () => {
    const currentDevices: DeviceState[] = [
      {
        deviceId: "test-bike",
        deviceType: "bike",
        deviceName: "MERACH",
        status: "connected",
        lastSeen: "2026-09-03T08:00:00Z",
        heartRateBpm: null,
        speedKmh: 28.4,
        cadenceRpm: 82.5,
        powerW: 175,
        resistance: 12,
      },
    ];

    const message: TelemetryMessage = {
      type: "bike.telemetry",
      timestamp: "2026-09-03T08:00:01Z",
      deviceId: "test-bike",
      payload: {
        powerW: 190,
      },
    };

    const result = applyTelemetryMessage(currentDevices, message);

    expect(result).toEqual([
      {
        deviceId: "test-bike",
        deviceType: "bike",
        deviceName: "MERACH",
        status: "connected",
        lastSeen: "2026-09-03T08:00:01Z",
        heartRateBpm: null,
        speedKmh: 28.4,
        cadenceRpm: 82.5,
        powerW: 190,
        resistance: 12,
      },
    ]);
  });

  it("preserves telemetry when a status event arrives later", () => {
    const currentDevices: DeviceState[] = [
      {
        deviceId: "test-bike",
        deviceType: "bike",
        deviceName: "FTMS Bike",
        status: "connected",
        lastSeen: "2026-09-03T08:00:00Z",
        heartRateBpm: null,
        speedKmh: 28.4,
        cadenceRpm: 82.5,
        powerW: 175,
        resistance: 12,
      },
    ];

    const message: TelemetryMessage = {
      type: "device.status_changed",
      timestamp: "2026-09-03T08:00:01Z",
      deviceId: "test-bike",
      payload: {
        deviceType: "bike",
        deviceName: "MERACH",
        status: "connected",
      },
    };

    const result = applyTelemetryMessage(currentDevices, message);

    expect(result).toEqual([
      {
        deviceId: "test-bike",
        deviceType: "bike",
        deviceName: "MERACH",
        status: "connected",
        lastSeen: "2026-09-03T08:00:01Z",
        heartRateBpm: null,
        speedKmh: 28.4,
        cadenceRpm: 82.5,
        powerW: 175,
        resistance: 12,
      },
    ]);
  });
});
