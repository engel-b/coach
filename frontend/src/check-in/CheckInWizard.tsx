import { useEffect, useState } from 'react'

import { createCheckIn } from '../api/check-ins'
import type { Person } from '../persons/types'
import { checkInQuestions } from './questions'
import type {
  CheckIn,
  CheckInRequest,
} from './types'


interface CheckInWizardProps {
  person: Person
  onComplete: (checkIn: CheckIn) => void
  onCancel: () => void
}


type Answers = Partial<CheckInRequest>


export function CheckInWizard({
  person,
  onComplete,
  onCancel,
}: CheckInWizardProps) {
  const [step, setStep] = useState(0)
  const [answers, setAnswers] = useState<Answers>({})
  const [selectedIndex, setSelectedIndex] =
    useState<number | null>(null)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const question = checkInQuestions[step]

  async function completeCheckIn(
    finalAnswers: Answers,
  ): Promise<void> {
    /*
     * Zu diesem Zeitpunkt müssen alle fünf Antworten vorhanden sein.
     *
     * Die expliziten Prüfungen schützen uns trotzdem davor,
     * versehentlich einen unvollständigen Check-in abzuschicken.
     */
    if (
      finalAnswers.energy === undefined ||
      finalAnswers.recovery === undefined ||
      finalAnswers.muscleSoreness === undefined ||
      finalAnswers.stress === undefined ||
      finalAnswers.availableTrainingMinutes === undefined
    ) {
      setError('Der Check-in ist unvollständig.')
      return
    }

    const request: CheckInRequest = {
      energy: finalAnswers.energy,
      recovery: finalAnswers.recovery,
      muscleSoreness: finalAnswers.muscleSoreness,
      stress: finalAnswers.stress,
      availableTrainingMinutes:
        finalAnswers.availableTrainingMinutes,
    }

    try {
      setSaving(true)
      setError(null)

      const result = await createCheckIn(
        person.id,
        request,
      )

      onComplete(result)
    } catch (saveError) {
      const message =
        saveError instanceof Error
          ? saveError.message
          : 'Unknown error'

      setError(message)
      setSaving(false)
    }
  }

  function selectOption(index: number): void {
    if (question === undefined) {
      return
    }

    if (index < 0 || index >= question.options.length) {
      return
    }

    setSelectedIndex(index)
  }

  function goBack(): void {
    if (saving) {
      return
    }

    if (step === 0) {
      onCancel()
      return
    }

    setStep((current) => current - 1)
    setSelectedIndex(null)
    setError(null)
  }

  function confirmSelection(): void {
    if (
      question === undefined ||
      selectedIndex === null ||
      saving
    ) {
      return
    }

    const option = question.options[selectedIndex]

    if (option === undefined) {
      return
    }

    const newAnswers: Answers = {
      ...answers,
      [question.field]: option.value,
    }

    setAnswers(newAnswers)

    const isLastQuestion =
      step === checkInQuestions.length - 1

    if (isLastQuestion) {
      void completeCheckIn(newAnswers)
      return
    }

    setStep((current) => current + 1)
    setSelectedIndex(null)
    setError(null)
  }

  useEffect(() => {
    function handleKeyDown(event: KeyboardEvent): void {
      if (saving || question === undefined) {
        return
      }

      /*
       * Zifferntasten wählen eine Option.
       *
       * Das funktioniert sowohl mit der normalen Tastatur
       * als später auch mit einem USB-Nummernblock.
       */
      const number = Number(event.key)

      if (
        Number.isInteger(number) &&
        number >= 1 &&
        number <= question.options.length
      ) {
        selectOption(number - 1)
        return
      }

      if (event.key === 'Enter') {
        confirmSelection()
        return
      }

      if (event.key === 'Escape') {
        goBack()
      }
    }

    window.addEventListener('keydown', handleKeyDown)

    return () => {
      window.removeEventListener(
        'keydown',
        handleKeyDown,
      )
    }
  })

  if (question === undefined) {
    return null
  }

  return (
    <section className="check-in">
      <header className="check-in-header">
        <div className="eyebrow">
          CHECK-IN · {person.displayName}
        </div>

        <div className="check-in-progress">
          Frage {step + 1} von {checkInQuestions.length}
        </div>
      </header>

      <div className="check-in-content">
        <h1>{question.title}</h1>

        <p className="check-in-description">
          {question.description}
        </p>

        <div className="check-in-options">
          {question.options.map((option, index) => {
            const selected = selectedIndex === index

            return (
              <button
                key={option.value}
                type="button"
                className={
                  selected
                    ? 'check-in-option selected'
                    : 'check-in-option'
                }
                onClick={() => selectOption(index)}
                disabled={saving}
              >
                <span className="option-key">
                  {index + 1}
                </span>

                <span className="option-label">
                  {option.label}
                </span>
              </button>
            )
          })}
        </div>

        {error !== null && (
          <div className="error-message">
            {error}
          </div>
        )}
      </div>

      <footer className="check-in-footer">
        <span>
          Esc · Zurück
        </span>

        <span>
          {saving
            ? 'Check-in wird gespeichert …'
            : 'Enter · Weiter'}
        </span>
      </footer>
    </section>
  )
}

