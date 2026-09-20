import { useCallback, useEffect, useState } from "react";

import { getDevices } from "./api/devices";
import { getPersons } from "./api/persons";
import { getTrainingRecommendation } from "./api/training";
import { startWorkout } from "./api/workouts";
import "./App.css";
import { CheckInWizard } from "./check-in/CheckInWizard";
import type { CheckIn } from "./check-in/types";
import { DeviceCard } from "./devices/DeviceCard";
import { mergeDeviceSnapshot } from "./devices/mergeDeviceSnapshot";
import type { DeviceState } from "./devices/types";
import { PersonDashboard } from "./persons/PersonDashboard";
import { PersonSelection } from "./persons/PersonSelection";
import type { Person } from "./persons/types";
import { applyTelemetryMessage } from "./telemetry/applyTelemetryMessage";
import { useTelemetry } from "./telemetry/useTelemetry";
import { TrainingRecommendationView } from "./training/TrainingRecommendationView";
import type { TrainingRecommendation } from "./training/types";
import { WorkoutVideoManagement } from "./workout/WorkoutVideoManagement";
import { WorkoutSummaryView } from "./workout/WorkoutSummaryView";
import type { Workout } from "./workout/types";
import { WorkoutView } from "./workout/WorkoutView";
import { PersonProfileEditor } from "./persons/PersonProfileEditor";

