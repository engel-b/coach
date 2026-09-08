from unittest.mock import Mock

from features.person.domain.person import Person
from features.person.service.person_service import PersonService


def test_persons_are_returned_from_repository() -> None:
    repository = Mock()
    repository.get_all.return_value = [
        Person(id=1, display_name="Person 1"),
        Person(id=2, display_name="Person 2"),
    ]

    service = PersonService(repository=repository)

    assert service.get_persons() == repository.get_all.return_value
    repository.get_all.assert_called_once_with()


def test_person_can_be_found_by_id() -> None:
    repository = Mock()
    repository.get.return_value = Person(
        id=2,
        display_name="Person 2",
    )

    service = PersonService(repository=repository)

    person = service.get_person(2)

    assert person == Person(id=2, display_name="Person 2")
    repository.get.assert_called_once_with(2)


def test_unknown_person_returns_none() -> None:
    repository = Mock()
    repository.get.return_value = None

    service = PersonService(repository=repository)

    assert service.get_person(999) is None
    repository.get.assert_called_once_with(999)
