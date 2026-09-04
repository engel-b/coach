import { useEffect, useState } from "react";

import { getWorkoutHistory } from "../api/workouts";
import type { Workout } from "./types";

interface WorkoutHistoryProps {
  personId: number;
}

function formatDuration(elapsedSeconds: number): string {
  const minutes = Math.floor(elapsedSeconds / 60);

  const seconds = elapsedSeconds % 60;

  return `${String(minutes).padStart(2, "0")}:${String(seconds).padStart(
    2,
    "0",
  )}`;
}

function formatDate(value: string): string {
  return new Intl.DateTimeFormat("de-DE", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
  }).format(new Date(value));
}

function statusLabel(status: Workout["status"]): string {
  switch (status) {
    case "running":
      return "Läuft";

    case "completed":
      return "Abgeschlossen";

    case "aborted":
      return "Abgebrochen";
  }
}

export function WorkoutHistory({ personId }: WorkoutHistoryProps) {
  const [workouts, setWorkouts] = useState<Workout[]>([]);

  const [loading, setLoading] = useState(true);

  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadHistory(): Promise<void> {
      try {
        setLoading(true);

        const result = await getWorkoutHistory(personId, 10);

        setWorkouts(result);
        setError(null);
      } catch (loadError) {
        const message =
          loadError instanceof Error ? loadError.message : "Unknown error";

        setError(message);
      } finally {
        setLoading(false);
      }
    }

    void loadHistory();
  }, [personId]);

  if (loading) {
    return (
      <section className="workout-history">
        <h2>Letzte Trainings</h2>

        <div className="loading-state">Trainings werden geladen …</div>
      </section>
    );
  }

  if (error !== null) {
    return (
      <section className="workout-history">
        <h2>Letzte Trainings</h2>

        <div className="error-message">{error}</div>
      </section>
    );
  }

  return (
    <section className="workout-history">
      <h2>Letzte Trainings</h2>

      {workouts.length === 0 ? (
        <div className="empty-state">Noch keine Trainings vorhanden.</div>
      ) : (
        <div className="workout-history-list">
          {workouts.map((workout) => (
            <article key={workout.id} className="workout-history-item">
              <div>
                <strong>{formatDate(workout.startedAt)}</strong>

                <div>{statusLabel(workout.status)}</div>
              </div>

              <div className="workout-history-duration">
                {formatDuration(workout.elapsedSeconds)}
              </div>
            </article>
          ))}
        </div>
      )}
    </section>
  );
}
