from collections.abc import Callable

from sqlalchemy.orm import Session

from adapters.persistence.database import create_session
from features.person.domain.profile import PersonProfile, TrainingGoal
from features.person.domain.profile_repository import PersonProfileRepository
from features.person.persistence.person_model import PersonProfileModel


class SqlAlchemyPersonProfileRepository(PersonProfileRepository):
    def __init__(
        self,
        session_factory: Callable[[], Session] = create_session,
    ) -> None:
        self._session_factory = session_factory

    def get(self, person_id: int) -> PersonProfile | None:
        with self._session_factory() as session:
            model = session.get(PersonProfileModel, person_id)

            if model is None:
                return None

            return self._to_domain(model)

    def save(self, profile: PersonProfile) -> PersonProfile:
        with self._session_factory() as session:
            model = session.get(PersonProfileModel, profile.person_id)

            if model is None:
                model = PersonProfileModel(
                    person_id=profile.person_id,
                    date_of_birth=profile.date_of_birth,
                    height_cm=profile.height_cm,
                    training_goal=profile.training_goal.value,
                    max_heart_rate_bpm=profile.max_heart_rate_bpm,
                    start_weight_kg=profile.start_weight_kg,
                    target_weight_kg=profile.target_weight_kg,
                )
                session.add(model)
            else:
                model.date_of_birth = profile.date_of_birth
                model.height_cm = profile.height_cm
                model.training_goal = profile.training_goal.value
                model.max_heart_rate_bpm = profile.max_heart_rate_bpm
                model.start_weight_kg = profile.start_weight_kg
                model.target_weight_kg = profile.target_weight_kg

            session.commit()

        return profile

    @staticmethod
    def _to_domain(model: PersonProfileModel) -> PersonProfile:
        return PersonProfile(
            person_id=model.person_id,
            date_of_birth=model.date_of_birth,
            height_cm=model.height_cm,
            training_goal=TrainingGoal(model.training_goal),
            max_heart_rate_bpm=model.max_heart_rate_bpm,
            start_weight_kg=model.start_weight_kg,
            target_weight_kg=model.target_weight_kg,
        )
