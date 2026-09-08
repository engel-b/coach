from datetime import date

from features.person.domain.profile import PersonProfile


def calculate_age(
    date_of_birth: date,
    on_date: date,
) -> int:
    """
    Berechnet das Alter an einem bestimmten Datum.

    Wir übergeben das Datum explizit, statt date.today()
    innerhalb der Funktion aufzurufen. Dadurch ist die
    Funktion deterministisch und sehr einfach testbar.
    """

    years = on_date.year - date_of_birth.year

    birthday_has_passed = (
        on_date.month,
        on_date.day,
    ) >= (
        date_of_birth.month,
        date_of_birth.day,
    )

    if not birthday_has_passed:
        years -= 1

    return years


def estimate_max_heart_rate(age: int) -> int:
    """
    Grobe altersbasierte Schätzung der maximalen Herzfrequenz.

    Diese Schätzung dient nur als Ausgangspunkt und ersetzt
    keine individuell bestimmte HFmax.
    """

    return round(208 - 0.7 * age)


def get_max_heart_rate(
    profile: PersonProfile,
    on_date: date,
) -> int:
    """
    Bevorzugt eine bekannte individuelle HFmax.

    Nur wenn keine vorhanden ist, wird sie aus dem Alter
    geschätzt.
    """

    if profile.max_heart_rate_bpm is not None:
        return profile.max_heart_rate_bpm

    age = calculate_age(
        profile.date_of_birth,
        on_date,
    )

    return estimate_max_heart_rate(age)
