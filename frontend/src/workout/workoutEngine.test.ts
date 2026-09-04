import { describe, expect, it } from "vitest";

import {
  applyWorkoutEngineEvent,
  createWorkoutEngine,
  getFinishWindowRemainingSeconds,
  shouldCountWorkoutTime,
  shouldPlayWorkoutVideo,
  shouldShowFinishPrompt,
  type WorkoutEngineState,
} from "./workoutEngine";

function applyTick(state: WorkoutEngineState): WorkoutEngineState {
  return applyWorkoutEngineEvent(state, {
    type: "tick",
  }).state;
}

function applyTicks(
  state: WorkoutEngineState,
  count: number,
): WorkoutEngineState {
  let current = state;

  for (let index = 0; index < count; index += 1) {
    current = applyTick(current);
  }

  return current;
}

function setBikeMoving(
  state: WorkoutEngineState,
  moving: boolean | null,
): WorkoutEngineState {
  return applyWorkoutEngineEvent(state, {
    type: "bike_movement_changed",
    moving,
  }).state;
}

describe("workout engine", () => {
  it("starts in running state", () => {
    const state = createWorkoutEngine(1200);

    expect(state.state).toBe("running");

    expect(state.elapsedSeconds).toBe(0);

    expect(state.bikeMoving).toBeNull();
  });

  it("rejects invalid planned durations", () => {
    expect(() => createWorkoutEngine(0)).toThrow();

    expect(() => createWorkoutEngine(-1)).toThrow();

    expect(() => createWorkoutEngine(1.5)).toThrow();
  });

  it("counts normal workout time", () => {
    const state = applyTicks(createWorkoutEngine(100), 10);

    expect(state.state).toBe("running");

    expect(state.elapsedSeconds).toBe(10);
  });

  it("enters finish window when planned duration is reached", () => {
    let state = createWorkoutEngine(3);

    state = applyTick(state);
    state = applyTick(state);

    const transition = applyWorkoutEngineEvent(state, {
      type: "tick",
    });

    expect(transition.state.state).toBe("finish_window");

    expect(transition.state.elapsedSeconds).toBe(3);

    expect(transition.effects.playFinishSound).toBe(true);

    expect(getFinishWindowRemainingSeconds(transition.state)).toBe(30);
  });

  it("requests finish sound only on entry into finish window", () => {
    let state = createWorkoutEngine(1);

    const entry = applyWorkoutEngineEvent(state, {
      type: "tick",
    });

    expect(entry.effects.playFinishSound).toBe(true);

    state = entry.state;

    const nextTick = applyWorkoutEngineEvent(state, {
      type: "tick",
    });

    expect(nextTick.effects.playFinishSound).toBe(false);
  });

  it("enters overtime after 30 seconds of continued riding", () => {
    let state = createWorkoutEngine(1);

    state = applyTick(state);

    expect(state.state).toBe("finish_window");

    state = applyTicks(state, 30);

    expect(state.state).toBe("overtime");

    expect(state.finishWindowElapsedSeconds).toBe(30);

    expect(state.elapsedSeconds).toBe(31);
  });

  it("completes after three stopped seconds during finish window", () => {
    let state = createWorkoutEngine(1);

    state = applyTick(state);

    state = setBikeMoving(state, false);

    state = applyTick(state);

    expect(state.state).toBe("finish_window");

    state = applyTick(state);

    expect(state.state).toBe("finish_window");

    state = applyTick(state);

    expect(state.state).toBe("completed");
  });

  it("does not enter overtime when stopping at second 29 of finish window", () => {
    let state = createWorkoutEngine(1);

    state = applyTick(state);

    state = applyTicks(state, 29);

    expect(state.state).toBe("finish_window");

    expect(state.finishWindowElapsedSeconds).toBe(29);

    state = setBikeMoving(state, false);

    state = applyTicks(state, 3);

    expect(state.state).toBe("completed");
  });

  it("ignores a transient bike stop shorter than debounce period", () => {
    let state = createWorkoutEngine(100);

    state = setBikeMoving(state, false);

    state = applyTick(state);
    state = applyTick(state);

    expect(state.state).toBe("running");

    state = setBikeMoving(state, true);

    expect(state.bikeStoppedForSeconds).toBe(0);

    state = applyTick(state);

    expect(state.state).toBe("running");
  });

  it("auto-pauses after three stopped seconds", () => {
    let state = createWorkoutEngine(100);

    state = setBikeMoving(state, false);

    state = applyTicks(state, 3);

    expect(state.state).toBe("paused");

    expect(state.pauseReason).toBe("bike");

    expect(state.pausedFrom).toBe("running");
  });

  it("auto-resumes a bike pause when movement returns", () => {
    let state = createWorkoutEngine(100);

    state = setBikeMoving(state, false);

    state = applyTicks(state, 3);

    expect(state.state).toBe("paused");

    state = setBikeMoving(state, true);

    expect(state.state).toBe("running");

    expect(state.pauseReason).toBeNull();

    expect(state.pausedFrom).toBeNull();
  });

  it("does not auto-resume a manual pause", () => {
    let state = createWorkoutEngine(100);

    state = applyWorkoutEngineEvent(state, {
      type: "manual_pause",
    }).state;

    expect(state.state).toBe("paused");

    expect(state.pauseReason).toBe("manual");

    state = setBikeMoving(state, true);

    expect(state.state).toBe("paused");

    state = applyWorkoutEngineEvent(state, {
      type: "manual_resume",
    }).state;

    expect(state.state).toBe("running");
  });

  it("auto-pauses instead of completing when bike stops in overtime", () => {
    let state = createWorkoutEngine(1);

    state = applyTick(state);

    state = applyTicks(state, 30);

    expect(state.state).toBe("overtime");

    state = setBikeMoving(state, false);

    state = applyTicks(state, 3);

    expect(state.state).toBe("paused");

    expect(state.pauseReason).toBe("bike");

    expect(state.pausedFrom).toBe("overtime");
  });

  it("resumes overtime after an automatic bike pause", () => {
    let state = createWorkoutEngine(1);

    state = applyTick(state);

    state = applyTicks(state, 30);

    state = setBikeMoving(state, false);

    state = applyTicks(state, 3);

    state = setBikeMoving(state, true);

    expect(state.state).toBe("overtime");
  });

  it("exposes UI decisions through selectors", () => {
    let state = createWorkoutEngine(1);

    expect(shouldPlayWorkoutVideo(state)).toBe(true);

    expect(shouldCountWorkoutTime(state)).toBe(true);

    state = applyTick(state);

    expect(shouldShowFinishPrompt(state)).toBe(true);

    state = applyWorkoutEngineEvent(state, {
      type: "manual_pause",
    }).state;

    expect(shouldPlayWorkoutVideo(state)).toBe(false);

    expect(shouldCountWorkoutTime(state)).toBe(false);
  });

  it("makes aborted state terminal", () => {
    let state = createWorkoutEngine(100);

    state = applyWorkoutEngineEvent(state, {
      type: "abort_requested",
    }).state;

    expect(state.state).toBe("aborted");

    const afterTick = applyTick(state);

    expect(afterTick).toBe(state);
  });

  it("makes completed state terminal", () => {
    let state = createWorkoutEngine(1);

    state = applyTick(state);

    state = setBikeMoving(state, false);

    state = applyTicks(state, 3);

    expect(state.state).toBe("completed");

    const afterTick = applyTick(state);

    expect(afterTick).toBe(state);
  });
});
