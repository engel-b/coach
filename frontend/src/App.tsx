import {
  useCallback,
  useEffect,
  useState,
} from 'react'

import { getDevices } from './api/devices'
import { getPersons } from './api/persons'
import { getTrainingRecommendation } from './api/training'
import { startWorkout } from './api/workouts'
import './App.css'
import { CheckInWizard } from './check-in/CheckInWizard'
import type { CheckIn } from './check-in/types'
import { DeviceCard } from './devices/DeviceCard'
import type { DeviceState } from './devices/types'
import { PersonDashboard } from './persons/PersonDashboard'
import { PersonSelection } from './persons/PersonSelection'
import type { Person } from './persons/types'
import { useTelemetry } from './telemetry/useTelemetry'
import type { TelemetryMessage } from './telemetry/types'
import { TrainingRecommendationView } from './training/TrainingRecommendationView'
import type { TrainingRecommendation } from './training/types'
import { WorkoutSummaryView } from './workout/WorkoutSummaryView'
import type { Workout } from './workout/types'
import { WorkoutView } from './workout/WorkoutView'


function App() {
  const [persons, setPersons] =
    useState<Person[]>([])

  const [activePerson, setActivePerson] =
    useState<Person | null>(null)

  const [checkIn, setCheckIn] =
    useState<CheckIn | null>(null)

  const [
    recommendation,
    setRecommendation,
  ] =
    useState<TrainingRecommendation | null>(
      null,
    )

  const [
    recommendationLoading,
    setRecommendationLoading,
  ] = useState(false)

  const [
    recommendationError,
    setRecommendationError,
  ] =
    useState<string | null>(null)

  const [workout, setWorkout] =
    useState<Workout | null>(null)

  const [
    checkInActive,
    setCheckInActive,
  ] = useState(false)

  const [devices, setDevices] =
    useState<DeviceState[]>([])

  const [error, setError] =
    useState<string | null>(null)


  /*
   * Eingehende Live-Telemetrie aus dem WebSocket.
   *
   * Wichtig:
   * Dieser Callback wird nicht synchron aus einem React-Effect
   * heraus ausgeführt, sondern vom WebSocket-Event ausgelöst.
   *
   * Deshalb ist setDevices() hier der korrekte React-Weg.
   *
   * Vergleich zur Java-Welt:
   * ungefähr ein EventListener, der eingehende Events auf
   * unseren aktuellen UI-State anwendet.
   */
  const handleTelemetryMessage =
    useCallback(
      (message: TelemetryMessage) => {
        /*
         * Ein Gerät hat seinen Status geändert.
         *
         * Beispiel:
         * Pulsgurt wurde verbunden oder getrennt.
         */
        if (
          message.type ===
          'device.status_changed'
        ) {
          const deviceType =
            message.payload.deviceType

          const deviceName =
            message.payload.deviceName

          const status =
            message.payload.status

          /*
           * WebSocket-Daten kommen über eine Prozessgrenze.
           * Deshalb prüfen wir die Payload defensiv,
           * bevor wir sie in unseren UI-State übernehmen.
           */
          if (
            typeof deviceType !== 'string' ||
            typeof deviceName !== 'string' ||
            typeof status !== 'string'
          ) {
            return
          }

          setDevices((currentDevices) => {
            const existingDevice =
              currentDevices.find(
                (device) =>
                  device.device_id ===
                  message.deviceId,
              )

            const updatedDevice: DeviceState = {
              device_id:
                message.deviceId,

              device_type:
                deviceType as DeviceState['device_type'],

              device_name:
                deviceName,

              status:
                status as DeviceState['status'],

              last_seen:
                message.timestamp,

              /*
               * Ein Status-Event enthält keine Herzfrequenz.
               * Falls wir schon einen Messwert kennen,
               * behalten wir ihn deshalb bei.
               */
              heart_rate_bpm:
                existingDevice?.heart_rate_bpm ??
                null,
            }

            /*
             * Upsert:
             *
             * vorhandenes Gerät entfernen und anschließend
             * die aktualisierte Version einfügen.
             */
            return [
              ...currentDevices.filter(
                (device) =>
                  device.device_id !==
                  message.deviceId,
              ),
              updatedDevice,
            ]
          })

          return
        }

        /*
         * Live-Herzfrequenz.
         */
        if (
          message.type ===
          'heart_rate.sample'
        ) {
          const bpm =
            message.payload.bpm

          if (typeof bpm !== 'number') {
            return
          }

          setDevices((currentDevices) =>
            currentDevices.map(
              (device) => {
                if (
                  device.device_id !==
                  message.deviceId
                ) {
                  return device
                }

                return {
                  ...device,
                  last_seen:
                    message.timestamp,
                  heart_rate_bpm: bpm,
                }
              },
            ),
          )
        }
      },
      [],
    )


  /*
   * WebSocket-Verbindung zum Backend aktivieren.
   *
   * useTelemetry kümmert sich ausschließlich um die
   * Verbindung und das Einlesen der Nachrichten.
   * Die fachliche Verarbeitung erfolgt oben im Callback.
   */
  useTelemetry({
    onMessage: handleTelemetryMessage,
  })


  /*
   * Personen einmal beim Start laden.
   */
  useEffect(() => {
    async function loadPersons(): Promise<void> {
      try {
        const result =
          await getPersons()

        setPersons(result)
        setError(null)
      } catch (loadError) {
        const message =
          loadError instanceof Error
            ? loadError.message
            : 'Unknown error'

        setError(message)
      }
    }

    void loadPersons()
  }, [])


  /*
   * Geräte einmal beim Start als Snapshot laden.
   *
   * Danach werden Änderungen nicht mehr gepollt,
   * sondern live über /ws/telemetry geliefert.
   *
   * Der initiale REST-Aufruf ist trotzdem sinnvoll:
   * Wenn der Pulsgurt bereits verbunden war, bevor der
   * Browser geöffnet wurde, kennen wir seinen aktuellen
   * Zustand sofort.
   */
  useEffect(() => {
    async function loadDevices(): Promise<void> {
      try {
        const result =
          await getDevices()

        setDevices(result)
      } catch {
        /*
         * Der Device-Snapshot ist optional.
         *
         * Falls dieser Request fehlschlägt, kann die
         * WebSocket-Telemetrie trotzdem weiterlaufen.
         */
      }
    }

    void loadDevices()
  }, [])


  async function handleStartWorkout(): Promise<void> {
    if (activePerson === null) {
      return
    }

    const startedWorkout =
      await startWorkout(
        activePerson.id,
      )

    setWorkout(startedWorkout)
  }


  async function handleCheckInComplete(
    completedCheckIn: CheckIn,
  ): Promise<void> {
    if (activePerson === null) {
      return
    }

    setCheckIn(completedCheckIn)
    setCheckInActive(false)
    setRecommendationLoading(true)
    setRecommendationError(null)

    try {
      const result =
        await getTrainingRecommendation(
          activePerson.id,
        )

      setRecommendation(result)
    } catch (loadError) {
      const message =
        loadError instanceof Error
          ? loadError.message
          : 'Unknown error'

      setRecommendationError(message)
    } finally {
      setRecommendationLoading(false)
    }
  }


  /*
   * Solange keine Person gewählt wurde, zeigen wir
   * ausschließlich die Personenauswahl.
   */
  if (activePerson === null) {
    return (
      <main className="app">
        {error !== null && (
          <div className="error-message">
            Backend nicht erreichbar: {error}
          </div>
        )}

        <PersonSelection
          persons={persons}
          onSelect={setActivePerson}
        />
      </main>
    )
  }


  /*
   * Person wurde gewählt, aber ein Check-in wurde
   * noch nicht gestartet.
   *
   * In diesem Zustand zeigen wir das persönliche
   * Dashboard inklusive Trainingshistorie.
   */
  if (
    checkIn === null &&
    !checkInActive
  ) {
    return (
      <main className="app">
        <PersonDashboard
          person={activePerson}
          onStartCheckIn={() => {
            setCheckInActive(true)
          }}
          onChangePerson={() => {
            setCheckIn(null)
            setRecommendation(null)
            setWorkout(null)
            setCheckInActive(false)
            setActivePerson(null)
          }}
        />
      </main>
    )
  }


  /*
   * Check-in läuft.
   */
  if (
    checkIn === null &&
    checkInActive
  ) {
    return (
      <main className="app">
        <CheckInWizard
          person={activePerson}
          onComplete={(completedCheckIn) => {
            void handleCheckInComplete(
              completedCheckIn,
            )
          }}
          onCancel={() => {
            setCheckIn(null)
            setRecommendation(null)
            setCheckInActive(false)
          }}
        />
      </main>
    )
  }


  /*
   * Empfehlung wird gerade berechnet/geladen.
   */
  if (recommendationLoading) {
    return (
      <main className="app">
        <div className="loading-state">
          Training wird geplant …
        </div>
      </main>
    )
  }


  /*
   * Laden der Trainingsempfehlung ist fehlgeschlagen.
   */
  if (recommendationError !== null) {
    return (
      <main className="app">
        <div className="error-message">
          {recommendationError}
        </div>

        <button
          type="button"
          className="secondary-action"
          onClick={() => {
            setCheckIn(null)
            setRecommendation(null)
            setRecommendationError(null)
          }}
        >
          Check-in erneut durchführen
        </button>
      </main>
    )
  }


  /*
   * Aktives Training.
   */
  if (
    workout !== null &&
    workout.status === 'running'
  ) {
    return (
      <main className="app">
        <WorkoutView
          person={activePerson}
          workout={workout}
          devices={devices}
          onComplete={(completedWorkout) => {
            setWorkout(completedWorkout)
          }}
        />
      </main>
    )
  }


  /*
   * Training wurde beendet oder abgebrochen.
   */
  if (
    workout !== null &&
    (
      workout.status === 'completed' ||
      workout.status === 'aborted'
    )
  ) {
    return (
      <main className="app">
        <WorkoutSummaryView
          person={activePerson}
          workout={workout}
          onDone={() => {
            setWorkout(null)
            setCheckIn(null)
            setRecommendation(null)
            setCheckInActive(false)
          }}
        />
      </main>
    )
  }


  /*
   * Check-in abgeschlossen und Empfehlung vorhanden.
   */
  if (recommendation !== null) {
    return (
      <main className="app">
        <TrainingRecommendationView
          person={activePerson}
          recommendation={recommendation}
          onBack={() => {
            setCheckIn(null)
            setRecommendation(null)
          }}
          onStart={() => {
            void handleStartWorkout()
          }}
        />
      </main>
    )
  }


  /*
   * Fallback-Anzeige der erkannten Pulssensoren.
   *
   * Dieser Bereich bleibt zunächst erhalten.
   * Später können hier weitere Geräte wie das Bike
   * hinzukommen.
   */
  const heartRateDevices =
    devices.filter(
      (device) =>
        device.device_type ===
        'heart_rate',
    )


  return (
    <main className="app">
      <header className="app-header">
        <div>
          <div className="eyebrow">
            DIGITAL FITNESS COACH
          </div>

          <h1>
            Hallo {activePerson.displayName}
          </h1>
        </div>

        <button
          className="change-person"
          type="button"
          onClick={() => {
            setCheckIn(null)
            setRecommendation(null)
            setWorkout(null)
            setCheckInActive(false)
            setActivePerson(null)
          }}
        >
          Person wechseln
        </button>
      </header>

      <section className="device-grid">
        {heartRateDevices.map(
          (device) => (
            <DeviceCard
              key={device.device_id}
              device={device}
            />
          ),
        )}

        {heartRateDevices.length === 0 && (
          <div className="empty-state">
            Noch kein Pulsgurt erkannt.
          </div>
        )}
      </section>
    </main>
  )
}


export default App