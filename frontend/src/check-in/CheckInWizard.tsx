import { useEffect, useRef, useState } from "react";

import { createCheckIn, getLatestCheckIn } from "../api/check-ins";
import type { Person } from "../persons/types";
import { checkInQuestions } from "./questions";
import type { CheckIn, CheckInRequest } from "./types";

interface CheckInWizardProps {
  person: Person;
  onComplete: (checkIn: CheckIn) => void;
  onCancel: () => void;
}

type Answers = Partial<CheckInRequest>;

type HealthData = {
  weight: string;
  sleepHours: string;
  sleepMinutes: string;
  steps: string;
  restingHeartRate: string;
};

const EMPTY_HEALTH_DATA: HealthData = {
  weight: "",
  sleepHours: "",
  sleepMinutes: "",
  steps: "",
  restingHeartRate: "",
};

function formatWeight(value: number): string {
  return value.toFixed(1).replace(".", ",");
}

function parseOptionalNumber(value: string): number | null {
  const normalized = value.trim().replace(",", ".");

  if (normalized === "") {
    return null;
  }

  const parsed = Number(normalized);
  return Number.isFinite(parsed) ? parsed : null;
}

function parseOptionalInteger(value: string): number | null {
  const normalized = value.trim();

  if (normalized === "") {
    return null;
  }

  if (!/^\d+$/.test(normalized)) {
    return null;
  }

  const parsed = Number(normalized);
  return Number.isSafeInteger(parsed) ? parsed : null;
}

function healthDataFromCheckIn(checkIn: CheckIn | null): HealthData {
  if (checkIn === null) {
    return { ...EMPTY_HEALTH_DATA };
  }

  const sleep = checkIn.sleepHours;
  const totalMinutes =
    sleep === null || sleep === undefined ? null : Math.round(sleep * 60);

  return {
    weight:
      checkIn.currentWeightKg === null || checkIn.currentWeightKg === undefined
        ? ""
        : formatWeight(checkIn.currentWeightKg),
    sleepHours:
      totalMinutes === null ? "" : String(Math.floor(totalMinutes / 60)),
    sleepMinutes: totalMinutes === null ? "" : String(totalMinutes % 60),
    steps:
      checkIn.steps === null || checkIn.steps === undefined
        ? ""
        : String(checkIn.steps),
    // Ruhepuls wird absichtlich nicht aus dem letzten Check-in vorbelegt.
    // Jede Baseline-Messung soll eine heute tatsaechlich erfasste Messung sein.
    restingHeartRate: "",
  };
}

function clamp(value: number, min: number, max: number): number {
  return Math.min(max, Math.max(min, value));
}

interface NumberControlProps {
  id: string;
  label: string;
  value: string;
  onChange: (value: string) => void;
  step: number;
  min: number;
  max: number;
  unit: string;
  placeholder?: string;
  decimals?: number;
  disabled?: boolean;
}

