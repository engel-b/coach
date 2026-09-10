import { afterEach, describe, expect, it, vi } from "vitest";

import {
  finishWorkout,
  getWorkoutVideo,
  getWorkoutVideos,
  startWorkout,
} from "./workouts";

describe("getWorkoutVideo", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("loads a workout video from the catalog", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({
        id: "Lqhq5UQ-U8A",
        title: "Alpen",
        description: "Trainingsvideo Alpen",
        url: "/videos/cycling/alpen.mp4",
        durationSeconds: 3600,
      }),
    });

    vi.stubGlobal("fetch", fetchMock);

    const video = await getWorkoutVideo("Lqhq5UQ-U8A");

    expect(fetchMock).toHaveBeenCalledWith("/api/workout-videos/Lqhq5UQ-U8A");
    expect(video.id).toBe("Lqhq5UQ-U8A");
    expect(video.url).toBe("/videos/cycling/alpen.mp4");
    expect(video.durationSeconds).toBe(3600);
  });

  it("encodes the video ID as a URL segment", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({
        id: "video mit leerzeichen",
        title: "Test",
        description: null,
        url: "/videos/cycling/test.mp4",
        durationSeconds: null,
      }),
    });

    vi.stubGlobal("fetch", fetchMock);

    await getWorkoutVideo("video mit leerzeichen");

    expect(fetchMock).toHaveBeenCalledWith(
      "/api/workout-videos/video%20mit%20leerzeichen",
    );
  });

  it("throws an error when the API request fails", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: false,
      status: 404,
    });

    vi.stubGlobal("fetch", fetchMock);

    await expect(getWorkoutVideo("unknown-video")).rejects.toThrow(
      "Could not load workout video: HTTP 404",
    );
  });
});

describe("getWorkoutVideos", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("loads the available workout videos", async () => {
    const videos = [
      {
        id: "Lqhq5UQ-U8A",
        title: "Alpen",
        description: "Trainingsvideo Alpen",
        url: "/videos/cycling/alpen.mp4",
        durationSeconds: 3600,
      },
    ];

    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => videos,
    });

    vi.stubGlobal("fetch", fetchMock);

    const result = await getWorkoutVideos();

    expect(fetchMock).toHaveBeenCalledWith("/api/workout-videos");
    expect(result).toEqual(videos);
  });

  it("throws when the catalog cannot be loaded", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: false,
        status: 503,
      }),
    );

    await expect(getWorkoutVideos()).rejects.toThrow(
      "Could not load workout videos: HTTP 503",
    );
  });
});

describe("startWorkout", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("starts without a video selection using the existing request", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ id: "workout-1" }),
    });

    vi.stubGlobal("fetch", fetchMock);

    await startWorkout(1);

    expect(fetchMock).toHaveBeenCalledWith("/api/persons/1/workouts", {
      method: "POST",
    });
  });

  it("sends an explicitly selected video ID", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({
        id: "workout-1",
        videoId: "cycling-kueste-01",
      }),
    });

    vi.stubGlobal("fetch", fetchMock);

    await startWorkout(1, "cycling-kueste-01");

    expect(fetchMock).toHaveBeenCalledWith("/api/persons/1/workouts", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        videoId: "cycling-kueste-01",
      }),
    });
  });
});

describe("finishWorkout", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("sends the final workout values to the finish endpoint", async () => {
    const finishedWorkout = {
      id: "workout-1",
      status: "completed",
      elapsedSeconds: 1937,
      distanceM: 12345,
    };

    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => finishedWorkout,
    });

    vi.stubGlobal("fetch", fetchMock);

    const result = await finishWorkout("workout-1", 1937, 12345);

    expect(fetchMock).toHaveBeenCalledWith("/api/workouts/workout-1/finish", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        elapsedSeconds: 1937,
        distanceM: 12345,
      }),
    });

    expect(result).toEqual(finishedWorkout);
  });

  it("throws when the workout cannot be finished", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: false,
        status: 409,
      }),
    );

    await expect(finishWorkout("workout-1", 100, 500)).rejects.toThrow(
      "Could not finish workout: HTTP 409",
    );
  });
});
