import type { Person } from '../persons/types'

/**
 * Lädt die verfügbaren Personen vom Backend.
 */
export async function getPersons(): Promise<Person[]> {
  const response = await fetch('/api/persons')

  if (!response.ok) {
    throw new Error(
      `Could not load persons: HTTP ${response.status}`,
    )
  }

  return (await response.json()) as Person[]
}

