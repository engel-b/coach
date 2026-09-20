import type { WorkoutVideoAdmin, WorkoutVideoMutation } from "../workout/types";
import { readApiError } from "./apiError";

export async function getManagedWorkoutVideos(): Promise<WorkoutVideoAdmin[]> {
  const response = await fetch("/api/admin/workout-videos");

  if (!response.ok) {
    throw await readApiError(
      response,
      "Trainingsvideos konnten nicht geladen werden",
    );
  }

  return (await response.json()) as WorkoutVideoAdmin[];
}

export async function createWorkoutVideo(
  request: WorkoutVideoMutation,
): Promise<WorkoutVideoAdmin> {
  const response = await fetch("/api/workout-videos", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    throw await readApiError(
      response,
      "Trainingsvideo konnte nicht angelegt werden",
    );
  }

  return (await response.json()) as WorkoutVideoAdmin;
}

export async function updateWorkoutVideo(
  videoId: string,
  request: WorkoutVideoMutation,
): Promise<WorkoutVideoAdmin> {
  const response = await fetch(
    `/api/workout-videos/${encodeURIComponent(videoId)}`,
    {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(request),
    },
  );

  if (!response.ok) {
    throw await readApiError(
      response,
      "Trainingsvideo konnte nicht gespeichert werden",
    );
  }

  return (await response.json()) as WorkoutVideoAdmin;
}

export async function deactivateWorkoutVideo(videoId: string): Promise<void> {
  const response = await fetch(
    `/api/workout-videos/${encodeURIComponent(videoId)}`,
    { method: "DELETE" },
  );

  if (!response.ok) {
    throw await readApiError(
      response,
      "Trainingsvideo konnte nicht deaktiviert werden",
    );
  }
}
