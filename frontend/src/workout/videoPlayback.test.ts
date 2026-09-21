import { describe, expect, it } from "vitest";

import {
  calculateVideoPlaybackRate,
  isBikeMoving,
  workoutVideoUrl,
} from "./videoPlayback";

describe("isBikeMoving", () => {
  it("returns unknown while no bike telemetry is known", () => {
    expect(isBikeMoving(null, null)).toBeNull();
  });

  it("uses cadence when cadence is available", () => {
    expect(isBikeMoving(82, 25)).toBe(true);

    expect(isBikeMoving(0, 25)).toBe(false);
  });

  it("uses speed as fallback when cadence is unavailable", () => {
    expect(isBikeMoving(null, 25)).toBe(true);

    expect(isBikeMoving(null, 0)).toBe(false);
  });

  it("treats negative cadence and speed as stopped", () => {
    expect(isBikeMoving(-1, 25)).toBe(false);

    expect(isBikeMoving(null, -1)).toBe(false);
  });
});

describe("calculateVideoPlaybackRate", () => {
  it("uses normal playback while no bike speed is known", () => {
    expect(calculateVideoPlaybackRate(null)).toBe(1);
  });

  it("uses normal playback at the reference speed", () => {
    expect(calculateVideoPlaybackRate(20)).toBe(1);
  });

  it("slows the video down below the reference speed", () => {
    expect(calculateVideoPlaybackRate(15)).toBe(0.75);
  });

  it("speeds the video up above the reference speed", () => {
    expect(calculateVideoPlaybackRate(30)).toBe(1.5);
  });

  it("does not go below the minimum playback rate", () => {
    expect(calculateVideoPlaybackRate(5)).toBe(0.5);

    expect(calculateVideoPlaybackRate(0)).toBe(0.5);
  });

  it("does not exceed the maximum playback rate", () => {
    expect(calculateVideoPlaybackRate(40)).toBe(2);

    expect(calculateVideoPlaybackRate(60)).toBe(2);
  });
});

describe("workoutVideoUrl", () => {
  it("builds the public URL from the relative catalog path", () => {
    expect(workoutVideoUrl("cycling/alpen.mp4")).toBe(
      "/videos/cycling/alpen.mp4",
    );
  });

  it("encodes individual path segments", () => {
    expect(workoutVideoUrl("Meine Tour/frühstück.mp4")).toBe(
      "/videos/Meine%20Tour/fr%C3%BChst%C3%BCck.mp4",
    );
  });
});
