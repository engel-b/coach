import logging
from datetime import UTC, datetime

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import ValidationError

from adapters.persistence.sqlalchemy_check_in_repository import (
    SqlAlchemyCheckInRepository,
)
from adapters.persistence.sqlalchemy_workout_repository import (
    SqlAlchemyWorkoutRepository,
)
from application.check_in.service import (
    CheckInService,
    InvalidCheckInError,
)
from application.person.profile_service import PersonProfileService
from application.person.service import PersonService
from application.telemetry.broadcaster import TelemetryBroadcaster
from application.telemetry.service import TelemetryService
from application.workout.service import (
    InvalidWorkoutDurationError,
    WorkoutAlreadyFinishedError,
    WorkoutNotFoundError,
    WorkoutService,
)
from contracts.check_in import CheckInRequest, CheckInResponse
from contracts.device import DeviceResponse
from contracts.person import PersonResponse
from contracts.telemetry import TelemetryMessage
from contracts.training import (
    TrainingRecommendationResponse,
    WorkoutPhaseResponse,
)
from contracts.workout import (
    FinishWorkoutRequest,
    WorkoutCheckpointRequest,
    WorkoutResponse,
    WorkoutSummaryResponse,
)
from contracts.workout_mapper import to_workout_response, to_workout_summary_response
from domains.training.heart_rate import get_max_heart_rate
from domains.training.recommendation import TrainingRecommendation
from domains.training.recommendation_engine import TrainingRecommendationEngine

from adapters.persistence.sqlalchemy_workout_video_repository import (SqlAlchemyWorkoutVideoRepository)
from application.workout.video_catalog_service import (VideoCatalogService, WorkoutVideoNotFoundError)
from contracts.workout_video import (WorkoutVideoResponse, to_workout_video_response)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)

logger = logging.getLogger(__name__)


app = FastAPI(
    title="Health Coach API",
    version="0.1.0",
)


# Vorerst eine Instanz für den gesamten Backend-Prozess.
#
# Später lösen wir die Objekterzeugung über einen kleinen
# Application Container / Dependency Wiring sauberer.
telemetry_service = TelemetryService()
person_service = PersonService()
person_profile_service = PersonProfileService()
training_recommendation_engine = TrainingRecommendationEngine()
workout_repository = SqlAlchemyWorkoutRepository()
workout_service = WorkoutService(repository=workout_repository)
workout_video_repository = SqlAlchemyWorkoutVideoRepository()
video_catalog_service = VideoCatalogService(repository=workout_video_repository)
check_in_repository = SqlAlchemyCheckInRepository()
check_in_service = CheckInService(repository=check_in_repository)
telemetry_broadcaster = TelemetryBroadcaster()


@app.get("/health")
async def health() -> dict[str, str]:
    return {
        "status": "ok",
    }


@app.get(
    "/api/devices",
    response_model=list[DeviceResponse],
    response_model_by_alias=True,
)
async def devices() -> list[DeviceResponse]:
    """
    Liefert den aktuellen Zustand aller bekannten Geräte.

    Der interne DeviceState verwendet Python-konformes snake_case.
    An der HTTP-Grenze serialisieren wir die Felder als camelCase.
    """

    return [
        DeviceResponse(
            device_id=device.device_id,
            device_type=device.device_type,
            device_name=device.device_name,
            status=device.status,
            last_seen=device.last_seen,
            heart_rate_bpm=device.heart_rate_bpm,
            speed_kmh=device.speed_kmh,
            cadence_rpm=device.cadence_rpm,
            distance_m=device.distance_m,
            power_w=device.power_w,
            resistance=device.resistance,
        )
        for device in telemetry_service.get_devices()
    ]


@app.websocket("/ws/device-agent")
async def device_agent_websocket(
    websocket: WebSocket,
) -> None:
    """
    Transport-Controller.

    Wichtig:
    Hier steckt jetzt KEINE eigentliche Telemetrie-Logik mehr.

    Controller:
        JSON empfangen
          ↓
        validieren
          ↓
        Application Service aufrufen
    """

    await websocket.accept()

    logger.info("Device Agent connected")

    try:
        while True:
            raw_message = await websocket.receive_text()

            try:
                message = TelemetryMessage.model_validate_json(raw_message)

            except ValidationError as exc:
                logger.warning(
                    "Invalid telemetry message: %s",
                    exc,
                )
                continue

            telemetry_service.handle(message)

            await telemetry_broadcaster.broadcast(
                message.model_dump_json(
                    by_alias=True,
                )
            )

            logger.debug(
                "Telemetry: type=%s device=%s",
                message.type,
                message.device_id,
            )

    except WebSocketDisconnect:
        logger.info("Device Agent disconnected")


