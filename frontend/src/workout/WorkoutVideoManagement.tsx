import { useEffect, useState } from "react";
import type { FormEvent } from "react";

import {
  createWorkoutVideo,
  deactivateWorkoutVideo,
  getManagedWorkoutVideos,
  updateWorkoutVideo,
} from "../api/workout-videos";
import type { WorkoutVideoAdmin, WorkoutVideoMutation } from "./types";

interface WorkoutVideoManagementProps {
  onClose: () => void;
}

interface WorkoutVideoFormProps {
  video: WorkoutVideoAdmin | null;
  saving: boolean;
  error: string | null;
  onSubmit: (request: WorkoutVideoMutation) => void;
  onCancel: () => void;
}

function optionalDuration(value: string): number | null {
  if (value.trim() === "") {
    return null;
  }

  const duration = Number(value);
  return Number.isFinite(duration) ? duration : null;
}

function WorkoutVideoForm({
  video,
  saving,
  error,
  onSubmit,
  onCancel,
}: WorkoutVideoFormProps) {
  function handleSubmit(event: FormEvent<HTMLFormElement>): void {
    event.preventDefault();

    const formData = new FormData(event.currentTarget);
    const durationValue = String(formData.get("durationSeconds") ?? "");
    const description = String(formData.get("description") ?? "").trim();

    onSubmit({
      title: String(formData.get("title") ?? "").trim(),
      description: description === "" ? null : description,
      filePath: String(formData.get("filePath") ?? "").trim(),
      durationSeconds: optionalDuration(durationValue),
      active: formData.get("active") === "on",
    });
  }

  return (
    <section className="video-editor">
      <div className="eyebrow">TRAININGSVIDEO</div>
      <h2>{video === null ? "Video hinzufügen" : "Video bearbeiten"}</h2>

      <form className="video-editor-form" onSubmit={handleSubmit}>
        <label>
          <span>Titel</span>
          <input
            name="title"
            type="text"
            defaultValue={video?.title ?? ""}
            required
            maxLength={200}
            autoFocus
          />
        </label>

        <label>
          <span>Beschreibung</span>
          <textarea
            name="description"
            rows={3}
            defaultValue={video?.description ?? ""}
            placeholder="optional"
          />
        </label>

        <label>
          <span>Dateipfad</span>
          <input
            name="filePath"
            type="text"
            defaultValue={video?.filePath ?? ""}
            placeholder="cycling/alpen.mp4"
            required
          />
          <small>Relativer MP4-Pfad innerhalb des Videoverzeichnisses.</small>
        </label>

        <label>
          <span>Dauer in Sekunden</span>
          <input
            name="durationSeconds"
            type="number"
            min={0}
            step="any"
            defaultValue={video?.durationSeconds ?? ""}
            placeholder="optional"
          />
        </label>

        <label className="video-active-field">
          <input
            name="active"
            type="checkbox"
            defaultChecked={video?.active ?? true}
          />
          <span>Video ist aktiv und auswählbar</span>
        </label>

        {error !== null && (
          <div className="error-message" role="alert">
            {error}
          </div>
        )}

        <div className="video-editor-actions">
          <button
            type="button"
            className="secondary-action"
            onClick={onCancel}
            disabled={saving}
          >
            Abbrechen
          </button>
          <button type="submit" className="primary-action" disabled={saving}>
            {saving ? "Wird gespeichert …" : "Speichern"}
          </button>
        </div>
      </form>
    </section>
  );
}

