import { afterEach, describe, expect, it, vi } from "vitest";

import { getWorkoutVideo, getWorkoutVideos } from "./workouts";

describe("getWorkoutVideo", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("loads a workout video from the catalog", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({
        id: "cycling-alpen-01",
        title: "Alpen",
        description: "Trainingsvideo Alpen",
        url: "/videos/cycling/alpen.mp4",
        durationSeconds: 3600,
      }),
    });

    vi.stubGlobal("fetch", fetchMock);

    const video = await getWorkoutVideo("cycling-alpen-01");

    expect(fetchMock).toHaveBeenCalledWith(
      "/api/workout-videos/cycling-alpen-01",
    );
    expect(video.id).toBe("cycling-alpen-01");
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
        id: "cycling-alpen-01",
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
