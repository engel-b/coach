import { useEffect, useState } from "react";

import { getWorkoutVideosForPerson } from "../api/workouts";
import type { Person } from "../persons/types";
import type { WorkoutVideoSelection } from "../workout/types";
import {
  recommendationReasonLabels,
  workoutTitle,
} from "./recommendationPresentation";
import { WeightGoalProgress } from "./WeightGoalProgress";
import type {
  TrainingRecommendation,
  WorkoutPhase,
  WorkoutPhaseType,
} from "./types";

interface TrainingRecommendationViewProps {
  person: Person;
  recommendation: TrainingRecommendation;
  onStart: (videoId: string) => void;
  onBack: () => void;
  startLoading: boolean;
  startError: string | null;
  onClearStartError: () => void;
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

function HeartRateTargetExplanation({
  recommendation,
}: {
  recommendation: TrainingRecommendation;
}) {
  const basis = recommendation.heartRateTargetBasis;
  const mainPhase =
    recommendation.phases.find((phase) => phase.phaseType === "main") ??
    recommendation.phases[0];

  if (mainPhase === undefined) {
    return null;
  }

  const usesReserve = basis.method === "heart_rate_reserve";
  const referenceWasLimited =
    usesReserve &&
    basis.restingHeartRateBpm !== null &&
    basis.referenceRestingHeartRateBpm !== null &&
    basis.restingHeartRateBpm !== basis.referenceRestingHeartRateBpm;

  return (
    <div className="heart-rate-target-explanation">
      <div className="reason-title">So entsteht dein Zielpuls</div>

      <div className="heart-rate-target-summary">
        <strong>
          {phaseTitle(mainPhase.phaseType)}: {mainPhase.targetHeartRateMin}–
          {mainPhase.targetHeartRateMax} bpm
        </strong>
      </div>

      <dl className="heart-rate-target-details">
        <div>
          <dt>HFmax</dt>
          <dd>{basis.maxHeartRateBpm} bpm</dd>
        </div>
        <div>
          <dt>Methode</dt>
          <dd>
            {usesReserve
              ? "Herzfrequenzreserve"
              : "Prozent der maximalen Herzfrequenz"}
          </dd>
        </div>
        {basis.restingHeartRateBpm !== null && (
          <div>
            <dt>Ruhepuls</dt>
            <dd>
              {basis.restingHeartRateBpm} bpm
              {basis.restingHeartRateSource === "check_in_baseline"
                ? ` · Baseline aus ${basis.restingHeartRateSampleCount} Messungen`
                : basis.restingHeartRateSource === "profile"
                  ? " · Profilwert"
                  : ""}
            </dd>
          </div>
        )}
        {referenceWasLimited && (
          <div>
            <dt>Rechenwert Ruhepuls</dt>
            <dd>{basis.referenceRestingHeartRateBpm} bpm</dd>
          </div>
        )}
      </dl>

      {!usesReserve && (
        <p className="heart-rate-target-note">
          Noch keine belastbare Ruhepuls-Baseline verfügbar: Die Zielbereiche
          werden als Fallback aus der maximalen Herzfrequenz berechnet.
        </p>
      )}

      {referenceWasLimited && (
        <p className="heart-rate-target-note">
          Der hinterlegte Ruhepuls wird für die Zielberechnung konservativ auf{" "}
          {basis.referenceRestingHeartRateBpm} bpm begrenzt.
        </p>
      )}
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
  const [videos, setVideos] = useState<WorkoutVideoSelection[]>([]);
  const [selectedVideoId, setSelectedVideoId] = useState<string | null>(null);
  const [videosLoading, setVideosLoading] = useState(true);
  const [videosError, setVideosError] = useState<string | null>(null);
  const [loadAttempt, setLoadAttempt] = useState(0);
  const reasonLabels = recommendationReasonLabels(recommendation);

  useEffect(() => {
    let cancelled = false;

    async function loadVideos(): Promise<void> {
      setVideosLoading(true);
      setVideosError(null);

      try {
        const result = await getWorkoutVideosForPerson(person.id);

        if (cancelled) {
          return;
        }

        setVideos(result);

        setSelectedVideoId((currentVideoId) => {
          if (
            currentVideoId !== null &&
            result.some((video) => video.id === currentVideoId)
          ) {
            return currentVideoId;
          }

          return (
            result.find((video) => video.isLastUsed)?.id ??
            result[0]?.id ??
            null
          );
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
  }, [loadAttempt, person.id]);

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

        <HeartRateTargetExplanation recommendation={recommendation} />

        <div className="recommendation-reason">
          <div className="reason-title">Warum dieses Training?</div>

          <p>{recommendation.reason}</p>

          <WeightGoalProgress recommendation={recommendation} />

          {reasonLabels.length > 0 && (
            <div className="recommendation-reason-tags">
              {reasonLabels.map((label) => (
                <span key={label}>{label}</span>
              ))}
            </div>
          )}
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
            <div className="workout-video-combobox">
              <select
                value={selectedVideoId ?? ""}
                onChange={(event) => {
                  setSelectedVideoId(event.target.value);
                  onClearStartError();
                }}
                aria-label="Trainingsvideo auswählen"
              >
                {videos.map((video) => (
                  <option key={video.id} value={video.id}>
                    {video.isNew
                      ? `NEU · ${video.title}`
                      : `${video.title} · ${video.usageCount}× verwendet`}
                  </option>
                ))}
              </select>

              {videos.find((video) => video.id === selectedVideoId)?.isNew && (
                <span className="workout-video-new-badge">NEU</span>
              )}
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
              onStart(selectedVideoId);
            }
          }}
        >
          {startLoading ? "Training wird gestartet …" : "Training starten"}
        </button>
      </footer>
    </section>
  );
}
