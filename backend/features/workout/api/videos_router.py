from typing import Annotated

from fastapi import APIRouter, HTTPException, Path, Response, status

from apps.api import wiring
from features.workout.api.contracts.workout_video import (
    WorkoutVideoMutationRequest,
    WorkoutVideoResponse,
    WorkoutVideoSelectionResponse,
    to_workout_video_response,
    to_workout_video_selection_response,
)
from features.workout.service.video_catalog_service import (
    WorkoutVideoNotFoundError,
    WorkoutVideoPathConflictError,
)

router = APIRouter(tags=["Workout Videos"])


VideoId = Annotated[
    str,
    Path(
        title="Video-ID",
        description="Stabile ID eines Videos aus dem Trainingskatalog.",
    ),
]

PersonId = Annotated[
    int,
    Path(
        title="Person-ID",
        description=(
            "ID der Person, für die die verfügbaren Trainingsvideos "
            "personenspezifisch aufgelistet werden."
        ),
        gt=0,
    ),
]


def _not_found(exc: WorkoutVideoNotFoundError) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=str(exc),
    )


@router.get(
    "/api/workout-videos",
    response_model=list[WorkoutVideoResponse],
    response_model_by_alias=True,
    summary="Trainingsvideo-Katalog auflisten",
    description=(
        "Liefert den vollständigen Trainingsvideo-Katalog einschließlich "
        "aktiver und inaktiver Videos. "
        "Der Endpunkt ist insbesondere für die Videoverwaltung vorgesehen. "
        "Inaktive Videos bleiben im Katalog erhalten, damit bestehende "
        "Workout-Historien und Referenzen weiterhin nachvollziehbar bleiben."
    ),
)
async def get_workout_videos() -> list[WorkoutVideoResponse]:
    videos = wiring.video_catalog_service.get_all()
    return [to_workout_video_response(video) for video in videos]


@router.get(
    "/api/persons/{person_id}/workout-videos",
    response_model=list[WorkoutVideoSelectionResponse],
    response_model_by_alias=True,
    summary="Trainingsvideos für eine Person auflisten",
    description=(
        "Liefert ausschließlich aktive Trainingsvideos, die für den Start "
        "eines neuen Workouts ausgewählt werden können. "
        "Die Liste wird personenspezifisch nach bisheriger Verwendung "
        "sortiert: wenig verwendete Videos erscheinen vor häufig "
        "verwendeten Videos. "
        "Zusätzlich werden Informationen zur bisherigen Verwendung, "
        "zur Kennzeichnung noch nie verwendeter Videos und zum zuletzt "
        "verwendeten Video bereitgestellt."
    ),
    responses={
        status.HTTP_200_OK: {
            "description": (
                "Personenspezifisch sortierte Liste der aktuell auswählbaren Trainingsvideos."
            ),
        },
    },
)
async def get_workout_videos_for_person(
    person_id: PersonId,
) -> list[WorkoutVideoSelectionResponse]:
    return [
        to_workout_video_selection_response(item)
        for item in wiring.video_catalog_service.get_for_person(person_id)
    ]


@router.get(
    "/api/workout-videos/{video_id}",
    response_model=WorkoutVideoResponse,
    response_model_by_alias=True,
    summary="Trainingsvideo abrufen",
    description=(
        "Liefert die vollständigen Katalogdaten eines einzelnen "
        "Trainingsvideos anhand seiner stabilen ID. "
        "Dabei können sowohl aktive als auch inaktive Videos abgerufen werden."
    ),
    responses={
        status.HTTP_404_NOT_FOUND: {
            "description": "Das Trainingsvideo wurde nicht gefunden.",
        },
    },
)
async def get_workout_video(
    video_id: VideoId,
) -> WorkoutVideoResponse:
    try:
        video = wiring.video_catalog_service.get(video_id)
    except WorkoutVideoNotFoundError as exc:
        raise _not_found(exc) from exc

    return to_workout_video_response(video)


