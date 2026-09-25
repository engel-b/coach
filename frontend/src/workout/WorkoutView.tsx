import { useCallback, useEffect, useMemo, useRef, useState } from "react";

import {
  checkpointWorkout,
  finishWorkout,
  getWorkoutVideo,
  updateWorkoutRuntimeState,
} from "../api/workouts";
import { coachingMessage } from "../coaching/coachingMessage";
import { CoachAvatar } from "../coaching/CoachAvatar";
import {
  useCoachSpeech,
  type CoachSpeechStatus,
} from "../coaching/useCoachSpeech";
import type { LiveCoachingEvent } from "../coaching/types";
import { useLiveCoaching } from "../coaching/useLiveCoaching";
import type { DeviceState } from "../devices/types";
import type { Person } from "../persons/types";
import type { Workout, WorkoutPhase, WorkoutRuntimeState } from "./types";
import {
  calculateVideoPlaybackRate,
  isBikeMoving,
  workoutVideoUrl,
} from "./videoPlayback";
import { playWorkoutFinishSound } from "./workoutSound";
import { WorkoutVideo } from "./WorkoutVideo";
import {
  applyWorkoutEngineEvent,
  createWorkoutEngine,
  getFinishWindowRemainingSeconds,
  shouldCountWorkoutTime,
  shouldPlayWorkoutVideo,
} from "./workoutEngine";

import {
  applyNativeDistanceSample,
  createWorkoutDistanceState,
} from "./workoutDistance";

type VideoLoadState =
  | { status: "loading"; videoId: string }
  | { status: "ready"; videoId: string; src: string }
  | { status: "error"; videoId: string; message: string };

interface WorkoutViewProps {
  person: Person;
  workout: Workout;

  /*
   * Die Gerätedaten gehören App.tsx.
   *
   * WorkoutView konsumiert nur den aktuellen Zustand
   * und muss deshalb keine eigene Datenquelle mehr pollen.
   */
  devices: DeviceState[];

  onComplete: (workout: Workout) => void;
}

/**
 * Formatiert Sekunden als MM:SS.
 *
 * Beispiel:
 *   75 -> "01:15"
 */
function formatTime(seconds: number): string {
  const safeSeconds = Math.max(0, seconds);

  const minutes = Math.floor(safeSeconds / 60);
  const remainingSeconds = safeSeconds % 60;

  return `${String(minutes).padStart(2, "0")}:${String(
    remainingSeconds,
  ).padStart(2, "0")}`;
}

/**
 * Ermittelt anhand der bereits trainierten Sekunden,
 * welche Trainingsphase aktuell aktiv ist.
 */
function getCurrentPhase(
  phases: WorkoutPhase[],
  elapsedSeconds: number,
): {
  phase: WorkoutPhase | null;
  phaseElapsedSeconds: number;
} {
  let consumedSeconds = 0;

  for (const phase of phases) {
    const phaseSeconds = phase.durationMinutes * 60;

    if (elapsedSeconds < consumedSeconds + phaseSeconds) {
      return {
        phase,
        phaseElapsedSeconds: elapsedSeconds - consumedSeconds,
      };
    }

    consumedSeconds += phaseSeconds;
  }

  return {
    phase: null,
    phaseElapsedSeconds: 0,
  };
}

function phaseLabel(phaseType: WorkoutPhase["phaseType"]): string {
  switch (phaseType) {
    case "warm_up":
      return "Aufwärmen";

    case "main":
      return "Hauptteil";

    case "cool_down":
      return "Cool-down";
  }
}

function heartRateMessage(
  state: "unknown" | "below" | "target" | "above",
): string {
  switch (state) {
    case "below":
      return "Intensität etwas erhöhen";

    case "target":
      return "Du bist im Zielbereich";

    case "above":
      return "Etwas Tempo herausnehmen";

    case "unknown":
      return "Warte auf Herzfrequenzdaten";
  }
}

