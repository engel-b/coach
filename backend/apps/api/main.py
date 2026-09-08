import logging

from fastapi import FastAPI

from apps.api.routers.devices import router as devices_router
from apps.api.routers.health import router as health_router
from apps.api.routers.telemetry import router as telemetry_router
from apps.api.routers.training import router as training_router
from apps.api.routers.workout_videos import router as workout_videos_router
from apps.api.routers.workouts import router as workouts_router
from features.check_in.api.router import router as check_ins_router
from features.person.api.router import router as persons_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)


OPENAPI_TAGS = [
    {
        "name": "Persons",
        "description": (
            "Personen anlegen, auflisten und ihre Stammdaten sowie Trainingsprofile verwalten."
        ),
    },
    {
        "name": "Check-ins",
        "description": (
            "Tagesform und verfügbare Trainingszeit erfassen und "
            "den letzten Check-in einer Person abrufen."
        ),
    },
    {
        "name": "Training",
        "description": (
            "Individuelle Trainingsempfehlungen auf Basis des "
            "Personenprofils und des letzten Check-ins erstellen."
        ),
    },
    {
        "name": "Workouts",
        "description": (
            "Trainings starten, Zwischenstände speichern, beenden "
            "und die Trainingshistorie sowie Zusammenfassungen abrufen."
        ),
    },
    {
        "name": "Workout Videos",
        "description": ("Verfügbare Trainingsvideos und ihre Metadaten abrufen."),
    },
    {
        "name": "Devices",
        "description": (
            "Aktuellen Verbindungsstatus und Telemetriedaten der bekannten Trainingsgeräte abrufen."
        ),
    },
    {
        "name": "System",
        "description": "Technische Endpunkte zur Zustandsprüfung des Backends.",
    },
]


app = FastAPI(
    title="Health Coach API",
    description=(
        "Die lokale HTTP-API des Health Coach. Sie verwaltet Personen, "
        "Check-ins, Trainingsempfehlungen, Workouts und Trainingsvideos. "
        "Gerätetelemetrie wird zusätzlich über WebSocket-Verbindungen "
        "übertragen.\n\n"
        "Die API verwendet JSON mit camelCase-Feldnamen. Personen werden "
        "über stabile numerische IDs identifiziert. Es handelt sich um "
        "eine lokale Anwendung ohne Benutzeranmeldung."
    ),
    version="0.1.0",
    openapi_tags=OPENAPI_TAGS,
)

app.include_router(health_router)
app.include_router(devices_router)
app.include_router(telemetry_router)
app.include_router(persons_router)
app.include_router(check_ins_router)
app.include_router(training_router)
app.include_router(workouts_router)
app.include_router(workout_videos_router)