function NumberControl({
  id,
  label,
  value,
  onChange,
  step,
  min,
  max,
  unit,
  placeholder,
  decimals = 0,
  disabled = false,
}: NumberControlProps) {
  const inputRef = useRef<HTMLInputElement>(null);

  function changeBy(direction: number): void {
    const current = parseOptionalNumber(value);
    const base = current ?? min;
    const next = clamp(
      Math.round((base + direction * step) * 1000) / 1000,
      min,
      max,
    );

    onChange(decimals === 1 ? formatWeight(next) : String(Math.round(next)));
  }

  useEffect(() => {
    const input = inputRef.current;

    if (input === null) {
      return;
    }

    function handleWheel(event: WheelEvent): void {
      if (disabled || document.activeElement !== input) {
        return;
      }

      event.preventDefault();
      changeBy(event.deltaY < 0 ? 1 : -1);
    }

    // passive: false ist nötig, damit das Mausrad beim Bearbeiten
    // nicht gleichzeitig die gesamte Seite scrollt.
    input.addEventListener("wheel", handleWheel, { passive: false });

    return () => {
      input.removeEventListener("wheel", handleWheel);
    };
  });

  return (
    <div className="check-in-number-control">
      <label htmlFor={id}>{label}</label>

      <div className="check-in-number-row">
        <button
          type="button"
          className="secondary-button"
          onClick={() => changeBy(-1)}
          disabled={disabled}
          aria-label={`${label} verringern`}
        >
          −
        </button>

        <input
          ref={inputRef}
          id={id}
          type="text"
          inputMode={decimals === 1 ? "decimal" : "numeric"}
          value={value}
          onChange={(event) => onChange(event.target.value)}
          onKeyDown={(event) => {
            if (event.key === "ArrowUp") {
              event.preventDefault();
              changeBy(1);
            } else if (event.key === "ArrowDown") {
              event.preventDefault();
              changeBy(-1);
            }
          }}
          placeholder={placeholder}
          disabled={disabled}
          autoComplete="off"
        />

        <span className="check-in-number-unit">{unit}</span>

        <button
          type="button"
          className="secondary-button"
          onClick={() => changeBy(1)}
          disabled={disabled}
          aria-label={`${label} erhöhen`}
        >
          +
        </button>
      </div>
    </div>
  );
}

