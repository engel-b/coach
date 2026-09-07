from application.person.service import PersonService


def test_four_persons_are_available() -> None:
    service = PersonService()

    persons = service.get_persons()

    assert len(persons) == 4


def test_person_can_be_found_by_id() -> None:
    service = PersonService()

    person = service.get_person(2)

    assert person is not None
    assert person.id == 2
    assert person.display_name == "Steffi"


def test_unknown_person_returns_none() -> None:
    service = PersonService()

    person = service.get_person(999)

    assert person is None
