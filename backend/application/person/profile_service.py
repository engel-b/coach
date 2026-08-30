from datetime import date

from domains.person.profile import PersonProfile, TrainingGoal


class PersonProfileService:
    """
    Liefert momentan statisch konfigurierte Personenprofile.

    Später wird die Datenquelle durch Persistenz ersetzt.
    """

    def __init__(self) -> None:
        self._profiles: dict[int, PersonProfile] = {
            1: PersonProfile(
                person_id=1,
                date_of_birth=date(1980, 1, 1),
                height_cm=180,
                training_goal=TrainingGoal.GENERAL_FITNESS,
            ),
            2: PersonProfile(
                person_id=2,
                date_of_birth=date(1980, 1, 1),
                height_cm=180,
                training_goal=TrainingGoal.GENERAL_FITNESS,
            ),
            3: PersonProfile(
                person_id=3,
                date_of_birth=date(1980, 1, 1),
                height_cm=180,
                training_goal=TrainingGoal.GENERAL_FITNESS,
            ),
            4: PersonProfile(
                person_id=4,
                date_of_birth=date(1980, 1, 1),
                height_cm=180,
                training_goal=TrainingGoal.GENERAL_FITNESS,
            ),
        }

    def get_profile(
        self,
        person_id: int,
    ) -> PersonProfile | None:
        return self._profiles.get(person_id)
