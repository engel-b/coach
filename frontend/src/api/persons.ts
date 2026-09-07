import type {
  Person,
  PersonProfile,
  UpdatePersonProfileRequest,
} from '../persons/types'

export async function getPersons(): Promise<Person[]> {
  const response = await fetch('/api/persons')

  if (!response.ok) {
    throw new Error(`Could not load persons: HTTP ${response.status}`)
  }

  return (await response.json()) as Person[]
}

export async function getPersonProfile(
  personId: number,
): Promise<PersonProfile> {
  const response = await fetch(`/api/persons/${personId}/profile`)

  if (!response.ok) {
    throw new Error(`Could not load person profile: HTTP ${response.status}`)
  }

  return (await response.json()) as PersonProfile
}

export async function updatePersonProfile(
  personId: number,
  request: UpdatePersonProfileRequest,
): Promise<PersonProfile> {
  const response = await fetch(`/api/persons/${personId}/profile`, {
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(request),
  })

  if (!response.ok) {
    throw new Error(`Could not update person profile: HTTP ${response.status}`)
  }

  return (await response.json()) as PersonProfile
}
