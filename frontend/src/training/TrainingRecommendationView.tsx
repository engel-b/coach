import type { Person } from "../persons/types";
import type {
  TrainingRecommendation,
  WorkoutPhase,
  WorkoutPhaseType,
  WorkoutType,
} from "./types";
import { useEffect } from "react";

interface TrainingRecommendationViewProps {
  person: Person;
  recommendation: TrainingRecommendation;
  onStart: () => void;
  onBack: () => void;
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
}: TrainingRecommendationViewProps) {
  useEffect(() => {
    function handleKeyDown(event: KeyboardEvent): void {
      if (event.key === "Enter") {
        onStart();
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
  }, [onStart, onBack]);
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
      </div>

      <footer className="recommendation-actions">
        <button type="button" className="secondary-action" onClick={onBack}>
          Zurück
        </button>

        <button type="button" className="primary-action" onClick={onStart}>
          Training starten
        </button>
      </footer>
    </section>
  );
}