@router.post(
    "/api/workout-videos",
    response_model=WorkoutVideoResponse,
    response_model_by_alias=True,
    status_code=status.HTTP_201_CREATED,
    summary="Trainingsvideo anlegen",
    description=(
        "Legt einen neuen Eintrag im Trainingsvideo-Katalog an. "
        "Der Dateipfad muss innerhalb des Katalogs eindeutig sein. "
        "Videos können bereits beim Anlegen als aktiv oder inaktiv "
        "gekennzeichnet werden."
    ),
    responses={
        status.HTTP_201_CREATED: {
            "description": "Das Trainingsvideo wurde erfolgreich angelegt.",
        },
        status.HTTP_409_CONFLICT: {
            "description": ("Für den angegebenen Dateipfad existiert bereits ein Trainingsvideo."),
        },
    },
)
async def create_workout_video(
    request: WorkoutVideoMutationRequest,
) -> WorkoutVideoResponse:
    try:
        video = wiring.video_catalog_service.create(
            title=request.title,
            description=request.description,
            file_path=request.file_path,
            duration_seconds=request.duration_seconds,
            active=request.active,
        )
    except WorkoutVideoPathConflictError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc

    return to_workout_video_response(video)


@router.put(
    "/api/workout-videos/{video_id}",
    response_model=WorkoutVideoResponse,
    response_model_by_alias=True,
    summary="Trainingsvideo aktualisieren",
    description=(
        "Aktualisiert die Metadaten eines vorhandenen Trainingsvideos. "
        "Dabei können unter anderem Titel, Beschreibung, Dateipfad, "
        "Dauer und Aktivstatus geändert werden. "
        "Der Dateipfad muss innerhalb des Katalogs eindeutig bleiben."
    ),
    responses={
        status.HTTP_200_OK: {
            "description": "Das Trainingsvideo wurde erfolgreich aktualisiert.",
        },
        status.HTTP_404_NOT_FOUND: {
            "description": "Das Trainingsvideo wurde nicht gefunden.",
        },
        status.HTTP_409_CONFLICT: {
            "description": (
                "Für den angegebenen Dateipfad existiert bereits ein anderes Trainingsvideo."
            ),
        },
    },
)
async def update_workout_video(
    video_id: VideoId,
    request: WorkoutVideoMutationRequest,
) -> WorkoutVideoResponse:
    try:
        video = wiring.video_catalog_service.update(
            video_id,
            title=request.title,
            description=request.description,
            file_path=request.file_path,
            duration_seconds=request.duration_seconds,
            active=request.active,
        )
    except WorkoutVideoNotFoundError as exc:
        raise _not_found(exc) from exc
    except WorkoutVideoPathConflictError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc

    return to_workout_video_response(video)


@router.delete(
    "/api/workout-videos/{video_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Trainingsvideo deaktivieren",
    description=(
        "Deaktiviert ein Trainingsvideo im Katalog. "
        "Der Datensatz wird bewusst nicht physisch gelöscht, damit "
        "bestehende Workouts weiterhin auf das verwendete Video "
        "verweisen können. "
        "Deaktivierte Videos erscheinen nicht mehr in der "
        "Trainingsauswahl, bleiben aber in der Videoverwaltung sichtbar."
    ),
    responses={
        status.HTTP_204_NO_CONTENT: {
            "description": "Das Trainingsvideo wurde erfolgreich deaktiviert.",
        },
        status.HTTP_404_NOT_FOUND: {
            "description": "Das Trainingsvideo wurde nicht gefunden.",
        },
    },
)
async def delete_workout_video(
    video_id: VideoId,
) -> Response:
    try:
        wiring.video_catalog_service.deactivate(video_id)
    except WorkoutVideoNotFoundError as exc:
        raise _not_found(exc) from exc

    return Response(status_code=status.HTTP_204_NO_CONTENT)
