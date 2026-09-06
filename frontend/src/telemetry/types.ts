export interface TelemetryMessage {
  type: string
  timestamp: string
  deviceId: string
  payload: Record<string, unknown>
}


export interface HeartRateSamplePayload {
  bpm: number
}


export interface BikeTelemetryPayload {
  powerW?: number
  cadenceRpm?: number
  speedKmh?: number
  distanceM?: number
  resistance?: number
}
