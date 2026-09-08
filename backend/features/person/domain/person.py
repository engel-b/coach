from dataclasses import dataclass


@dataclass(frozen=True)
class Person:
    """
    Eine Person, die den Health Coach benutzt.

    Wichtig:
    Person ist zunächst KEIN Benutzerkonto.

    Es gibt:
    - kein Passwort
    - keine Anmeldung
    - keine Rollen/Berechtigungen

    Die Person identifiziert lediglich, wem Check-ins,
    Trainingseinheiten und Gesundheitsdaten gehören.

    frozen=True macht das Objekt unveränderlich.
    """

    id: int
    display_name: str
