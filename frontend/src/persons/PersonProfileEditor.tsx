import { useEffect, useState } from 'react'

import {
  getPersonProfile,
  updatePersonProfile,
} from '../api/persons'
import type {
  Person,
  PersonProfile,
  TrainingGoal,
  UpdatePersonProfileRequest,
} from './types'

interface PersonProfileEditorProps {
  person: Person
  onSaved: (person: Person) => void
  onCancel: () => void
}

function optionalNumber(value: string): number | null {
  if (value.trim() === '') {
    return null
  }

  const number = Number(value)
  return Number.isFinite(number) ? number : null
}

export function PersonProfileEditor({
  person,
  onSaved,
  onCancel,
}: PersonProfileEditorProps) {
  const [profile, setProfile] = useState<PersonProfile | null>(null)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false

    async function loadProfile(): Promise<void> {
      setLoading(true)
      setError(null)

      try {
        const result = await getPersonProfile(person.id)

        if (!cancelled) {
          setProfile(result)
        }
      } catch (loadError) {
        if (!cancelled) {
          setError(
            loadError instanceof Error
              ? loadError.message
              : 'Profil konnte nicht geladen werden',
          )
        }
      } finally {
        if (!cancelled) {
          setLoading(false)
        }
      }
    }

    void loadProfile()

    return () => {
      cancelled = true
    }
  }, [person.id])

  if (loading) {
    return <div className="loading-state">Profil wird geladen …</div>
  }

  if (error !== null && profile === null) {
    return (
      <section className="person-profile-editor">
        <div className="error-message" role="alert">
          {error}
        </div>

        <button
          type="button"
          className="secondary-action"
          onClick={onCancel}
        >
          Zurück
        </button>
      </section>
    )
  }

  if (profile === null) {
    return null
  }

  async function handleSubmit(
    event: React.FormEvent<HTMLFormElement>,
  ): Promise<void> {
    event.preventDefault()

    if (profile === null || saving) {
      return
    }

    const formData = new FormData(event.currentTarget)

    const request: UpdatePersonProfileRequest = {
      displayName: String(formData.get('displayName') ?? ''),
      dateOfBirth: String(formData.get('dateOfBirth') ?? ''),
      heightCm: Number(formData.get('heightCm')),
      trainingGoal: String(
        formData.get('trainingGoal'),
      ) as TrainingGoal,
      maxHeartRateBpm: optionalNumber(
        String(formData.get('maxHeartRateBpm') ?? ''),
      ),
      startWeightKg: optionalNumber(
        String(formData.get('startWeightKg') ?? ''),
      ),
      targetWeightKg: optionalNumber(
        String(formData.get('targetWeightKg') ?? ''),
      ),
    }

    setSaving(true)
    setError(null)

    try {
      const saved = await updatePersonProfile(person.id, request)

      setProfile(saved)

      onSaved({
        id: saved.personId,
        displayName: saved.displayName,
      })
    } catch (saveError) {
      setError(
        saveError instanceof Error
          ? saveError.message
          : 'Profil konnte nicht gespeichert werden',
      )
    } finally {
      setSaving(false)
    }
  }

  return (
    <section className="person-profile-editor">
      <header>
        <div className="eyebrow">PERSONENPROFIL</div>
        <h1>Profil bearbeiten</h1>
      </header>

      <form className="person-profile-form" onSubmit={handleSubmit}>
        <label>
          <span>Name</span>
          <input
            name="displayName"
            type="text"
            defaultValue={profile.displayName}
            required
            maxLength={100}
          />
        </label>

        <label>
          <span>Geburtsdatum</span>
          <input
            name="dateOfBirth"
            type="date"
            defaultValue={profile.dateOfBirth}
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
            defaultValue={profile.heightCm}
            required
          />
        </label>

        <label>
          <span>Trainingsziel</span>
          <select
            name="trainingGoal"
            defaultValue={profile.trainingGoal}
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
            defaultValue={profile.maxHeartRateBpm ?? ''}
            placeholder="optional"
          />
        </label>

        <label>
          <span>Startgewicht in kg</span>
          <input
            name="startWeightKg"
            type="number"
            min="1"
            max="500"
            step="0.1"
            defaultValue={profile.startWeightKg ?? ''}
            placeholder="optional"
          />
        </label>

        <label>
          <span>Zielgewicht in kg</span>
          <input
            name="targetWeightKg"
            type="number"
            min="1"
            max="500"
            step="0.1"
            defaultValue={profile.targetWeightKg ?? ''}
            placeholder="optional"
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

          <button
            type="submit"
            className="primary-action"
            disabled={saving}
          >
            {saving ? 'Wird gespeichert …' : 'Speichern'}
          </button>
        </div>
      </form>
    </section>
  )
}