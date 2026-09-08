import { useEffect } from "react";

import type { Person } from "./types";

interface PersonSelectionProps {
  persons: Person[];
  onSelect: (person: Person) => void;
  onCreate: () => void;
}

/**
 * Auswahl der aktiven Person.
 *
 * Bedienung:
 *
 *   Maus:
 *       Karte anklicken
 *
 *   Tastatur:
 *       Taste 1 bis 4
 *
 * Ein späterer USB-Nummernblock sendet dieselben KeyboardEvents.
 * Deshalb funktioniert er ohne Änderung dieser Komponente.
 */
export function PersonSelection({
  persons,
  onSelect,
  onCreate,
}: PersonSelectionProps) {
  useEffect(() => {
    function handleKeyDown(event: KeyboardEvent): void {
      /*
       * "1" wird Index 0,
       * "2" wird Index 1 usw.
       */
      const number = Number(event.key);

      if (Number.isInteger(number) && number >= 1 && number <= persons.length) {
        const person = persons[number - 1];

        if (person !== undefined) {
          onSelect(person);
        }
      }
    }

    window.addEventListener("keydown", handleKeyDown);

    return () => {
      window.removeEventListener("keydown", handleKeyDown);
    };
  }, [persons, onSelect]);

  return (
    <section className="person-selection">
      <div className="selection-heading">
        <div className="eyebrow">DIGITAL FITNESS COACH</div>

        <h1>Wer trainiert heute?</h1>

        <p>Wähle eine Person oder drücke die entsprechende Zifferntaste.</p>
      </div>

      <div className="person-grid">
        {persons.map((person, index) => (
          <button
            className="person-card"
            key={person.id}
            type="button"
            onClick={() => onSelect(person)}
          >
            <span className="person-number">{index + 1}</span>

            <span className="person-name">{person.displayName}</span>
          </button>
        ))}
      </div>
      <div className="person-selection-actions">
        <button type="button" className="secondary-action" onClick={onCreate}>
          + Person hinzufügen
        </button>
      </div>
    </section>
  );
}
