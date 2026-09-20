import {
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import {
  createWorkoutVideo,
  deactivateWorkoutVideo,
  getManagedWorkoutVideos,
  updateWorkoutVideo,
} from "../api/workout-videos";
import { WorkoutVideoManagement } from "./WorkoutVideoManagement";

vi.mock("../api/workout-videos", () => ({
  createWorkoutVideo: vi.fn(),
  deactivateWorkoutVideo: vi.fn(),
  getManagedWorkoutVideos: vi.fn(),
  updateWorkoutVideo: vi.fn(),
}));

const getManagedWorkoutVideosMock = vi.mocked(getManagedWorkoutVideos);
const createWorkoutVideoMock = vi.mocked(createWorkoutVideo);
const updateWorkoutVideoMock = vi.mocked(updateWorkoutVideo);
const deactivateWorkoutVideoMock = vi.mocked(deactivateWorkoutVideo);

const video = {
  id: "video-1",
  title: "Alpen",
  description: "Trainingsvideo Alpen",
  url: "/videos/cycling/alpen.mp4",
  durationSeconds: 3600,
  active: true,
};

describe("WorkoutVideoManagement", () => {
  beforeEach(() => {
    getManagedWorkoutVideosMock.mockResolvedValue([video]);
  });

  afterEach(() => {
    cleanup();
    vi.clearAllMocks();
  });

  it("creates a workout video", async () => {
    const created = {
      ...video,
      id: "video-2",
      title: "Küste",
      description: null,
      url: "/videos/cycling/kueste.mp4",
      durationSeconds: 2700,
    };
    createWorkoutVideoMock.mockResolvedValue(created);

    render(<WorkoutVideoManagement onClose={vi.fn()} />);

    await screen.findByText("Alpen");
    fireEvent.click(screen.getByRole("button", { name: "+ Video hinzufügen" }));
    fireEvent.change(screen.getByLabelText("Titel"), {
      target: { value: "Küste" },
    });
    fireEvent.change(screen.getByLabelText(/Dateipfad/), {
      target: { value: "/videos/cycling/kueste.mp4" },
    });
    fireEvent.change(screen.getByLabelText("Dauer in Sekunden"), {
      target: { value: "2700" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Speichern" }));

    await waitFor(() => {
      expect(createWorkoutVideoMock).toHaveBeenCalledWith({
        title: "Küste",
        description: null,
        url: "/videos/cycling/kueste.mp4",
        durationSeconds: 2700,
        active: true,
      });
    });
    expect(await screen.findByText("Küste")).toBeTruthy();
  });

  it("edits and deactivates a workout video", async () => {
    const updated = { ...video, title: "Alpenrunde" };
    updateWorkoutVideoMock.mockResolvedValue(updated);
    deactivateWorkoutVideoMock.mockResolvedValue();

    render(<WorkoutVideoManagement onClose={vi.fn()} />);

    await screen.findByText("Alpen");
    fireEvent.click(screen.getByRole("button", { name: "Bearbeiten" }));
    fireEvent.change(screen.getByLabelText("Titel"), {
      target: { value: "Alpenrunde" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Speichern" }));

    expect(await screen.findByText("Alpenrunde")).toBeTruthy();
    expect(updateWorkoutVideoMock).toHaveBeenCalledWith("video-1", {
      title: "Alpenrunde",
      description: "Trainingsvideo Alpen",
      url: "/videos/cycling/alpen.mp4",
      durationSeconds: 3600,
      active: true,
    });

    fireEvent.click(screen.getByRole("button", { name: "Deaktivieren" }));

    await waitFor(() => {
      expect(deactivateWorkoutVideoMock).toHaveBeenCalledWith("video-1");
    });
    expect(await screen.findByText("Inaktiv")).toBeTruthy();
  });
});
