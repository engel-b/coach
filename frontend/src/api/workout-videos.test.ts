import { afterEach, describe, expect, it, vi } from "vitest";

import {
  createWorkoutVideo,
  deactivateWorkoutVideo,
  getManagedWorkoutVideos,
  updateWorkoutVideo,
} from "./workout-videos";

const request = {
  title: "Alpen",
  description: "Trainingsvideo Alpen",
  filePath: "cycling/alpen.mp4",
  durationSeconds: 3600,
  active: true,
};

describe("workout video management API", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("loads all videos through the management endpoint", async () => {
    const videos = [
      { id: "video-1", url: "/videos/cycling/alpen.mp4", ...request },
    ];
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => videos,
    });
    vi.stubGlobal("fetch", fetchMock);

    await expect(getManagedWorkoutVideos()).resolves.toEqual(videos);
    expect(fetchMock).toHaveBeenCalledWith("/api/workout-videos");
  });

  it("creates a video with the mutation contract", async () => {
    const created = {
      id: "video-1",
      url: "/videos/cycling/alpen.mp4",
      ...request,
    };
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => created,
    });
    vi.stubGlobal("fetch", fetchMock);

    await expect(createWorkoutVideo(request)).resolves.toEqual(created);
    expect(fetchMock).toHaveBeenCalledWith("/api/workout-videos", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(request),
    });
  });

  it("updates an encoded video ID", async () => {
    const updated = {
      id: "video id",
      url: "/videos/cycling/alpen.mp4",
      ...request,
    };
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => updated,
    });
    vi.stubGlobal("fetch", fetchMock);

    await updateWorkoutVideo("video id", request);

    expect(fetchMock).toHaveBeenCalledWith("/api/workout-videos/video%20id", {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(request),
    });
  });

  it("deactivates an encoded video ID", async () => {
    const fetchMock = vi.fn().mockResolvedValue({ ok: true });
    vi.stubGlobal("fetch", fetchMock);

    await deactivateWorkoutVideo("video id");

    expect(fetchMock).toHaveBeenCalledWith("/api/workout-videos/video%20id", {
      method: "DELETE",
    });
  });
});
