import { useEffect, useState } from "react";
import type { FormEvent } from "react";

import {
  createPerson,
  getPersonProfile,
  updatePersonProfile,
} from "../api/persons";
import type {
  Person,
  PersonProfile,
  TrainingGoal,
  UpdatePersonProfileRequest,
} from "./types";

interface PersonProfileEditorProps {
  person: Person | null;
  onSaved: (person: Person) => void;
  onCancel: () => void;
}

function optionalNumber(value: string): number | null {
  if (value.trim() === "") {
    return null;
  }

  const number = Number(value);
  return Number.isFinite(number) ? number : null;
}

function ProfileForm({
  profile,
  creating,
  saving,
  error,
  onSubmit,
  onCancel,
}: {
  profile: PersonProfile | null;
  creating: boolean;
  saving: boolean;
  error: string | null;
  onSubmit: (event: FormEvent<HTMLFormElement>) => void;
  onCancel: () => void;
}) {
  const [trainingGoal, setTrainingGoal] = useState<TrainingGoal>(
    profile?.trainingGoal ?? "general_fitness",
  );

  const weightLoss = trainingGoal === "weight_loss";

  return (
    <section className="person-profile-editor">
      <header>
        <div className="eyebrow">PERSONENPROFIL</div>
        <h1>{creating ? "Person hinzufügen" : "Profil bearbeiten"}</h1>
      </header>

      <form className="person-profile-form" onSubmit={onSubmit}>
        <label>
          <span>Name</span>
          <input
            name="displayName"
            type="text"
            defaultValue={profile?.displayName ?? ""}
            required
            maxLength={100}
            autoFocus
          />
        </label>

        <label>
          <span>Geburtsdatum</span>
          <input
            name="dateOfBirth"
            type="date"
            defaultValue={profile?.dateOfBirth ?? ""}
            required
          />
        </label>

        <label>
          <span>Größe in cm</span>
          <input
            name="heightCm"
            type="number"
            min={100}
            max={250}
            defaultValue={profile?.heightCm ?? ""}
            required
          />
        </label>

        <label>
          <span>Trainingsziel</span>
          <select
            name="trainingGoal"
            value={trainingGoal}
            onChange={(event) =>
              setTrainingGoal(event.target.value as TrainingGoal)
            }
          >
            <option value="general_fitness">Fitness</option>
            <option value="muscle_gain">Muskelaufbau</option>
            <option value="weight_loss">Abnehmen</option>
            <option value="endurance">Ausdauer</option>
          </select>
        </label>

        <label>
          <span>Maximalpuls</span>
          <input
            name="maxHeartRateBpm"
            type="number"
            min={100}
            max={230}
            defaultValue={profile?.maxHeartRateBpm ?? ""}
            placeholder="optional"
          />
        </label>

        <label>
          <span>Startgewicht in kg</span>
          <input
            name="startWeightKg"
            type="number"
            min="0.1"
            max="500"
            step="0.1"
            defaultValue={profile?.startWeightKg ?? ""}
            placeholder={weightLoss ? "erforderlich" : "optional"}
            required={weightLoss}
          />
        </label>

        <label>
          <span>Zielgewicht in kg</span>
          <input
            name="targetWeightKg"
            type="number"
            min="0.1"
            max="500"
            step="0.1"
            defaultValue={profile?.targetWeightKg ?? ""}
            placeholder={weightLoss ? "erforderlich" : "optional"}
            required={weightLoss}
          />
        </label>

        {error !== null && (
          <div className="error-message" role="alert">
            {error}
          </div>
        )}

        <div className="person-profile-actions">
          <button
            type="button"
            className="secondary-action"
            onClick={onCancel}
            disabled={saving}
          >
            Abbrechen
          </button>

          <button type="submit" className="primary-action" disabled={saving}>
            {saving
              ? "Wird gespeichert …"
              : creating
                ? "Person anlegen"
                : "Speichern"}
          </button>
        </div>
      </form>
    </section>
  );
}

export function PersonProfileEditor({
  person,
  onSaved,
  onCancel,
}: PersonProfileEditorProps) {
  const creating = person === null;
  const [profile, setProfile] = useState<PersonProfile | null>(null);
  const [loading, setLoading] = useState(!creating);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (person === null) {
      return;
    }

    let cancelled = false;

    async function loadProfile(): Promise<void> {
      setLoading(true);
      setError(null);

      try {
        const result = await getPersonProfile(person!.id);

        if (!cancelled) {
          setProfile(result);
        }
      } catch (loadError) {
        if (!cancelled) {
          setError(
            loadError instanceof Error
              ? loadError.message
              : "Profil konnte nicht geladen werden",
          );
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    void loadProfile();

    return () => {
      cancelled = true;
    };
  }, [person]);

  async function handleSubmit(
    event: FormEvent<HTMLFormElement>,
  ): Promise<void> {
    event.preventDefault();

    if (saving) {
      return;
    }

    const formData = new FormData(event.currentTarget);

    const request: UpdatePersonProfileRequest = {
      displayName: String(formData.get("displayName") ?? ""),
      dateOfBirth: String(formData.get("dateOfBirth") ?? ""),
      heightCm: Number(formData.get("heightCm")),
      trainingGoal: String(formData.get("trainingGoal")) as TrainingGoal,
      maxHeartRateBpm: optionalNumber(
        String(formData.get("maxHeartRateBpm") ?? ""),
      ),
      startWeightKg: optionalNumber(
        String(formData.get("startWeightKg") ?? ""),
      ),
      targetWeightKg: optionalNumber(
        String(formData.get("targetWeightKg") ?? ""),
      ),
    };

    if (
      request.trainingGoal === "weight_loss" &&
      request.startWeightKg !== null &&
      request.targetWeightKg !== null &&
      request.targetWeightKg >= request.startWeightKg
    ) {
      setError("Das Zielgewicht muss unter dem Startgewicht liegen.");
      return;
    }

    setSaving(true);
    setError(null);

    try {
      const saved =
        person === null
          ? await createPerson(request)
          : await updatePersonProfile(person.id, request);

      onSaved({
        id: saved.personId,
        displayName: saved.displayName,
      });
    } catch (saveError) {
      setError(
        saveError instanceof Error
          ? saveError.message
          : "Profil konnte nicht gespeichert werden",
      );
    } finally {
      setSaving(false);
    }
  }

  if (loading) {
    return <div className="loading-state">Profil wird geladen …</div>;
  }

  if (error !== null && !creating && profile === null) {
    return (
      <section className="person-profile-editor">
        <div className="error-message" role="alert">
          {error}
        </div>
        <button type="button" className="secondary-action" onClick={onCancel}>
          Zurück
        </button>
      </section>
    );
  }

  return (
    <ProfileForm
      profile={profile}
      creating={creating}
      saving={saving}
      error={error}
      onSubmit={(event) => {
        void handleSubmit(event);
      }}
      onCancel={onCancel}
    />
  );
}