export function CheckInWizard({
  person,
  onComplete,
  onCancel,
}: CheckInWizardProps) {
  const [step, setStep] = useState(0);
  const [answers, setAnswers] = useState<Answers>({});
  const [showHealthData, setShowHealthData] = useState(false);
  const [healthData, setHealthData] = useState<HealthData>({
    ...EMPTY_HEALTH_DATA,
  });
  const [loadingPrevious, setLoadingPrevious] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const savingRef = useRef(false);

  const question = checkInQuestions[step];

  useEffect(() => {
    let cancelled = false;

    async function loadPrevious(): Promise<void> {
      setLoadingPrevious(true);

      try {
        const latest = await getLatestCheckIn(person.id);

        if (!cancelled) {
          setHealthData(healthDataFromCheckIn(latest));
        }
      } catch {
        // Ein fehlender vorheriger Check-in darf den neuen nicht blockieren.
        if (!cancelled) {
          setHealthData({ ...EMPTY_HEALTH_DATA });
        }
      } finally {
        if (!cancelled) {
          setLoadingPrevious(false);
        }
      }
    }

    void loadPrevious();

    return () => {
      cancelled = true;
    };
  }, [person.id]);

  function updateHealthData(field: keyof HealthData, value: string): void {
    setHealthData((current) => ({
      ...current,
      [field]: value,
    }));
    setError(null);
  }

  function validateHealthData(): {
    currentWeightKg: number | null;
    sleepHours: number | null;
    steps: number | null;
    restingHeartRateBpm: number | null;
  } | null {
    const weight = parseOptionalNumber(healthData.weight);
    const weightEntered = healthData.weight.trim() !== "";

    if (weightEntered && (weight === null || weight <= 0 || weight > 500)) {
      setError("Bitte gib ein gültiges Gewicht zwischen 0 und 500 kg ein.");
      return null;
    }

    const hours = parseOptionalInteger(healthData.sleepHours);
    const minutes = parseOptionalInteger(healthData.sleepMinutes);
    const sleepEntered =
      healthData.sleepHours.trim() !== "" ||
      healthData.sleepMinutes.trim() !== "";

    if (
      sleepEntered &&
      ((healthData.sleepHours.trim() !== "" && hours === null) ||
        (healthData.sleepMinutes.trim() !== "" && minutes === null))
    ) {
      setError("Bitte gib gültige Stunden und Minuten ein.");
      return null;
    }

    const sleepHours = sleepEntered ? (hours ?? 0) + (minutes ?? 0) / 60 : null;

    if (
      sleepEntered &&
      ((hours ?? 0) > 24 ||
        (minutes ?? 0) > 59 ||
        sleepHours === null ||
        sleepHours > 24)
    ) {
      setError("Die Schlafdauer muss zwischen 0 und 24 Stunden liegen.");
      return null;
    }

    const steps = parseOptionalInteger(healthData.steps);

    if (healthData.steps.trim() !== "" && steps === null) {
      setError("Bitte gib eine gültige, nicht negative Schrittzahl ein.");
      return null;
    }

    const restingHeartRate = parseOptionalInteger(healthData.restingHeartRate);

    if (
      healthData.restingHeartRate.trim() !== "" &&
      (restingHeartRate === null ||
        restingHeartRate < 35 ||
        restingHeartRate > 120)
    ) {
      setError("Bitte gib einen Ruhepuls zwischen 35 und 120 bpm ein.");
      return null;
    }

    return {
      currentWeightKg: weight === null ? null : Math.round(weight * 10) / 10,
      sleepHours,
      steps,
      restingHeartRateBpm: restingHeartRate,
    };
  }

  async function completeCheckIn(): Promise<void> {
    if (savingRef.current) {
      return;
    }

    if (
      answers.energy === undefined ||
      answers.recovery === undefined ||
      answers.muscleSoreness === undefined ||
      answers.stress === undefined ||
      answers.availableTrainingMinutes === undefined
    ) {
      setError("Der Check-in ist unvollständig.");
      return;
    }

    const health = validateHealthData();

    if (health === null) {
      return;
    }

    const request: CheckInRequest = {
      energy: answers.energy,
      recovery: answers.recovery,
      muscleSoreness: answers.muscleSoreness,
      stress: answers.stress,
      availableTrainingMinutes: answers.availableTrainingMinutes,
      ...health,
    };

    savingRef.current = true;
    setSaving(true);
    setError(null);

    try {
      const result = await createCheckIn(person.id, request);
      onComplete(result);
    } catch (saveError) {
      setError(
        saveError instanceof Error
          ? saveError.message
          : "Der Check-in konnte nicht gespeichert werden.",
      );
      savingRef.current = false;
      setSaving(false);
    }
  }

  function selectOption(index: number): void {
    if (question === undefined || savingRef.current) {
      return;
    }

    const option = question.options[index];

    if (option === undefined) {
      return;
    }

    const newAnswers: Answers = {
      ...answers,
      [question.field]: option.value,
    };

    setAnswers(newAnswers);
    setError(null);

    if (step === checkInQuestions.length - 1) {
      setShowHealthData(true);
      return;
    }

    setStep((current) => current + 1);
  }

  function goBack(): void {
    if (savingRef.current) {
      return;
    }

    if (showHealthData) {
      setShowHealthData(false);
      setError(null);
      return;
    }

    if (step === 0) {
      onCancel();
      return;
    }

    setStep((current) => current - 1);
    setError(null);
  }

  useEffect(() => {
    function handleKeyDown(event: KeyboardEvent): void {
      if (savingRef.current) {
        return;
      }

      if (event.key === "Escape") {
        event.preventDefault();
        goBack();
        return;
      }

      if (showHealthData || question === undefined) {
        return;
      }

      const target = event.target;

      if (
        target instanceof HTMLElement &&
        target.closest("input, textarea, select")
      ) {
        return;
      }

      const number = Number(event.key);

      if (
        event.key !== "" &&
        Number.isInteger(number) &&
        number >= 1 &&
        number <= question.options.length
      ) {
        event.preventDefault();
        selectOption(number - 1);
      }
    }

    window.addEventListener("keydown", handleKeyDown);

    return () => {
      window.removeEventListener("keydown", handleKeyDown);
    };
  });

  if (showHealthData) {
    return (
      <section className="check-in">
        <header className="check-in-header">
          <div className="eyebrow">CHECK-IN · {person.displayName}</div>
          <div className="check-in-progress">Tagesdaten</div>
        </header>

        <form
          className="check-in-content"
          noValidate
          onSubmit={(event) => {
            event.preventDefault();
            void completeCheckIn();
          }}
        >
          <h1>Zusätzliche Tagesdaten</h1>

          <p className="check-in-description">
            Die Werte des letzten Check-ins sind vorbelegt. Du kannst sie ändern
            oder leer lassen, wenn du sie heute nicht erfasst hast.
          </p>

          {loadingPrevious && (
            <p className="check-in-description">
              Letzte Werte werden geladen …
            </p>
          )}

          <div className="check-in-health-fields">
            <NumberControl
              id="check-in-weight"
              label="Aktuelles Gewicht"
              value={healthData.weight}
              onChange={(value) => updateHealthData("weight", value)}
              step={0.1}
              min={0.1}
              max={500}
              decimals={1}
              unit="kg"
              placeholder="82,4"
              disabled={saving || loadingPrevious}
            />

            <div className="check-in-sleep-fields">
              <NumberControl
                id="check-in-sleep-hours"
                label="Schlaf – Stunden"
                value={healthData.sleepHours}
                onChange={(value) => updateHealthData("sleepHours", value)}
                step={1}
                min={0}
                max={24}
                unit="Std."
                placeholder="7"
                disabled={saving || loadingPrevious}
              />

              <NumberControl
                id="check-in-sleep-minutes"
                label="Schlaf – Minuten"
                value={healthData.sleepMinutes}
                onChange={(value) => updateHealthData("sleepMinutes", value)}
                step={5}
                min={0}
                max={59}
                unit="Min."
                placeholder="30"
                disabled={saving || loadingPrevious}
              />
            </div>

            <NumberControl
              id="check-in-resting-heart-rate"
              label="Ruhepuls (heute gemessen)"
              value={healthData.restingHeartRate}
              onChange={(value) => updateHealthData("restingHeartRate", value)}
              step={1}
              min={35}
              max={120}
              unit="bpm"
              placeholder="72"
              disabled={saving || loadingPrevious}
            />

            <p className="check-in-description">
              Nur eintragen, wenn du den Wert heute tatsächlich in Ruhe gemessen
              hast. Mehrere Messungen können später eine stabilere persönliche
              Baseline bilden.
            </p>

            <NumberControl
              id="check-in-steps"
              label="Schritte"
              value={healthData.steps}
              onChange={(value) => updateHealthData("steps", value)}
              step={100}
              min={0}
              max={1000000}
              unit="Schritte"
              placeholder="8450"
              disabled={saving || loadingPrevious}
            />
          </div>

          {error !== null && (
            <div className="error-message" role="alert">
              {error}
            </div>
          )}

          <footer className="check-in-footer">
            <button
              type="button"
              className="secondary-button"
              onClick={goBack}
              disabled={saving}
            >
              Zurück
            </button>

            <button
              type="submit"
              className="primary-button"
              disabled={saving || loadingPrevious}
            >
              {saving ? "Wird gespeichert …" : "Check-in speichern"}
            </button>
          </footer>
        </form>
      </section>
    );
  }

  if (question === undefined) {
    return null;
  }

  return (
    <section className="check-in">
      <header className="check-in-header">
        <div className="eyebrow">CHECK-IN · {person.displayName}</div>

        <div className="check-in-progress">
          Frage {step + 1} von {checkInQuestions.length}
        </div>
      </header>

      <div className="check-in-content">
        <h1>{question.title}</h1>

        <p className="check-in-description">{question.description}</p>

        <div className="check-in-options">
          {question.options.map((option, index) => {
            const selected = answers[question.field] === option.value;

            return (
              <button
                key={option.value}
                type="button"
                className={
                  selected ? "check-in-option selected" : "check-in-option"
                }
                onClick={() => selectOption(index)}
                disabled={saving}
              >
                <span className="option-key">{index + 1}</span>
                <span className="option-label">{option.label}</span>
              </button>
            );
          })}
        </div>

        {error !== null && (
          <div className="error-message" role="alert">
            {error}
          </div>
        )}
      </div>

      <footer className="check-in-footer">
        <button
          type="button"
          className="secondary-button"
          onClick={goBack}
          disabled={saving}
        >
          {step === 0 ? "Abbrechen" : "Zurück"}
        </button>

        <span>Antwort anklicken, um fortzufahren</span>
      </footer>
    </section>
  );
}