export function WorkoutView({
  workout,
  devices,
  onComplete,
}: WorkoutViewProps) {
  const [finishConfirmation, setFinishConfirmation] = useState(false);

  const [finishing, setFinishing] = useState(false);

  const [latestCoachingEvent, setLatestCoachingEvent] =
    useState<LiveCoachingEvent | null>(null);
  const [speechStatus, setSpeechStatus] = useState<CoachSpeechStatus>("idle");
  const greetedWorkoutIdRef = useRef<string | null>(null);

  const [videoLoadState, setVideoLoadState] = useState<VideoLoadState>({
    status: "loading",
    videoId: workout.videoId,
  });

  const [videoLoadAttempt, setVideoLoadAttempt] = useState(0);

  const speakCoachingEvent = useCoachSpeech(setSpeechStatus);

  const handleCoachingMessage = useCallback(
    (message: LiveCoachingEvent): void => {
      if (message.workoutId === workout.id) {
        setLatestCoachingEvent(message);
        speakCoachingEvent(message);
      }
    },
    [speakCoachingEvent, workout.id],
  );

  const coachingConnected = useLiveCoaching({
    onMessage: handleCoachingMessage,
  });

  // Das erste Phasen-Event entsteht vor dem WebSocket-Verbindungsaufbau.
  // Sobald der Coach verbunden ist, begrüßen wir deshalb einmal pro Workout.
  useEffect(() => {
    if (!coachingConnected || greetedWorkoutIdRef.current === workout.id)
      return;
    const firstPhase = workout.phases[0];
    if (!firstPhase) return;
    greetedWorkoutIdRef.current = workout.id;
    speakCoachingEvent({
      type: "coaching.phase_started",
      timestamp: new Date().toISOString(),
      workoutId: workout.id,
      phaseIndex: 0,
      phaseType: firstPhase.phaseType,
      durationMinutes: firstPhase.durationMinutes,
      targetMinBpm: firstPhase.targetHeartRateMin,
      targetMaxBpm: firstPhase.targetHeartRateMax,
      isFinalPhase: false,
    });
  }, [coachingConnected, speakCoachingEvent, workout.id, workout.phases]);

  /*
   * Eine Coaching-Nachricht soll Aufmerksamkeit erzeugen, aber nicht
   * dauerhaft über dem Trainingsvideo stehen bleiben. Der fachliche
   * Event bleibt im Backend entprellt; diese acht Sekunden betreffen
   * ausschließlich die visuelle Darstellung.
   */
  useEffect(() => {
    if (latestCoachingEvent === null) {
      return;
    }

    const timer = window.setTimeout(() => {
      setLatestCoachingEvent(null);
    }, 8_000);

    return () => {
      window.clearTimeout(timer);
    };
  }, [latestCoachingEvent]);

  /*
   * Die aktuelle Videoposition ist technischer Laufzeitzustand.
   *
   * Sie beeinflusst den Render nicht. Deshalb verwenden wir ein Ref
   * statt useState. Der spätere 5-Sekunden-Checkpoint kann jederzeit
   * den zuletzt bekannten Wert daraus lesen.
   *
   * Java-Vergleich:
   * ungefähr ein veränderliches privates Feld, das nicht Teil des
   * UI-State-Modells ist.
   */
  const videoPositionSecondsRef = useRef(workout.videoPositionSeconds);

  /*
   * Es darf immer nur ein Checkpoint-Request gleichzeitig laufen.
   *
   * Ein Ref ist hier passend, weil dieser technische Zustand
   * keinen Render auslösen soll.
   */
  const checkpointInFlightRef = useRef(false);

  const lastReportedRuntimeStateRef = useRef<WorkoutRuntimeState>("running");

  const totalDurationSeconds = useMemo(
    () =>
      workout.phases.reduce(
        (total, phase) => total + phase.durationMinutes * 60,
        0,
      ),
    [workout.phases],
  );

  /*
   * Die WorkoutEngine ist ab jetzt die einzige Quelle
   * für den fachlichen Laufzeitzustand des Workouts.
   *
   * Vergleichbar mit einem Domain-Objekt in Java:
   *
   *   WorkoutEngine engine =
   *       new WorkoutEngine(plannedDurationSeconds);
   */
  const [engineState, setEngineState] = useState(() =>
    createWorkoutEngine(totalDurationSeconds),
  );

  /*
   * elapsedSeconds ist kein eigener React-State mehr.
   * Die WorkoutEngine ist die einzige Quelle dafür.
   */
  const elapsedSeconds = engineState.elapsedSeconds;

  const current = getCurrentPhase(workout.phases, elapsedSeconds);

  const finishWindowRemainingSeconds =
    getFinishWindowRemainingSeconds(engineState);

  const workoutProgress =
    totalDurationSeconds > 0
      ? Math.min(100, Math.round((elapsedSeconds / totalDurationSeconds) * 100))
      : 0;

  const phaseDurationSeconds =
    current.phase !== null ? current.phase.durationMinutes * 60 : 0;

  const phaseRemainingSeconds =
    current.phase !== null
      ? Math.max(0, phaseDurationSeconds - current.phaseElapsedSeconds)
      : 0;

  const phaseProgress =
    phaseDurationSeconds > 0
      ? Math.min(
          100,
          Math.round(
            (current.phaseElapsedSeconds / phaseDurationSeconds) * 100,
          ),
        )
      : 100;

  /*
   * Wir suchen den aktuell verbundenen Pulsgurt.
   *
   * Für V1 verwenden wir das erste verbundene HR-Gerät.
   */
  const heartRateDevice = useMemo(
    () =>
      devices.find(
        (device) =>
          device.deviceType === "heart_rate" && device.status === "connected",
      ),
    [devices],
  );

  const heartRate = heartRateDevice?.heartRateBpm ?? null;

  const targetMin = current.phase?.targetHeartRateMin ?? null;

  const targetMax = current.phase?.targetHeartRateMax ?? null;

  let heartRateState: "unknown" | "below" | "target" | "above" = "unknown";

  if (heartRate !== null && targetMin !== null && targetMax !== null) {
    if (heartRate < targetMin) {
      heartRateState = "below";
    } else if (heartRate > targetMax) {
      heartRateState = "above";
    } else {
      heartRateState = "target";
    }
  }

  const bikeDevice = useMemo(
    () =>
      devices.find(
        (device) =>
          device.deviceType === "bike" && device.status === "connected",
      ),
    [devices],
  );

  const speedKmh = bikeDevice?.speedKmh ?? null;

  const cadenceRpm = bikeDevice?.cadenceRpm ?? null;

  const nativeDistanceM = bikeDevice?.distanceM ?? null;

  const powerW = bikeDevice?.powerW ?? null;

  useEffect(() => {
    let cancelled = false;

    const timer = window.setTimeout(() => {
      setVideoLoadState({
        status: "loading",
        videoId: workout.videoId,
      });
    }, 0);

    void getWorkoutVideo(workout.videoId)
      .then((video) => {
        if (!cancelled) {
          setVideoLoadState({
            status: "ready",
            videoId: workout.videoId,
            src: workoutVideoUrl(video.filePath),
          });
        }
      })
      .catch((error: unknown) => {
        if (!cancelled) {
          setVideoLoadState({
            status: "error",
            videoId: workout.videoId,
            message:
              error instanceof Error
                ? error.message
                : "Unbekannter Fehler beim Laden des Trainingsvideos",
          });
        }
      });

    return () => {
      cancelled = true;
      window.clearTimeout(timer);
    };
  }, [workout.videoId, videoLoadAttempt]);

  /*
   * Die FTMS Total Distance ist ein nativer absoluter
   * Bike-Zähler.
   *
   * Unser Workout beginnt aber immer bei 0 m.
   * Deshalb merken wir uns den beim Mount bereits bekannten
   * Wert als Baseline.
   */
  const [workoutDistance, setWorkoutDistance] = useState(() =>
    createWorkoutDistanceState(nativeDistanceM),
  );

  /*
   * Die Engine ist die fachliche Quelle dafür, ob gerade
   * Trainingszeit zählt.
   *
   * Bei manueller bzw. automatischer Pause zählt deshalb
   * auch keine Workout-Distanz.
   *
   * Das Abbruch-Bestätigungsfenster pausiert ebenfalls
   * Timer und Video und wird deshalb hier genauso behandelt.
   */
  const countWorkoutDistance =
    shouldCountWorkoutTime(engineState) && !finishConfirmation;

  /*
   * Neue native FTMS-Distanzwerte werden in relative
   * Workout-Distanz umgerechnet.
   *
   * setTimeout(0) verwenden wir aus demselben Grund wie beim
   * Bike-Movement-Event: kein direkter State-Write innerhalb
   * des Effects gemäß unserer Hooks-Lint-Regel.
   */
  useEffect(() => {
    const timer = window.setTimeout(() => {
      setWorkoutDistance((currentDistance) =>
        applyNativeDistanceSample(
          currentDistance,
          nativeDistanceM,
          countWorkoutDistance,
        ),
      );
    }, 0);

    return () => {
      window.clearTimeout(timer);
    };
  }, [countWorkoutDistance, nativeDistanceM]);

  const workoutDistanceKm = workoutDistance.accumulatedDistanceM / 1000;

  /*
   * Die aktuellen Laufzeitwerte werden vom späteren
   * Checkpoint-Intervall gelesen.
   *
   * Refs sind dafür passend, weil Änderungen daran keinen
   * zusätzlichen Render auslösen.
   */
  const elapsedSecondsRef = useRef(engineState.elapsedSeconds);

  const workoutDistanceMRef = useRef(workoutDistance.accumulatedDistanceM);

  /*
   * Unser React-Lint-Setup erlaubt keine Änderung von
   * ref.current direkt während des Renderns.
   *
   * Deshalb synchronisieren wir die beiden Werte nach dem
   * jeweiligen Render in einem Effect.
   */
  useEffect(() => {
    elapsedSecondsRef.current = engineState.elapsedSeconds;

    workoutDistanceMRef.current = workoutDistance.accumulatedDistanceM;
  }, [engineState.elapsedSeconds, workoutDistance.accumulatedDistanceM]);

  /*
   * Alle fünf Sekunden sichern wir den zuletzt bekannten
   * Workout-Zustand.
   *
   * Es darf immer nur ein Checkpoint gleichzeitig laufen.
   * Schlägt ein Checkpoint fehl, läuft das Workout weiter
   * und das nächste Intervall versucht es erneut.
   */
  useEffect(() => {
    const timer = window.setInterval(() => {
      if (checkpointInFlightRef.current || finishing) {
        return;
      }

      checkpointInFlightRef.current = true;

      void checkpointWorkout(
        workout.id,
        elapsedSecondsRef.current,
        Math.round(workoutDistanceMRef.current),
        videoPositionSecondsRef.current,
        engineState.state === "paused" ||
          engineState.state === "finish_window" ||
          engineState.state === "overtime"
          ? engineState.state
          : "running",
      )
        .catch((error: unknown) => {
          console.error("Could not checkpoint workout", error);
        })
        .finally(() => {
          checkpointInFlightRef.current = false;
        });
    }, 5000);

    return () => {
      window.clearInterval(timer);
    };
  }, [engineState.state, finishing, workout.id]);

  /*
   * Runtime-State-Wechsel werden sofort separat gemeldet. So kann der Coach
   * auf Pause/Resume ohne das naechste 5-Sekunden-Checkpoint-Intervall warten.
   * Fehlende HR-Hardware spielt hier keine Rolle: Pause/Resume sind reine
   * Workout-Ereignisse.
   */
  useEffect(() => {
    if (engineState.state === "completed" || engineState.state === "aborted") {
      return;
    }

    const runtimeState: WorkoutRuntimeState = engineState.state;

    if (lastReportedRuntimeStateRef.current === runtimeState) {
      return;
    }

    lastReportedRuntimeStateRef.current = runtimeState;

    void updateWorkoutRuntimeState(workout.id, runtimeState).catch(
      (error: unknown) => {
        console.error("Could not update workout runtime state", error);
      },
    );
  }, [engineState.state, workout.id]);

  /*
   * Die Telemetrie entscheidet nur, ob das Bike gerade
   * bewegt wird.
   *
   * Ob daraus tatsächlich eine Pause entsteht, entscheidet
   * ausschließlich die WorkoutEngine. Dort sitzt auch die
   * 3-Sekunden-Entprellung.
   */
  const bikeMoving = isBikeMoving(cadenceRpm, speedKmh);

  /*
   * Neue Bike-Telemetrie wird als Event an die Engine
   * weitergereicht.
   *
   * setTimeout verhindert einen direkten State-Write
   * innerhalb des Effects und verträgt sich damit mit
   * unserer React-Hooks-Lint-Regel.
   */
  useEffect(() => {
    const timer = window.setTimeout(() => {
      setEngineState(
        (currentState) =>
          applyWorkoutEngineEvent(currentState, {
            type: "bike_movement_changed",
            moving: bikeMoving,
          }).state,
      );
    }, 0);

    return () => {
      window.clearTimeout(timer);
    };
  }, [bikeMoving]);

  /*
   * Während der Fahrt folgt die Geschwindigkeit des
   * Trainingsvideos der gemessenen Bike-Geschwindigkeit.
   */
  const videoPlaybackRate = calculateVideoPlaybackRate(speedKmh);

  /*
   * Der Browser liefert nur noch den 1-Sekunden-Takt.
   *
   * Was dieser Tick fachlich bedeutet, entscheidet die
   * WorkoutEngine.
   */
  useEffect(() => {
    if (
      finishConfirmation ||
      engineState.state === "paused" ||
      engineState.state === "completed" ||
      engineState.state === "aborted"
    ) {
      return;
    }

    const timer = window.setTimeout(() => {
      setEngineState((currentState) => {
        const transition = applyWorkoutEngineEvent(currentState, {
          type: "tick",
        });

        /*
         * Ein Engine-Effekt wird genau beim zugehörigen
         * Zustandsübergang ausgeführt.
         *
         * Der Sound gehört technisch in den Browser-Adapter,
         * nicht in die reine Engine.
         */
        if (transition.effects.playFinishSound) {
          void playWorkoutFinishSound();
        }

        return transition.state;
      });
    }, 1000);

    return () => {
      window.clearTimeout(timer);
    };
  }, [
    engineState.state,
    engineState.elapsedSeconds,
    engineState.finishWindowElapsedSeconds,
    engineState.bikeStoppedForSeconds,
    finishConfirmation,
  ]);

  const finishCurrentWorkout = useCallback(async (): Promise<void> => {
    if (finishing) {
      return;
    }

    try {
      setFinishing(true);

      const finished = await finishWorkout(
        workout.id,
        elapsedSeconds,
        Math.round(workoutDistance.accumulatedDistanceM),
      );

      onComplete(finished);
    } catch (error) {
      console.error("Could not finish workout", error);
    } finally {
      setFinishing(false);
    }
  }, [
    elapsedSeconds,
    finishing,
    onComplete,
    workout.id,
    workoutDistance.accumulatedDistanceM,
  ]);

  /*
   * "completed" ist ein fachlicher Endzustand der Engine.
   *
   * Das Frontend meldet dem Backend nur noch:
   * "Dieses Workout soll jetzt beendet werden."
   *
   * Ob es fachlich "completed" oder "aborted" ist,
   * entscheidet ausschließlich das Backend anhand der
   * tatsächlich absolvierten Trainingszeit.
   */
  useEffect(() => {
    if (engineState.state !== "completed" || finishing) {
      return;
    }

    const timer = window.setTimeout(() => {
      void finishCurrentWorkout();
    }, 0);

    return () => {
      window.clearTimeout(timer);
    };
  }, [engineState.state, finishCurrentWorkout, finishing]);

  useEffect(() => {
    function handleKeyDown(event: KeyboardEvent): void {
      if (finishing) {
        return;
      }

      if (finishConfirmation) {
        if (event.key === "Enter") {
          void finishCurrentWorkout();
          return;
        }

        if (event.key === "Escape") {
          setFinishConfirmation(false);
        }

        return;
      }

      if (event.key === "Enter") {
        setEngineState(
          (currentState) =>
            applyWorkoutEngineEvent(currentState, {
              type:
                currentState.state === "paused" &&
                currentState.pauseReason === "manual"
                  ? "manual_resume"
                  : "manual_pause",
            }).state,
        );
        return;
      }

      if (event.key === "Escape") {
        setFinishConfirmation(true);
      }
    }

    window.addEventListener("keydown", handleKeyDown);

    return () => {
      window.removeEventListener("keydown", handleKeyDown);
    };
  });

  return (
    <section className="workout-view">
      <header className="workout-stage-header">
        <button
          type="button"
          className="workout-exit-button"
          disabled={finishing}
          onClick={() => {
            setFinishConfirmation(true);
          }}
        >
          ← Workout beenden
        </button>

        <div className="workout-stage-title">
          <strong>Cycling Basic Endurance</strong>

          <span>
            {current.phase !== null
              ? phaseLabel(current.phase.phaseType)
              : engineState.state === "finish_window"
                ? "Trainingsziel erreicht"
                : engineState.state === "overtime"
                  ? "Overtime"
                  : "Abgeschlossen"}
          </span>
        </div>

        <div className="workout-stage-status">
          <span
            className={
              heartRateDevice !== undefined
                ? "device-dot connected"
                : "device-dot"
            }
          />

          {heartRateDevice !== undefined
            ? heartRateDevice.deviceName
            : "Pulsgurt nicht verbunden"}
        </div>
      </header>

      {(speechStatus === "browser_fallback" ||
        speechStatus === "unavailable") && (
        <div className="workout-speech-banner" role="alert">
          <strong>Coach-Ansage gestört</strong>
          <span>
            {speechStatus === "browser_fallback"
              ? "Die lokale Stimme ist ausgefallen. Die Browserstimme wird als Ersatz versucht; Hinweise bleiben sichtbar."
              : "Sprachausgabe derzeit nicht verfügbar. Coaching-Hinweise bleiben sichtbar."}
          </span>
        </div>
      )}

      <div className="workout-stage">
        {videoLoadState.videoId === workout.videoId &&
        videoLoadState.status === "ready" ? (
          <WorkoutVideo
            key={workout.videoId}
            src={videoLoadState.src}
            paused={!shouldPlayWorkoutVideo(engineState) || finishConfirmation}
            playbackRate={videoPlaybackRate}
            initialPositionSeconds={workout.videoPositionSeconds}
            onPositionChange={(positionSeconds) => {
              videoPositionSecondsRef.current = positionSeconds;
            }}
          />
        ) : videoLoadState.videoId === workout.videoId &&
          videoLoadState.status === "error" ? (
          <div className="workout-video-loading" role="alert">
            <p>Das Trainingsvideo konnte nicht geladen werden.</p>
            <p>{videoLoadState.message}</p>
            <button
              type="button"
              onClick={() => {
                setVideoLoadAttempt((attempt) => attempt + 1);
              }}
            >
              Erneut versuchen
            </button>
          </div>
        ) : (
          <div className="workout-video-loading" role="status">
            Trainingsvideo wird geladen …
          </div>
        )}
        <div className="workout-stage-shade" />

        <div className="workout-phase-overlay workout-overlay-card">
          <div className="workout-overlay-label">NÄCHSTES / AKTUELL</div>

          <div className="workout-overlay-title">
            {current.phase !== null
              ? phaseLabel(current.phase.phaseType)
              : engineState.state === "finish_window"
                ? "Trainingsziel erreicht"
                : engineState.state === "overtime"
                  ? "Overtime"
                  : "Training abgeschlossen"}
          </div>

          {current.phase !== null && (
            <>
              <div className="workout-overlay-meta">
                <strong>{formatTime(phaseRemainingSeconds)}</strong>

                <span>
                  {targetMin ?? "–"}–{targetMax ?? "–"} bpm
                </span>
              </div>

              <div className="workout-progress-track">
                <div
                  className="workout-progress-value"
                  style={{
                    width: `${phaseProgress}%`,
                  }}
                />
              </div>
            </>
          )}
        </div>

        <div className="workout-total-overlay workout-overlay-card">
          <div className="workout-overlay-label">FORTSCHRITT</div>

          <div className="workout-overlay-meta">
            <strong>{formatTime(elapsedSeconds)}</strong>

            <span>/ {formatTime(totalDurationSeconds)}</span>
          </div>

          <div className="workout-progress-track">
            <div
              className="workout-progress-value"
              style={{
                width: `${workoutProgress}%`,
              }}
            />
          </div>
        </div>

        <div
          className={`workout-target-overlay workout-overlay-card ${heartRateState}`}
        >
          <div className="workout-overlay-label">♥ ZIELPULS</div>

          <div className="workout-target-range">
            {targetMin ?? "–"}–{targetMax ?? "–"}
            <span>bpm</span>
          </div>

          <div className="workout-target-message">
            {heartRateMessage(heartRateState)}
          </div>
        </div>

        <div className="workout-total-percent workout-overlay-card">
          <div
            className="workout-progress-ring"
            style={{
              background: `conic-gradient(
                #73d55b ${workoutProgress}%,
                rgba(255, 255, 255, 0.14) 0
              )`,
            }}
          >
            <div className="workout-progress-ring-inner" />
          </div>

          <div>
            <div className="workout-overlay-label">GESAMT</div>

            <strong>{workoutProgress}%</strong>
          </div>
        </div>

        <div className="coach-avatar">
          {latestCoachingEvent !== null && (
            <div className="coach-message" role="status" aria-live="polite">
              <div className="coach-message-label">COACH</div>

              <div className="coach-message-text">
                {coachingMessage(latestCoachingEvent)}
              </div>
            </div>
          )}

          <CoachAvatar className="coach-avatar-face" label="" />

          <div
            className={`coach-avatar-status${
              coachingConnected ? " connected" : ""
            }`}
          >
            {coachingConnected
              ? heartRateDevice !== undefined
                ? "Coach online"
                : "Coach online · Kein Pulssensor"
              : "Coach verbindet …"}
          </div>
          <div
            className="coach-avatar-status coach-speech-status"
            role="status"
          >
            Sprache:{" "}
            {
              (
                {
                  idle: "bereit",
                  synthesizing: "Piper erzeugt Audio …",
                  playing: "Ansage läuft",
                  browser_fallback:
                    "Lokale Ansage fehlgeschlagen · Browserstimme versucht",
                  unavailable: "Ansage fehlgeschlagen · Konsole und API prüfen",
                } satisfies Record<CoachSpeechStatus, string>
              )[speechStatus]
            }
          </div>
          <button
            type="button"
            className="secondary-action coach-test-speech-button"
            onClick={() => {
              const phase = workout.phases[0];
              if (!phase) return;
              speakCoachingEvent({
                type: "coaching.phase_started",
                timestamp: new Date().toISOString(),
                workoutId: workout.id,
                phaseIndex: 0,
                phaseType: phase.phaseType,
                durationMinutes: phase.durationMinutes,
                targetMinBpm: phase.targetHeartRateMin,
                targetMaxBpm: phase.targetHeartRateMax,
                isFinalPhase: false,
              });
            }}
          >
            Testansage
          </button>
        </div>

        {engineState.state === "paused" && (
          <div className="workout-pause-overlay">
            <strong>PAUSE</strong>

            <span>
              {engineState.pauseReason === "manual"
                ? "Training manuell pausiert"
                : "Weiter treten zum Fortsetzen"}
            </span>
          </div>
        )}

        {engineState.state === "finish_window" && (
          <div className="workout-pause-overlay workout-complete-overlay">
            <strong>Trainingsziel erreicht</strong>

            <span>Weiterfahren für Overtime</span>

            <span>Bei Stopp wird das Training abgeschlossen</span>

            <strong>{finishWindowRemainingSeconds}s</strong>
          </div>
        )}

        <div className="workout-telemetry-bar">
          <div className="workout-telemetry-metrics">
            <div className="telemetry-metric heart-rate-metric">
              <div className="telemetry-label">♥ PULS</div>

              <div className="telemetry-value">
                {heartRate ?? "–"}
                <span>bpm</span>
              </div>

              <div className={`telemetry-caption ${heartRateState}`}>
                {targetMin !== null && targetMax !== null
                  ? `${targetMin}–${targetMax} bpm`
                  : "Kein Zielbereich"}
              </div>
            </div>

            <div className="telemetry-metric">
              <div className="telemetry-label">◷ ZEIT</div>

              <div className="telemetry-value">
                {formatTime(elapsedSeconds)}
              </div>

              <div className="telemetry-caption">
                / {formatTime(totalDurationSeconds)}
              </div>
            </div>

            <div className="telemetry-metric">
              <div className="telemetry-label">↔ DISTANZ</div>

              <div className="telemetry-value">
                <strong>{workoutDistanceKm.toFixed(2)}</strong>
                <span>km</span>
              </div>

              <div className="telemetry-caption">Workout</div>
            </div>

            <div className="telemetry-metric">
              <div className="telemetry-label">◉ GESCHWINDIGKEIT</div>

              <div className="telemetry-value">
                <strong>{speedKmh !== null ? speedKmh.toFixed(1) : "–"}</strong>
                <span>km/h</span>
              </div>

              <div className="telemetry-caption">
                {speedKmh !== null ? "" : "Bike noch nicht verbunden"}
              </div>
            </div>

            <div className="telemetry-metric">
              <div className="telemetry-label">⚡ LEISTUNG</div>

              <div className="telemetry-value">
                <strong>{powerW !== null ? Math.round(powerW) : "–"}</strong>
                <span>W</span>
              </div>

              <div className="telemetry-caption">
                {powerW !== null ? "" : "Bike noch nicht verbunden"}
              </div>
            </div>

            <div className="telemetry-metric">
              <div className="telemetry-label">◌ TRITTFREQUENZ</div>

              <div className="telemetry-value">
                <strong>
                  {cadenceRpm !== null ? Math.round(cadenceRpm) : "–"}
                </strong>
                <span>rpm</span>
              </div>

              <div className="telemetry-caption">
                {cadenceRpm !== null ? "" : "Bike noch nicht verbunden"}
              </div>
            </div>
          </div>

          <div className="workout-telemetry-actions">
            {engineState.state !== "completed" && (
              <>
                <button
                  type="button"
                  className="workout-pause-button"
                  disabled={finishing}
                  onClick={() => {
                    setEngineState(
                      (currentState) =>
                        applyWorkoutEngineEvent(currentState, {
                          type:
                            currentState.state === "paused" &&
                            currentState.pauseReason === "manual"
                              ? "manual_resume"
                              : "manual_pause",
                        }).state,
                    );
                  }}
                >
                  {engineState.state === "paused" &&
                  engineState.pauseReason === "manual"
                    ? "▶ Fortsetzen"
                    : "Ⅱ Pause"}
                </button>

                <button
                  type="button"
                  className="workout-stop-button"
                  disabled={finishing}
                  onClick={() => {
                    setFinishConfirmation(true);
                  }}
                >
                  □ Workout beenden
                </button>
              </>
            )}
          </div>
        </div>
      </div>

      {finishConfirmation && (
        <div className="confirmation-backdrop">
          <div className="confirmation-dialog">
            <div className="eyebrow">TRAINING BEENDEN</div>

            <h2>Möchtest du das Training wirklich beenden?</h2>

            <p>
              Die bisherige Trainingszeit beträgt {formatTime(elapsedSeconds)}.
            </p>

            <div className="confirmation-actions">
              <button
                type="button"
                className="secondary-action"
                disabled={finishing}
                onClick={() => {
                  setFinishConfirmation(false);
                }}
              >
                Weiter trainieren
              </button>

              <button
                type="button"
                className="primary-action"
                disabled={finishing}
                onClick={() => {
                  void finishCurrentWorkout();
                }}
              >
                {finishing ? "Wird beendet …" : "Training beenden"}
              </button>
            </div>

            <div className="keyboard-hint">
              Esc · Weiter trainieren
              {" · "}
              Enter · Training beenden
            </div>
          </div>
        </div>
      )}
    </section>
  );
}
