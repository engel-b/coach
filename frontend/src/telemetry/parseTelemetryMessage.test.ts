import { describe, expect, it } from "vitest";

import { parseTelemetryMessage } from "./parseTelemetryMessage";

describe("parseTelemetryMessage", () => {
  it("accepts a valid heart-rate sample", () => {
    const result = parseTelemetryMessage({
      type: "heart_rate.sample",
      timestamp: "2026-09-03T09:00:00Z",
      deviceId: "heart-rate-1",
      payload: {
        bpm: 142,
      },
    });

    expect(result).toEqual({
      type: "heart_rate.sample",
      timestamp: "2026-09-03T09:00:00Z",
      deviceId: "heart-rate-1",
      payload: {
        bpm: 142,
      },
    });
  });

  it("rejects a heart-rate sample without bpm", () => {
    const result = parseTelemetryMessage({
      type: "heart_rate.sample",
      timestamp: "2026-09-03T09:00:00Z",
      deviceId: "heart-rate-1",
      payload: {},
    });

    expect(result).toBeNull();
  });

  it("rejects a heart-rate sample with invalid bpm", () => {
    const result = parseTelemetryMessage({
      type: "heart_rate.sample",
      timestamp: "2026-09-03T09:00:00Z",
      deviceId: "heart-rate-1",
      payload: {
        bpm: "142",
      },
    });

    expect(result).toBeNull();
  });

  it("accepts valid bike telemetry", () => {
    const result = parseTelemetryMessage({
      type: "bike.telemetry",
      timestamp: "2026-09-03T09:00:00Z",
      deviceId: "bike-1",
      payload: {
        powerW: 180,
        cadenceRpm: 82,
        speedKmh: 31.4,
        resistance: 7,
      },
    });

    expect(result).not.toBeNull();
  });

  it("accepts partial bike telemetry", () => {
    const result = parseTelemetryMessage({
      type: "bike.telemetry",
      timestamp: "2026-09-03T09:00:00Z",
      deviceId: "bike-1",
      payload: {
        cadenceRpm: 82,
      },
    });

    expect(result).not.toBeNull();
  });

  it("accepts bike telemetry with null values", () => {
    const result = parseTelemetryMessage({
      type: "bike.telemetry",
      timestamp: "2026-09-03T09:00:00Z",
      deviceId: "bike-1",
      payload: {
        speedKmh: 24.5,
        cadenceRpm: 81,
        powerW: null,
        resistance: null,
      },
    });

    expect(result).not.toBeNull();
  });

  it("rejects bike telemetry with invalid values", () => {
    const result = parseTelemetryMessage({
      type: "bike.telemetry",
      timestamp: "2026-09-03T09:00:00Z",
      deviceId: "bike-1",
      payload: {
        powerW: "180",
      },
    });

    expect(result).toBeNull();
  });

  it("accepts a valid device status change", () => {
    const result = parseTelemetryMessage({
      type: "device.status_changed",
      timestamp: "2026-09-03T09:00:00Z",
      deviceId: "bike-1",
      payload: {
        deviceType: "bike",
        deviceName: "MERACH",
        status: "connected",
      },
    });

    expect(result).not.toBeNull();
  });

  it("rejects an incomplete device status change", () => {
    const result = parseTelemetryMessage({
      type: "device.status_changed",
      timestamp: "2026-09-03T09:00:00Z",
      deviceId: "bike-1",
      payload: {
        status: "connected",
      },
    });

    expect(result).toBeNull();
  });

  it("rejects an unknown telemetry type", () => {
    const result = parseTelemetryMessage({
      type: "something.new",
      timestamp: "2026-09-03T09:00:00Z",
      deviceId: "device-1",
      payload: {},
    });

    expect(result).toBeNull();
  });

  it("rejects malformed envelopes", () => {
    expect(parseTelemetryMessage(null)).toBeNull();

    expect(
      parseTelemetryMessage({
        type: "heart_rate.sample",
      }),
    ).toBeNull();

    expect(
      parseTelemetryMessage({
        type: "heart_rate.sample",
        timestamp: "2026-09-03T09:00:00Z",
        deviceId: "heart-rate-1",
        payload: [],
      }),
    ).toBeNull();
  });
});
