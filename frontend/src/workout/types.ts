export type WorkoutStatus = "running" | "completed" | "aborted";

export type WorkoutRuntimeState =
  "running" | "paused" | "finish_window" | "overtime";

export interface WorkoutPhase {
  phaseType: "warm_up" | "main" | "cool_down";
  durationMinutes: number;
  targetHeartRateMin: number;
  targetHeartRateMax: number;
}

export interface Workout {
  id: string;
  personId: number;
  startedAt: string;
  status: WorkoutStatus;
  totalDurationMinutes: number;
  elapsedSeconds: number;
  distanceM: number;
  videoId: string;
  videoPositionSeconds: number;
  completedAt: string | null;
  phases: WorkoutPhase[];
}

export interface WorkoutVideo {
  id: string;
  title: string;
  description: string | null;
  url: string;
  durationSeconds: number | null;
  active: boolean;
}

export interface WorkoutVideoAdmin extends WorkoutVideo {
  filePath: string;
}

export interface WorkoutVideoMutation {
  title: string;
  description: string | null;
  filePath: string;
  durationSeconds: number | null;
  active: boolean;
}

export interface WorkoutVideoSelection extends WorkoutVideo {
  usageCount: number;
  isNew: boolean;
  isLastUsed: boolean;
  lastUsedAt: string | null;
}
