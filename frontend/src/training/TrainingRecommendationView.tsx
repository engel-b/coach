import { useEffect, useState } from "react";

import { getWorkoutVideos } from "../api/workouts";
import type { Person } from "../persons/types";
import type { WorkoutVideo } from "../workout/types";
import type {
  TrainingRecommendation,
  WorkoutPhase,
  WorkoutPhaseType,
  WorkoutType,
} from "./types";

interface TrainingRecommendationViewProps {
  person: Person;
  recommendation: TrainingRecommendation;
  onStart: (videoId: string) => void;
  onBack: () => void;
  startLoading: boolean
  startError: string | null
  onClearStartError: () => void
}

function workoutTitle(type: WorkoutType): string {
  switch (type) {
    case "recovery":
      return "Regeneration";

    case "base_endurance":
      return "Grundlagenausdauer";

    case "moderate":
      return "Moderates Training";
  }
}

function phaseTitle(type: WorkoutPhaseType): string {
  switch (type) {
    case "warm_up":
      return "Aufwärmen";

    case "main":
      return "Hauptteil";

    case "cool_down":
      return "Cool-down";
  }
}

function PhaseRow({ phase }: { phase: WorkoutPhase }) {
  return (
    <div className="training-phase">
      <div className="phase-name">{phaseTitle(phase.phaseType)}</div>

      <div className="phase-duration">{phase.durationMinutes} min</div>

      <div className="phase-heart-rate">
        ♥ {phase.targetHeartRateMin}
        {"–"}
        {phase.targetHeartRateMax} bpm
      </div>
    </div>
  );
}

export function TrainingRecommendationView({
  person,
  recommendation,
  onStart,
  onBack,
  startLoading,
  startError,
  onClearStartError,
}: TrainingRecommendationViewProps) {
  const [videos, setVideos] = useState<WorkoutVideo[]>([]);
  const [selectedVideoId, setSelectedVideoId] = useState<string | null>(null);
  const [videosLoading, setVideosLoading] = useState(true);
  const [videosError, setVideosError] = useState<string | null>(null);
  const [loadAttempt, setLoadAttempt] = useState(0);

  useEffect(() => {
    let cancelled = false;

    async function loadVideos(): Promise<void> {
      setVideosLoading(true);
      setVideosError(null);

      try {
        const result = await getWorkoutVideos();

        if (cancelled) {
          return;
        }

        setVideos(result);

        /*
         * Wenn noch keine Auswahl existiert, wählen wir das erste
         * verfügbare Video vor.
         *
         * Der Benutzer kann die Auswahl anschließend per Maus ändern.
         */
        setSelectedVideoId((currentVideoId) => {
          if (
            currentVideoId !== null &&
            result.some((video) => video.id === currentVideoId)
          ) {
            return currentVideoId;
          }

          return result[0]?.id ?? null;
        });
      } catch (loadError) {
        if (cancelled) {
          return;
        }

        const message =
          loadError instanceof Error
            ? loadError.message
            : "Trainingsvideos konnten nicht geladen werden";

        setVideos([]);
        setSelectedVideoId(null);
        setVideosError(message);
      } finally {
        if (!cancelled) {
          setVideosLoading(false);
        }
      }
    }

    void loadVideos();

    return () => {
      cancelled = true;
    };
  }, [loadAttempt]);

  useEffect(() => {
    function handleKeyDown(event: KeyboardEvent): void {
      if (event.key === "Enter") {
        if (selectedVideoId !== null && !startLoading) {
          onStart(selectedVideoId);
        }

        return;
      }

      if (event.key === "Escape") {
        onBack();
      }
    }

    window.addEventListener("keydown", handleKeyDown);

    return () => {
      window.removeEventListener("keydown", handleKeyDown);
    };
  }, [onStart, onBack, selectedVideoId, startLoading]);

  return (
    <section className="training-recommendation">
      <header className="recommendation-header">
        <div>
          <div className="eyebrow">HEUTE · {person.displayName}</div>

          <h1>Dein Training für heute</h1>
        </div>
      </header>

      <div className="recommendation-card">
        <div className="recommendation-summary">
          <div className="workout-type">
            {workoutTitle(recommendation.workoutType)}
          </div>

          <div className="workout-duration">
            {recommendation.totalDurationMinutes} min
          </div>
        </div>

        <div className="training-phases">
          {recommendation.phases.map((phase, index) => (
            <PhaseRow key={`${phase.phaseType}-${index}`} phase={phase} />
          ))}
        </div>

        <div className="recommendation-reason">
          <div className="reason-title">Warum dieses Training?</div>

          <p>{recommendation.reason}</p>
        </div>

        <div className="workout-video-selection">
          <div className="reason-title">Trainingsvideo</div>

          {videosLoading && (
            <div className="loading-state">Videos werden geladen …</div>
          )}

          {videosError !== null && (
            <div className="video-selection-error" role="alert">
              <div>{videosError}</div>

              <button
                type="button"
                className="secondary-action"
                onClick={() => {
                  setLoadAttempt((currentAttempt) => currentAttempt + 1);
                }}
              >
                Erneut laden
              </button>
            </div>
          )}

          {!videosLoading && videosError === null && videos.length === 0 && (
            <div className="empty-state">Keine Trainingsvideos verfügbar.</div>
          )}

          {!videosLoading && videos.length > 0 && (
            <div className="workout-video-options">
              {videos.map((video) => (
                <button
                  key={video.id}
                  type="button"
                  className={
                    selectedVideoId === video.id
                      ? "workout-video-option selected"
                      : "workout-video-option"
                  }
                  aria-pressed={selectedVideoId === video.id}
                  onClick={() => {
                    setSelectedVideoId(video.id);
                    onClearStartError();
                  }}
                >
                  <span className="workout-video-option-title">
                    {video.title}
                  </span>

                  {video.description !== null && (
                    <span className="workout-video-option-description">
                      {video.description}
                    </span>
                  )}
                </button>
              ))}
            </div>
          )}
        </div>
      </div>

      {startError !== null && (
        <div className="error-message" role="alert">
          {startError}
        </div>
      )}

      <footer className="recommendation-actions">
        <button type="button" className="secondary-action" onClick={onBack}>
          Zurück
        </button>

        <button
          type="button"
          className="primary-action"
          disabled={selectedVideoId === null || startLoading}
          onClick={() => {
            if (selectedVideoId !== null && !startLoading) {
              onStart(selectedVideoId)
            }
          }}
        >
          {startLoading ? 'Training wird gestartet …' : 'Training starten'}
        </button>
      </footer>
    </section>
  );
}
