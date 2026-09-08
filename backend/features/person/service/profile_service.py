from features.person.domain.profile import PersonProfile
from features.person.domain.profile_repository import PersonProfileRepository


class PersonProfileService:
    """
    Application Service für die trainingsrelevanten Personenprofile.
    """

    def __init__(self, repository: PersonProfileRepository) -> None:
        self._repository = repository

    def get_profile(
        self,
        person_id: int,
    ) -> PersonProfile | None:
        return self._repository.get(person_id)