function App() {
  const [persons, setPersons] = useState<Person[]>([]);
  const [activePerson, setActivePerson] = useState<Person | null>(null);
  const [profileEditorOpen, setProfileEditorOpen] = useState(false);
  const [personCreateOpen, setPersonCreateOpen] = useState(false);
  const [videoManagementOpen, setVideoManagementOpen] = useState(false);
  const [checkIn, setCheckIn] = useState<CheckIn | null>(null);
  const [recommendation, setRecommendation] =
    useState<TrainingRecommendation | null>(null);
  const [recommendationLoading, setRecommendationLoading] = useState(false);
  const [recommendationError, setRecommendationError] = useState<string | null>(
    null,
  );
  const [workout, setWorkout] = useState<Workout | null>(null);
  const [checkInActive, setCheckInActive] = useState(false);
  const [devices, setDevices] = useState<DeviceState[]>([]);
  const [workoutStartLoading, setWorkoutStartLoading] = useState(false);
  const [workoutStartError, setWorkoutStartError] = useState<string | null>(
    null,
  );
  const [error, setError] = useState<string | null>(null);

  /*
   * Eingehende Live-Telemetrie wird durch eine pure Funktion
   * auf unseren aktuellen Device-State angewendet.
   *
   * React ist damit nur noch für die State-Verwaltung zuständig.
   * Die fachliche Merge-/Upsert-Logik liegt in
   * applyTelemetryMessage().
   */
  const handleTelemetryMessage = useCallback(
    (message: Parameters<typeof applyTelemetryMessage>[1]) => {
      setDevices((currentDevices) =>
        applyTelemetryMessage(currentDevices, message),
      );
    },
    [],
  );

  /*
   * Lädt den aktuellen Gerätezustand als REST-Snapshot.
   *
   * Der Snapshot ersetzt den lokalen Zustand nicht blind.
   * mergeDeviceSnapshot() sorgt dafür, dass neuere
   * WebSocket-Daten erhalten bleiben.
   *
   * Diese Funktion wird sowohl beim Start als auch nach
   * einem WebSocket-Reconnect verwendet.
   */
  const loadDeviceSnapshot = useCallback(async (): Promise<void> => {
    try {
      const result = await getDevices();

      setDevices((currentDevices) =>
        mergeDeviceSnapshot(currentDevices, result),
      );
    } catch {
      /*
       * Der Device-Snapshot ist optional.
       *
       * Falls dieser Request fehlschlägt, kann die
       * WebSocket-Telemetrie trotzdem weiterlaufen.
       */
    }
  }, []);

  /*
   * WebSocket-Verbindung zum Backend aktivieren.
   *
   * Nach einer tatsächlich wiederhergestellten Verbindung
   * synchronisieren wir zusätzlich den aktuellen REST-Snapshot.
   * Dadurch holen wir Zustandsänderungen nach, die während
   * des WebSocket-Ausfalls möglicherweise verpasst wurden.
   */
  useTelemetry({
    onMessage: handleTelemetryMessage,
    onConnected: loadDeviceSnapshot,
  });

  /*
   * Personen einmal beim Start laden.
   */
  useEffect(() => {
    async function loadPersons(): Promise<void> {
      try {
        const result = await getPersons();

        setPersons(result);
        setError(null);
      } catch (loadError) {
        const message =
          loadError instanceof Error ? loadError.message : "Unknown error";

        setError(message);
      }
    }

    void loadPersons();
  }, []);

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
        const result = await getDevices();

        setDevices((currentDevices) =>
          mergeDeviceSnapshot(currentDevices, result),
        );
      } catch {
        /*
         * Der Device-Snapshot ist optional.
         *
         * Falls dieser Request fehlschlägt, kann die
         * WebSocket-Telemetrie trotzdem weiterlaufen.
         */
      }
    }

    void loadDevices();
  }, []);

  function handlePersonCreated(createdPerson: Person): void {
    setPersons((currentPersons) => [...currentPersons, createdPerson]);
    setPersonCreateOpen(false);
  }

  function handleProfileSaved(updatedPerson: Person): void {
    // Die Personenauswahl erhält den neuen Namen.
    setPersons((currentPersons) =>
      currentPersons.map((person) =>
        person.id === updatedPerson.id ? updatedPerson : person,
      ),
    );

    // Auch das aktuell geöffnete Dashboard erhält den neuen Namen.
    setActivePerson((currentPerson) =>
      currentPerson?.id === updatedPerson.id ? updatedPerson : currentPerson,
    );

    setProfileEditorOpen(false);
  }

  async function handleStartWorkout(videoId: string): Promise<void> {
    if (activePerson === null || workoutStartLoading) {
      return;
    }

    setWorkoutStartLoading(true);
    setWorkoutStartError(null);

    try {
      const startedWorkout = await startWorkout(activePerson.id, videoId);

      setWorkout(startedWorkout);
    } catch (startError) {
      const message =
        startError instanceof Error
          ? startError.message
          : "Training konnte nicht gestartet werden";

      setWorkoutStartError(message);
    } finally {
      setWorkoutStartLoading(false);
    }
  }

  async function handleCheckInComplete(
    completedCheckIn: CheckIn,
  ): Promise<void> {
    if (activePerson === null) {
      return;
    }

    setCheckIn(completedCheckIn);
    setCheckInActive(false);
    setRecommendationLoading(true);
    setRecommendationError(null);

    try {
      const result = await getTrainingRecommendation(activePerson.id);

      setRecommendation(result);
    } catch (loadError) {
      const message =
        loadError instanceof Error ? loadError.message : "Unknown error";

      setRecommendationError(message);
    } finally {
      setRecommendationLoading(false);
    }
  }

  /*
   * Solange keine Person gewählt wurde, zeigen wir
   * ausschließlich die Personenauswahl.
   */
  if (activePerson === null) {
    return (
      <main className="app">
        {videoManagementOpen ? (
          <WorkoutVideoManagement
            onClose={() => setVideoManagementOpen(false)}
          />
        ) : personCreateOpen ? (
          <PersonProfileEditor
            key="create"
            person={null}
            onSaved={handlePersonCreated}
            onCancel={() => setPersonCreateOpen(false)}
          />
        ) : (
          <>
            {error !== null && (
              <div className="error-message">
                Backend nicht erreichbar: {error}
              </div>
            )}

            <PersonSelection
              persons={persons}
              onSelect={setActivePerson}
              onCreate={() => setPersonCreateOpen(true)}
              onManageVideos={() => setVideoManagementOpen(true)}
            />
          </>
        )}
      </main>
    );
  }

  /*
   * Personenprofil bearbeiten.
   *
   * Der Editor ist nur vom Dashboard aus erreichbar.
   * Währenddessen bleibt die aktive Person erhalten.
   */
  if (profileEditorOpen) {
    return (
      <main className="app">
        <PersonProfileEditor
          key={activePerson.id}
          person={activePerson}
          onSaved={handleProfileSaved}
          onCancel={() => {
            setProfileEditorOpen(false);
          }}
        />
      </main>
    );
  }

  /*
   * Person wurde gewählt, aber ein Check-in wurde
   * noch nicht gestartet.
   *
   * In diesem Zustand zeigen wir das persönliche
   * Dashboard inklusive Trainingshistorie.
   */
  if (checkIn === null && !checkInActive) {
    return (
      <main className="app">
        <PersonDashboard
          person={activePerson}
          onStartCheckIn={() => {
            setCheckInActive(true);
          }}
          onChangePerson={() => {
            setCheckIn(null);
            setRecommendation(null);
            setWorkout(null);
            setCheckInActive(false);
            setActivePerson(null);
          }}
          onEditProfile={() => {
            setProfileEditorOpen(true);
          }}
        />
      </main>
    );
  }

  /*
   * Check-in läuft.
   */
  if (checkIn === null && checkInActive) {
    return (
      <main className="app">
        <CheckInWizard
          person={activePerson}
          onComplete={(completedCheckIn) => {
            void handleCheckInComplete(completedCheckIn);
          }}
          onCancel={() => {
            setCheckIn(null);
            setRecommendation(null);
            setCheckInActive(false);
          }}
        />
      </main>
    );
  }

  /*
   * Empfehlung wird gerade berechnet/geladen.
   */
  if (recommendationLoading) {
    return (
      <main className="app">
        <div className="loading-state">Training wird geplant …</div>
      </main>
    );
  }

  /*
   * Laden der Trainingsempfehlung ist fehlgeschlagen.
   */
  if (recommendationError !== null) {
    return (
      <main className="app">
        <div className="error-message">{recommendationError}</div>

        <button
          type="button"
          className="secondary-action"
          onClick={() => {
            setCheckIn(null);
            setRecommendation(null);
            setRecommendationError(null);
          }}
        >
          Check-in erneut durchführen
        </button>
      </main>
    );
  }

  /*
   * Aktives Training.
   */
  if (workout !== null && workout.status === "running") {
    return (
      <main className="app">
        <WorkoutView
          person={activePerson}
          workout={workout}
          devices={devices}
          onComplete={(completedWorkout) => {
            setWorkout(completedWorkout);
          }}
        />
      </main>
    );
  }

  /*
   * Training wurde beendet oder abgebrochen.
   */
  if (
    workout !== null &&
    (workout.status === "completed" || workout.status === "aborted")
  ) {
    return (
      <main className="app">
        <WorkoutSummaryView
          person={activePerson}
          workout={workout}
          onDone={() => {
            setWorkout(null);
            setCheckIn(null);
            setRecommendation(null);
            setCheckInActive(false);
          }}
        />
      </main>
    );
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
          startLoading={workoutStartLoading}
          startError={workoutStartError}
          onClearStartError={() => {
            setWorkoutStartError(null);
          }}
          onBack={() => {
            setCheckIn(null);
            setRecommendation(null);
          }}
          onStart={(videoId) => {
            void handleStartWorkout(videoId);
          }}
        />
      </main>
    );
  }

  /*
   * Fallback-Anzeige der erkannten Pulssensoren.
   *
   * Dieser Bereich bleibt zunächst erhalten.
   * Später können hier weitere Geräte wie das Bike
   * hinzukommen.
   */
  const heartRateDevices = devices.filter(
    (device) => device.deviceType === "heart_rate",
  );

  return (
    <main className="app">
      <header className="app-header">
        <div>
          <div className="eyebrow">DIGITAL FITNESS COACH</div>

          <h1>Hallo {activePerson.displayName}</h1>
        </div>

        <button
          className="change-person"
          type="button"
          onClick={() => {
            setCheckIn(null);
            setRecommendation(null);
            setWorkout(null);
            setCheckInActive(false);
            setActivePerson(null);
          }}
        >
          Person wechseln
        </button>
      </header>

      <section className="device-grid">
        {heartRateDevices.map((device) => (
          <DeviceCard key={device.deviceId} device={device} />
        ))}

        {heartRateDevices.length === 0 && (
          <div className="empty-state">Noch kein Pulsgurt erkannt.</div>
        )}
      </section>
    </main>
  );
}

export default App;
