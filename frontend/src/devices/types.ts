/**
 * Gerätetypen, die unser Backend momentan kennt.
 *
 * Python:
 *
 *   DeviceType(StrEnum)
 *
 * TypeScript:
 *
 *   String Union Type
 *
 * Anders als ein Java enum existiert dieser Typ nur zur Compile-Zeit.
 */
export type DeviceType = 'heart_rate' | 'bike' | 'scale'

export type DeviceStatus =
  | 'disconnected'
  | 'scanning'
  | 'connecting'
  | 'connected'
  | 'error'

/**
 * Aktueller Zustand eines Geräts.
 *
 * Entspricht dem DeviceState unseres Python-Backends.
 *
 * Wichtig:
 * Das Backend liefert momentan noch snake_case.
 * Deshalb heißen die Properties hier ebenfalls device_id usw.
 *
 * Später können wir unsere öffentliche API konsequent auf camelCase
 * umstellen. Für den ersten Slice lassen wir den Transport erst einmal
 * exakt so, wie FastAPI ihn aktuell liefert.
 */
export interface DeviceState {
  device_id: string
  device_type: DeviceType
  device_name: string
  status: DeviceStatus
  last_seen: string
  heart_rate_bpm: number | null
}

