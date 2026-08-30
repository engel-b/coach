import type { DeviceState } from '../devices/types'

/**
 * Lädt den aktuellen Zustand aller Geräte.
 *
 * fetch() ist die eingebaute Browser-HTTP-API.
 *
 * Java-Vergleich grob:
 *
 *   RestClient / WebClient
 *
 * Nur ohne zusätzliches Framework.
 */
export async function getDevices(): Promise<DeviceState[]> {
  const response = await fetch('/api/devices')

  if (!response.ok) {
    throw new Error(
      `Could not load devices: HTTP ${response.status}`,
    )
  }

  /*
   * response.json() kann zur Laufzeit natürlich beliebiges JSON liefern.
   *
   * Der Cast sagt TypeScript:
   * "Ab hier behandeln wir dieses JSON als DeviceState[]."
   *
   * Später können wir hier Runtime-Validierung ergänzen.
   */
  return (await response.json()) as DeviceState[]
}

