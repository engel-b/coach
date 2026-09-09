from typing import Annotated

from fastapi import APIRouter, HTTPException, Path, Query

from apps.api import wiring
from features.check_in.api.contracts.check_in import CheckInRequest, CheckInResponse
from features.check_in.domain.check_in import CheckIn
from features.check_in.service.service import InvalidCheckInError

router = APIRouter(tags=["Check-ins"])


PersonId = Annotated[
    int,
    Path(
        title="Personen-ID",
        description="Stabile numerische ID der Person.",
    ),
]


@router.post(
    "/api/persons/{person_id}/check-ins",
    response_model=CheckInResponse,
    response_model_by_alias=True,
    summary="Check-in erfassen",
    description=(
        "Erfasst die aktuelle Tagesform und die verfügbare Trainingszeit "
        "einer Person. Der Check-in wird mit einem Zeitstempel gespeichert "
        "und kann anschließend für eine Trainingsempfehlung verwendet werden."
    ),
    responses={
        400: {
            "description": ("Die Angaben verletzen eine fachliche Validierungsregel."),
        },
        404: {
            "description": "Die Person wurde nicht gefunden.",
        },
        422: {
            "description": ("Die Anfrage entspricht nicht dem erwarteten JSON-Schema."),
        },
    },
)
async def create_check_in(
    person_id: int,
    request: CheckInRequest,
) -> CheckInResponse:
    person = wiring.person_service.get_person(person_id)

    if person is None:
        raise HTTPException(
            status_code=404,
            detail="Person not found",
        )

    try:
        check_in = wiring.check_in_service.create(
            person_id=person_id,
            energy=request.energy,
            recovery=request.recovery,
            muscle_soreness=request.muscle_soreness,
            stress=request.stress,
            available_training_minutes=(request.available_training_minutes),
            current_weight_kg=request.current_weight_kg,
            sleep_hours=request.sleep_hours,
            steps=request.steps,
        )
    except InvalidCheckInError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    return _to_response(check_in)


@router.get(
    "/api/persons/{person_id}/check-ins/latest",
    response_model=CheckInResponse | None,
    response_model_by_alias=True,
    summary="Letzten Check-in abrufen",
    description=(
        "Liefert den zuletzt gespeicherten Check-in einer Person. "
        "Wenn die Person existiert, aber noch keinen Check-in hat, "
        "wird HTTP 200 mit dem JSON-Wert null zurückgegeben."
    ),
    responses={
        404: {
            "description": "Die Person wurde nicht gefunden.",
        },
    },
)
async def latest_check_in(
    person_id: int,
) -> CheckInResponse | None:
    person = wiring.person_service.get_person(person_id)

    if person is None:
        raise HTTPException(
            status_code=404,
            detail="Person not found",
        )

    check_in = wiring.check_in_service.get_latest(person_id)

    if check_in is None:
        return None

    return _to_response(check_in)


@router.get(
    "/api/persons/{person_id}/check-ins",
    response_model=list[CheckInResponse],
    response_model_by_alias=True,
    summary="Check-in-Historie abrufen",
    description=(
        "Liefert die neuesten Check-ins einer Person, absteigend nach "
        "Zeitpunkt sortiert. Die Anzahl ist begrenzt. Fehlende optionale "
        "Tagesdaten bleiben null."
    ),
    responses={
        404: {"description": "Die Person wurde nicht gefunden."},
        422: {"description": "Der limit-Parameter ist ungültig."},
    },
)
async def check_in_history(
    person_id: PersonId,
    limit: Annotated[
        int,
        Query(ge=1, le=1000, description="Maximale Anzahl der Check-ins."),
    ] = 90,
) -> list[CheckInResponse]:
    if wiring.person_service.get_person(person_id) is None:
        raise HTTPException(status_code=404, detail="Person not found")

    return [
        _to_response(check_in) for check_in in wiring.check_in_service.get_history(person_id, limit)
    ]


def _to_response(check_in: CheckIn) -> CheckInResponse:
    return CheckInResponse(
        person_id=check_in.person_id,
        timestamp=check_in.timestamp,
        energy=check_in.energy,
        recovery=check_in.recovery,
        muscle_soreness=check_in.muscle_soreness,
        stress=check_in.stress,
        available_training_minutes=check_in.available_training_minutes,
        current_weight_kg=check_in.current_weight_kg,
        sleep_hours=check_in.sleep_hours,
        steps=check_in.steps,
    )