@app.websocket("/ws/telemetry")
async def telemetry_websocket(
    websocket: WebSocket,
) -> None:
    await telemetry_broadcaster.connect(websocket)

    logger.info("Frontend telemetry client connected")

    try:
        while True:
            # Wir erwarten vom Frontend aktuell keine
            # fachlichen Nachrichten.
            #
            # receive_text() hält die Verbindung offen
            # und erkennt Disconnects.
            await websocket.receive_text()

    except WebSocketDisconnect:
        telemetry_broadcaster.disconnect(websocket)

        logger.info("Frontend telemetry client disconnected")


@app.get(
    "/api/persons",
    response_model=list[PersonResponse],
    response_model_by_alias=True,
)
async def persons() -> list[PersonResponse]:
    """
    Liefert die Personen, die den Health Coach verwenden können.

    Die Reihenfolge ist relevant:
    Im Frontend entspricht sie den Tasten 1 bis 4.
    """

    return [
        PersonResponse(
            id=person.id,
            display_name=person.display_name,
        )
        for person in person_service.get_persons()
    ]


@app.post(
    "/api/persons/{person_id}/check-ins",
    response_model=CheckInResponse,
    response_model_by_alias=True,
)
async def create_check_in(
    person_id: int,
    request: CheckInRequest,
) -> CheckInResponse:
    person = person_service.get_person(person_id)

    if person is None:
        raise HTTPException(
            status_code=404,
            detail="Person not found",
        )

    try:
        check_in = check_in_service.create(
            person_id=person_id,
            energy=request.energy,
            recovery=request.recovery,
            muscle_soreness=request.muscle_soreness,
            stress=request.stress,
            available_training_minutes=(request.available_training_minutes),
        )

    except InvalidCheckInError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    return CheckInResponse(
        person_id=check_in.person_id,
        timestamp=check_in.timestamp,
        energy=check_in.energy,
        recovery=check_in.recovery,
        muscle_soreness=check_in.muscle_soreness,
        stress=check_in.stress,
        available_training_minutes=(check_in.available_training_minutes),
    )


@app.get(
    "/api/persons/{person_id}/check-ins/latest",
    response_model=CheckInResponse | None,
    response_model_by_alias=True,
)
async def latest_check_in(
    person_id: int,
) -> CheckInResponse | None:
    person = person_service.get_person(person_id)

    if person is None:
        raise HTTPException(
            status_code=404,
            detail="Person not found",
        )

    check_in = check_in_service.get_latest(person_id)

    if check_in is None:
        return None

    return CheckInResponse(
        person_id=check_in.person_id,
        timestamp=check_in.timestamp,
        energy=check_in.energy,
        recovery=check_in.recovery,
        muscle_soreness=check_in.muscle_soreness,
        stress=check_in.stress,
        available_training_minutes=(check_in.available_training_minutes),
    )


@app.get(
    "/api/persons/{person_id}/training-recommendation",
    response_model=TrainingRecommendationResponse,
    response_model_by_alias=True,
)
async def training_recommendation(
    person_id: int,
) -> TrainingRecommendationResponse:
    person = person_service.get_person(person_id)

    if person is None:
        raise HTTPException(
            status_code=404,
            detail="Person not found",
        )

    recommendation = create_training_recommendation(person_id)

    return TrainingRecommendationResponse(
        workout_type=recommendation.workout_type.value,
        total_duration_minutes=(recommendation.total_duration_minutes),
        reason=recommendation.reason,
        phases=[
            WorkoutPhaseResponse(
                phase_type=phase.phase_type.value,
                duration_minutes=phase.duration_minutes,
                target_heart_rate_min=(phase.target_heart_rate_min),
                target_heart_rate_max=(phase.target_heart_rate_max),
            )
            for phase in recommendation.phases
        ],
    )


def create_training_recommendation(
    person_id: int,
) -> TrainingRecommendation:
    profile = person_profile_service.get_profile(person_id)

    if profile is None:
        raise HTTPException(
            status_code=404,
            detail="Person profile not found",
        )

    check_in = check_in_service.get_latest(person_id)

    if check_in is None:
        raise HTTPException(
            status_code=409,
            detail="No check-in available",
        )

    max_heart_rate = get_max_heart_rate(
        profile,
        datetime.now(UTC).date(),
    )

    return training_recommendation_engine.recommend(
        check_in=check_in,
        max_heart_rate=max_heart_rate,
    )