export function WorkoutVideoManagement({
  onClose,
}: WorkoutVideoManagementProps) {
  const [videos, setVideos] = useState<WorkoutVideoAdmin[]>([]);
  const [editingVideo, setEditingVideo] = useState<
    WorkoutVideoAdmin | null | undefined
  >(undefined);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [deactivatingId, setDeactivatingId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [formError, setFormError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function loadVideos(): Promise<void> {
      try {
        const result = await getManagedWorkoutVideos();

        if (!cancelled) {
          setVideos(result);
          setError(null);
        }
      } catch (loadError) {
        if (!cancelled) {
          setError(
            loadError instanceof Error
              ? loadError.message
              : "Trainingsvideos konnten nicht geladen werden",
          );
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    void loadVideos();

    return () => {
      cancelled = true;
    };
  }, []);

  async function handleSave(request: WorkoutVideoMutation): Promise<void> {
    if (request.title === "") {
      setFormError("Bitte gib einen Titel ein.");
      return;
    }

    if (request.filePath === "") {
      setFormError("Bitte gib einen Dateipfad ein.");
      return;
    }

    if (request.durationSeconds !== null && request.durationSeconds < 0) {
      setFormError("Die Dauer darf nicht negativ sein.");
      return;
    }

    setSaving(true);
    setFormError(null);

    try {
      const saved =
        editingVideo === null
          ? await createWorkoutVideo(request)
          : await updateWorkoutVideo(editingVideo!.id, request);

      setVideos((currentVideos) => {
        const exists = currentVideos.some((video) => video.id === saved.id);

        if (!exists) {
          return [...currentVideos, saved];
        }

        return currentVideos.map((video) =>
          video.id === saved.id ? saved : video,
        );
      });
      setEditingVideo(undefined);
    } catch (saveError) {
      setFormError(
        saveError instanceof Error
          ? saveError.message
          : "Trainingsvideo konnte nicht gespeichert werden",
      );
    } finally {
      setSaving(false);
    }
  }

  async function handleDeactivate(video: WorkoutVideoAdmin): Promise<void> {
    if (deactivatingId !== null) {
      return;
    }

    setDeactivatingId(video.id);
    setError(null);

    try {
      await deactivateWorkoutVideo(video.id);
      setVideos((currentVideos) =>
        currentVideos.map((currentVideo) =>
          currentVideo.id === video.id
            ? { ...currentVideo, active: false }
            : currentVideo,
        ),
      );
    } catch (deactivateError) {
      setError(
        deactivateError instanceof Error
          ? deactivateError.message
          : "Trainingsvideo konnte nicht deaktiviert werden",
      );
    } finally {
      setDeactivatingId(null);
    }
  }

  if (editingVideo !== undefined) {
    return (
      <div className="video-management">
        <WorkoutVideoForm
          key={editingVideo?.id ?? "new"}
          video={editingVideo}
          saving={saving}
          error={formError}
          onSubmit={(request) => {
            void handleSave(request);
          }}
          onCancel={() => {
            setEditingVideo(undefined);
            setFormError(null);
          }}
        />
      </div>
    );
  }

  return (
    <section className="video-management">
      <header className="video-management-header">
        <div>
          <div className="eyebrow">VERWALTUNG</div>
          <h1>Trainingsvideos</h1>
          <p>Videos anlegen, bearbeiten und für die Auswahl freigeben.</p>
        </div>
        <div className="video-management-header-actions">
          <button type="button" className="secondary-action" onClick={onClose}>
            Zurück
          </button>
          <button
            type="button"
            className="primary-action"
            onClick={() => {
              setEditingVideo(null);
              setFormError(null);
            }}
          >
            + Video hinzufügen
          </button>
        </div>
      </header>

      {error !== null && (
        <div className="error-message" role="alert">
          {error}
        </div>
      )}

      {loading ? (
        <div className="loading-state">Videos werden geladen …</div>
      ) : videos.length === 0 ? (
        <div className="empty-state">Noch keine Trainingsvideos vorhanden.</div>
      ) : (
        <div className="video-management-list">
          {videos.map((video) => (
            <article key={video.id} className="video-management-row">
              <div className="video-management-details">
                <div className="video-management-title">
                  <strong>{video.title}</strong>
                  <span className={video.active ? "active" : "inactive"}>
                    {video.active ? "Aktiv" : "Inaktiv"}
                  </span>
                </div>
                <p>{video.description ?? "Keine Beschreibung"}</p>
                <code>{video.filePath}</code>
              </div>

              <div className="video-management-actions">
                <button
                  type="button"
                  className="secondary-action"
                  onClick={() => {
                    setEditingVideo(video);
                    setFormError(null);
                  }}
                >
                  Bearbeiten
                </button>
                {video.active && (
                  <button
                    type="button"
                    className="danger-action"
                    disabled={deactivatingId === video.id}
                    onClick={() => {
                      void handleDeactivate(video);
                    }}
                  >
                    {deactivatingId === video.id
                      ? "Wird deaktiviert …"
                      : "Deaktivieren"}
                  </button>
                )}
              </div>
            </article>
          ))}
        </div>
      )}
    </section>
  );
}
