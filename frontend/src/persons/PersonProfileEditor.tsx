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

function formatDateForInput(isoDate: string): string {
  const match = /^(\d{4})-(\d{2})-(\d{2})$/.exec(isoDate);

  if (match === null) {
    return isoDate;
  }

  return `${match[3]}.${match[2]}.${match[1]}`;
}

function parseGermanDate(value: string): string | null {
  const match = /^(\d{2})\.(\d{2})\.(\d{4})$/.exec(value.trim());

  if (match === null) {
    return null;
  }

  const day = Number(match[1]);
  const month = Number(match[2]);
  const year = Number(match[3]);

  const date = new Date(Date.UTC(year, month - 1, day));
  date.setUTCFullYear(year);

  if (
    date.getUTCFullYear() !== year ||
    date.getUTCMonth() !== month - 1 ||
    date.getUTCDate() !== day
  ) {
    return null;
  }

  return `${match[3]}-${match[2]}-${match[1]}`;
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

      <form className="person-profile-form" onSubmit={onSubmit} noValidate>
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
            type="text"
            inputMode="numeric"
            placeholder="TT.MM.JJJJ"
            defaultValue={
              profile?.dateOfBirth
                ? formatDateForInput(profile.dateOfBirth)
                : ""
            }
            required
            maxLength={10}
            autoComplete="bday"
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
          <span className="field-hint">
            Optional. Trage deinen gemessenen oder ärztlich bestimmten
            Maximalpuls ein. Wenn du keinen Wert kennst, lass das Feld leer. Der
            Coach verwendet dann einen altersbasierten Schätzwert.
          </span>
        </label>

        <label>
          <span>Ruhepuls</span>
          <input
            name="restingHeartRateBpm"
            type="number"
            min={35}
            max={120}
            defaultValue={profile?.restingHeartRateBpm ?? ""}
            placeholder="optional"
          />
          <span className="field-hint">
            Optional. Verwende einen typischen Ruhewert, der mehrfach in ruhiger
            Situation gemessen wurde. Er personalisiert die
            Trainings-Zielbereiche; ein hoher Wert hebt die Grenzen nicht
            unbegrenzt an.
          </span>
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

  function validateProfileRequest(
    request: UpdatePersonProfileRequest,
  ): string | null {
    if (request.displayName.trim() === "") {
      return "Bitte gib einen Namen ein.";
    }

    if (request.dateOfBirth === "") {
      return "Bitte gib dein Geburtsdatum ein.";
    }

    if (request.heightCm < 100 || request.heightCm > 250) {
      return "Bitte gib eine Körpergröße zwischen 100 und 250 cm ein.";
    }

    if (request.trainingGoal === "weight_loss") {
      if (request.startWeightKg === null) {
        return "Bitte gib dein Startgewicht ein.";
      }

      if (request.targetWeightKg === null) {
        return "Bitte gib dein Zielgewicht ein.";
      }

      if (request.targetWeightKg >= request.startWeightKg) {
        return "Das Zielgewicht muss unter dem Startgewicht liegen.";
      }
    }

    return null;
  }

  async function handleSubmit(
    event: FormEvent<HTMLFormElement>,
  ): Promise<void> {
    event.preventDefault();

    if (saving) {
      return;
    }

    const formData = new FormData(event.currentTarget);

    const dateInput = String(formData.get("dateOfBirth") ?? "").trim();
    const parsedDate = parseGermanDate(dateInput);

    if (dateInput === "") {
      setError("Bitte gib dein Geburtsdatum ein.");
      return;
    }

    if (parsedDate === null) {
      setError("Bitte gib das Datum im Format TT.MM.JJJJ ein.");
      return;
    }

    const request: UpdatePersonProfileRequest = {
      displayName: String(formData.get("displayName") ?? "").trim(),
      dateOfBirth: parsedDate,
      heightCm: Number(formData.get("heightCm")),
      trainingGoal: String(formData.get("trainingGoal")) as TrainingGoal,
      maxHeartRateBpm: optionalNumber(
        String(formData.get("maxHeartRateBpm") ?? ""),
      ),
      restingHeartRateBpm: optionalNumber(
        String(formData.get("restingHeartRateBpm") ?? ""),
      ),
      startWeightKg: optionalNumber(
        String(formData.get("startWeightKg") ?? ""),
      ),
      targetWeightKg: optionalNumber(
        String(formData.get("targetWeightKg") ?? ""),
      ),
    };

    const validationError = validateProfileRequest(request);

    if (validationError !== null) {
      setError(validationError);
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
