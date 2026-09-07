import type { Person } from './types'
import { WorkoutHistory } from '../workout/WorkoutHistory'

interface PersonDashboardProps {
  person: Person
  onStartCheckIn: () => void
  onChangePerson: () => void
  onEditProfile: () => void
}

export function PersonDashboard({
  person,
  onStartCheckIn,
  onChangePerson,
  onEditProfile,
}: PersonDashboardProps) {
  return (
    <section className="person-dashboard">
      <header className="app-header">
        <div>
          <div className="eyebrow">DIGITAL FITNESS COACH</div>
          <h1>Hallo {person.displayName}</h1>
        </div>

        <button
          type="button"
          className="change-person"
          onClick={onChangePerson}
        >
          Person wechseln
        </button>
      </header>

      <WorkoutHistory personId={person.id} />

      <div className="dashboard-actions">
        <button
          type="button"
          className="secondary-action"
          onClick={onEditProfile}
        >
          Profil bearbeiten
        </button>

        <button
          type="button"
          className="primary-action"
          onClick={onStartCheckIn}
        >
          Check-in starten
        </button>
      </div>
    </section>
  )
}