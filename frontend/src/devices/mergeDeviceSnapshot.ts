import type { DeviceState } from "./types";

/*
 * Führt einen REST-Snapshot mit dem bereits bekannten
 * lokalen Gerätezustand zusammen.
 *
 * Hintergrund:
 *
 *   1. WebSocket liefert z. B. Bike-Telemetrie um 10:00:05.
 *   2. Ein bereits laufender GET /api/devices liefert danach
 *      einen älteren Snapshot von 10:00:03.
 *
 * Ein einfaches setDevices(snapshot) würde dann die neueren
 * Live-Daten wieder überschreiben.
 *
 * Deshalb gewinnt für dieselbe deviceId immer der Zustand
 * mit dem neueren lastSeen-Zeitpunkt.
 */
export function mergeDeviceSnapshot(
  currentDevices: DeviceState[],
  snapshotDevices: DeviceState[],
): DeviceState[] {
  const mergedDevices = new Map<string, DeviceState>();

  for (const device of currentDevices) {
    mergedDevices.set(device.deviceId, device);
  }

  for (const snapshotDevice of snapshotDevices) {
    const currentDevice = mergedDevices.get(snapshotDevice.deviceId);

    if (
      currentDevice === undefined ||
      isNewerOrSame(snapshotDevice.lastSeen, currentDevice.lastSeen)
    ) {
      mergedDevices.set(snapshotDevice.deviceId, snapshotDevice);
    }
  }

  return Array.from(mergedDevices.values());
}

function isNewerOrSame(
  candidateTimestamp: string,
  currentTimestamp: string,
): boolean {
  return Date.parse(candidateTimestamp) >= Date.parse(currentTimestamp);
}
