import { describe, expect, it } from "vitest";

import { mergeDeviceSnapshot } from "./mergeDeviceSnapshot";
import type { DeviceState } from "./types";

function createBike(overrides: Partial<DeviceState> = {}): DeviceState {
  return {
    deviceId: "test-bike",
    deviceType: "bike",
    deviceName: "FTMS Bike",
    status: "connected",
    lastSeen: "2026-09-03T10:00:00Z",
    heartRateBpm: null,
    speedKmh: 25,
    cadenceRpm: 80,
    powerW: 150,
    resistance: 10,
    ...overrides,
  };
}

describe("mergeDeviceSnapshot", () => {
  it("adds devices that only exist in the snapshot", () => {
    const snapshotDevice = createBike();

    const result = mergeDeviceSnapshot([], [snapshotDevice]);

    expect(result).toEqual([snapshotDevice]);
  });

  it("keeps devices that only exist in the current state", () => {
    const currentDevice = createBike();

    const result = mergeDeviceSnapshot([currentDevice], []);

    expect(result).toEqual([currentDevice]);
  });

  it("uses a newer snapshot for the same device", () => {
    const currentDevice = createBike({
      lastSeen: "2026-09-03T10:00:00Z",
      powerW: 150,
    });

    const snapshotDevice = createBike({
      lastSeen: "2026-09-03T10:00:05Z",
      powerW: 175,
    });

    const result = mergeDeviceSnapshot([currentDevice], [snapshotDevice]);

    expect(result).toEqual([snapshotDevice]);
  });

  it("does not overwrite newer live data with an older snapshot", () => {
    const liveDevice = createBike({
      lastSeen: "2026-09-03T10:00:05Z",
      speedKmh: 31.2,
      cadenceRpm: 88,
      powerW: 210,
    });

    const olderSnapshotDevice = createBike({
      lastSeen: "2026-09-03T10:00:03Z",
      speedKmh: 27.4,
      cadenceRpm: 81,
      powerW: 170,
    });

    const result = mergeDeviceSnapshot([liveDevice], [olderSnapshotDevice]);

    expect(result).toEqual([liveDevice]);
  });

  it("uses the snapshot when timestamps are equal", () => {
    const currentDevice = createBike({
      deviceName: "unknown",
      powerW: null,
    });

    const snapshotDevice = createBike({
      deviceName: "MERACH",
      powerW: 175,
    });

    const result = mergeDeviceSnapshot([currentDevice], [snapshotDevice]);

    expect(result).toEqual([snapshotDevice]);
  });
});