@app.get(
    "/api/persons/{person_id}/workouts",
    response_model=list[WorkoutResponse],
    response_model_by_alias=True,
)
async def workout_history(
    person_id: int,
    limit: int = 20,
) -> list[WorkoutResponse]:
    """
    Liefert die letzten Workouts einer Person.

    Die neuesten Trainingseinheiten stehen zuerst.
    """

    person = person_service.get_person(person_id)

    if person is None:
        raise HTTPException(
            status_code=404,
            detail="Person not found",
        )

    if limit < 1 or limit > 100:
        raise HTTPException(
            status_code=422,
            detail="Limit must be between 1 and 100",
        )

    workouts = workout_service.get_for_person(
        person_id,
        limit=limit,
    )

    return [to_workout_response(workout) for workout in workouts]


@app.post(
    "/api/persons/{person_id}/workouts",
    response_model=WorkoutResponse,
    response_model_by_alias=True,
)
async def start_workout(
    person_id: int,
) -> WorkoutResponse:
    person = person_service.get_person(person_id)

    if person is None:
        raise HTTPException(
            status_code=404,
            detail="Person not found",
        )

    recommendation = create_training_recommendation(person_id)

    workout = workout_service.start(
        person_id=person_id,
        recommendation=recommendation,
    )

    return to_workout_response(workout)


@app.get(
    "/api/workout-videos",
    response_model=list[WorkoutVideoResponse],
    response_model_by_alias=True,
)
async def get_workout_videos() -> list[WorkoutVideoResponse]:
    """
    Liefert alle aktiven Trainingsvideos.
    """

    videos = video_catalog_service.get_available()

    return [
        to_workout_video_response(video)
        for video in videos
    ]


@app.get(
    "/api/workout-videos/{video_id}",
    response_model=WorkoutVideoResponse,
    response_model_by_alias=True,
)
async def get_workout_video(
    video_id: str,
) -> WorkoutVideoResponse:
    """
    Liefert die Metadaten eines einzelnen Trainingsvideos.
    """

    try:
        video = video_catalog_service.get(video_id)
    except WorkoutVideoNotFoundError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc

    return to_workout_video_response(video)

    
@app.post(
    "/api/workouts/{workout_id}/checkpoint",
    response_model=WorkoutResponse,
    response_model_by_alias=True,
)
async def checkpoint_workout(
    workout_id: str,
    request: WorkoutCheckpointRequest,
) -> WorkoutResponse:
    try:
        workout = workout_service.checkpoint(
            workout_id,
            elapsed_seconds=request.elapsed_seconds,
            distance_m=request.distance_m,
            video_position_seconds=request.video_position_seconds,
        )
    except WorkoutNotFoundError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc

    except WorkoutAlreadyFinishedError as exc:
        raise HTTPException(
            status_code=409,
            detail=str(exc),
        ) from exc

    except InvalidWorkoutDurationError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc

    return to_workout_response(workout)


@app.post(
    "/api/workouts/{workout_id}/complete",
    response_model=WorkoutResponse,
    response_model_by_alias=True,
)
async def complete_workout(
    workout_id: str,
    request: FinishWorkoutRequest,
) -> WorkoutResponse:
    try:
        workout = workout_service.complete(
            workout_id,
            elapsed_seconds=request.elapsed_seconds,
            distance_m=request.distance_m,
        )

    except WorkoutNotFoundError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc

    except WorkoutAlreadyFinishedError as exc:
        raise HTTPException(
            status_code=409,
            detail=str(exc),
        ) from exc

    except InvalidWorkoutDurationError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc

    return to_workout_response(workout)


@app.post(
    "/api/workouts/{workout_id}/abort",
    response_model=WorkoutResponse,
    response_model_by_alias=True,
)
async def abort_workout(
    workout_id: str,
    request: FinishWorkoutRequest,
) -> WorkoutResponse:
    try:
        workout = workout_service.abort(
            workout_id,
            elapsed_seconds=request.elapsed_seconds,
            distance_m=request.distance_m,
        )

    except WorkoutNotFoundError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc

    except WorkoutAlreadyFinishedError as exc:
        raise HTTPException(
            status_code=409,
            detail=str(exc),
        ) from exc

    except InvalidWorkoutDurationError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc

    return to_workout_response(workout)


@app.get(
    "/api/workouts/{workout_id}/summary",
    response_model=WorkoutSummaryResponse,
    response_model_by_alias=True,
)
async def workout_summary(
    workout_id: str,
) -> WorkoutSummaryResponse:
    try:
        summary = workout_service.get_summary(workout_id)
    except WorkoutNotFoundError as error:
        raise HTTPException(
            status_code=404,
            detail=str(error),
        ) from error

    return to_workout_summary_response(summary)
