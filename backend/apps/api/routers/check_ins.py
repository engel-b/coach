from fastapi import APIRouter, HTTPException

from apps.api import wiring
from application.check_in.service import InvalidCheckInError
from contracts.check_in import CheckInRequest, CheckInResponse


router = APIRouter()


@router.post(
    "/api/persons/{person_id}/check-ins",
    response_model=CheckInResponse,
    response_model_by_alias=True,
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
            available_training_minutes=(
                request.available_training_minutes
            ),
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
        available_training_minutes=(
            check_in.available_training_minutes
        ),
    )


@router.get(
    "/api/persons/{person_id}/check-ins/latest",
    response_model=CheckInResponse | None,
    response_model_by_alias=True,
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

    return CheckInResponse(
        person_id=check_in.person_id,
        timestamp=check_in.timestamp,
        energy=check_in.energy,
        recovery=check_in.recovery,
        muscle_soreness=check_in.muscle_soreness,
        stress=check_in.stress,
        available_training_minutes=(
            check_in.available_training_minutes
        ),
    )