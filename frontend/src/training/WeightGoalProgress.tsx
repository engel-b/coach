import { weightGoalProgressPresentation } from "./recommendationPresentation";
import type { TrainingRecommendation } from "./types";

interface WeightGoalProgressProps {
  recommendation: TrainingRecommendation;
  compact?: boolean;
}

export function WeightGoalProgress({
  recommendation,
  compact = false,
}: WeightGoalProgressProps) {
  const progress = weightGoalProgressPresentation(recommendation);

  if (progress === null) {
    return null;
  }

  return (
    <div
      className={
        compact
          ? "weight-goal-progress weight-goal-progress-compact"
          : "weight-goal-progress"
      }
      aria-label="Fortschritt zum Zielgewicht"
    >
      <div className="weight-goal-progress-heading">
        <span>Ziel-Fortschritt</span>
        <strong>{progress.headline}</strong>
      </div>

      <div
        className="weight-goal-progress-track"
        role="progressbar"
        aria-valuemin={0}
        aria-valuemax={100}
        aria-valuenow={Math.round(progress.percent)}
      >
        <span style={{ width: `${progress.percent}%` }} />
      </div>

      <small>{progress.detail}</small>
    </div>
  );
}
