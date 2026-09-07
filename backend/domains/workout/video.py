from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class WorkoutVideo:
    """
    Fachliche Beschreibung eines verfügbaren Trainingsvideos.

    Die Videodatei selbst liegt im Dateisystem.
    Die Datenbank speichert nur Metadaten und den relativen Pfad.
    """

    id: str
    title: str
    file_path: str
    created_at: datetime
    description: str | None = None
    duration_seconds: float | None = None
    active: bool = True