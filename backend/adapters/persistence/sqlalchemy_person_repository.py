from collections.abc import Callable

from sqlalchemy import select
from sqlalchemy.orm import Session

from adapters.persistence.database import create_session
from adapters.persistence.person_model import PersonModel
from domains.person.person import Person
from domains.person.person_repository import PersonRepository


class SqlAlchemyPersonRepository(PersonRepository):
    def __init__(
        self,
        session_factory: Callable[[], Session] = create_session,
    ) -> None:
        self._session_factory = session_factory

    def get_all(self) -> list[Person]:
        with self._session_factory() as session:
            statement = select(PersonModel).order_by(PersonModel.id)
            models = session.scalars(statement).all()

            return [self._to_domain(model) for model in models]

    def get(self, person_id: int) -> Person | None:
        with self._session_factory() as session:
            model = session.get(PersonModel, person_id)

            if model is None:
                return None

            return self._to_domain(model)

    def save(self, person: Person) -> Person:
        with self._session_factory() as session:
            model = session.get(PersonModel, person.id)

            if model is None:
                model = PersonModel(
                    id=person.id,
                    display_name=person.display_name,
                )
                session.add(model)
            else:
                model.display_name = person.display_name

            session.commit()

        return person

    @staticmethod
    def _to_domain(model: PersonModel) -> Person:
        return Person(
            id=model.id,
            display_name=model.display_name,
        )