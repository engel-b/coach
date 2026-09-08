from typing import Annotated

from fastapi import APIRouter, HTTPException, Path

from apps.api import wiring
from contracts.person import PersonResponse
from contracts.person_create import CreatePersonRequest
from contracts.person_profile import (
    PersonProfileRequest,
    PersonProfileResponse,
)
from features.person.domain.profile import PersonProfile
from features.person.domain.profile_validation import InvalidPersonProfileError
from features.person.service.management_service import PersonNotFoundError

router = APIRouter(
    tags=["Persons"],
)


PersonId = Annotated[
    int,
    Path(
        title="Personen-ID",
        description=(
            "Stabile numerische ID der Person. Die ID bleibt auch "
            "bei einer Änderung des Anzeigenamens erhalten."
        ),
        ge=1,
    ),
]


@router.get(
    "/api/persons",
    response_model=list[PersonResponse],
    response_model_by_alias=True,
    summary="Personen auflisten",
    description=(
        "Liefert alle angelegten Personen mit ihrer ID und ihrem "
        "Anzeigenamen. Die Liste wird für die Personenauswahl verwendet."
    ),
)
async def persons() -> list[PersonResponse]:
    return [
        PersonResponse(
            id=person.id,
            display_name=person.display_name,
        )
        for person in wiring.person_service.get_persons()
    ]


@router.post(
    "/api/persons",
    response_model=PersonProfileResponse,
    response_model_by_alias=True,
    status_code=201,
    summary="Person anlegen",
    description=(
        "Legt eine neue Person zusammen mit ihrem Trainingsprofil an. "
        "Person und Profil werden in einer gemeinsamen Datenbanktransaktion "
        "gespeichert. Die ID wird automatisch vergeben.\n\n"
        "Beim Trainingsziel „Abnehmen“ sind Start- und Zielgewicht "
        "erforderlich. Das Zielgewicht muss unter dem Startgewicht liegen."
    ),
    responses={
        422: {
            "description": (
                "Die Eingabedaten sind ungültig, beispielsweise wegen "
                "eines fehlenden Pflichtfeldes, eines ungültigen "
                "Geburtsdatums oder einer nicht zulässigen "
                "Gewichtskonstellation."
            ),
        },
    },
)
async def create_person(
    request: CreatePersonRequest,
) -> PersonProfileResponse:
    try:
        person, profile = wiring.person_management_service.create_person(
            display_name=request.display_name,
            date_of_birth=request.date_of_birth,
            height_cm=request.height_cm,
            training_goal=request.training_goal,
            max_heart_rate_bpm=request.max_heart_rate_bpm,
            start_weight_kg=request.start_weight_kg,
            target_weight_kg=request.target_weight_kg,
        )
    except InvalidPersonProfileError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc

    return PersonProfileResponse(
        person_id=person.id,
        display_name=person.display_name,
        date_of_birth=profile.date_of_birth,
        height_cm=profile.height_cm,
        training_goal=profile.training_goal,
        max_heart_rate_bpm=profile.max_heart_rate_bpm,
        start_weight_kg=profile.start_weight_kg,
        target_weight_kg=profile.target_weight_kg,
    )


@router.get(
    "/api/persons/{person_id}/profile",
    response_model=PersonProfileResponse,
    response_model_by_alias=True,
    summary="Personenprofil abrufen",
    description=(
        "Liefert die Stammdaten und Trainingsziele einer Person. "
        "Das Profil enthält unter anderem Geburtsdatum, Körpergröße, "
        "Trainingsziel und optionale Gewichts- und Pulswerte."
    ),
    responses={
        404: {
            "description": "Die Person oder ihr Profil wurde nicht gefunden.",
        },
    },
)
async def get_person_profile(
    person_id: int,
) -> PersonProfileResponse:
    person = wiring.person_service.get_person(person_id)

    if person is None:
        raise HTTPException(
            status_code=404,
            detail="Person not found",
        )

    profile = wiring.person_profile_service.get_profile(person_id)

    if profile is None:
        raise HTTPException(
            status_code=404,
            detail="Person profile not found",
        )

    return PersonProfileResponse(
        person_id=person.id,
        display_name=person.display_name,
        date_of_birth=profile.date_of_birth,
        height_cm=profile.height_cm,
        training_goal=profile.training_goal,
        max_heart_rate_bpm=profile.max_heart_rate_bpm,
        start_weight_kg=profile.start_weight_kg,
        target_weight_kg=profile.target_weight_kg,
    )


@router.put(
    "/api/persons/{person_id}/profile",
    response_model=PersonProfileResponse,
    response_model_by_alias=True,
    summary="Personenprofil bearbeiten",
    description=(
        "Aktualisiert den Anzeigenamen und das vollständige Trainingsprofil "
        "einer bestehenden Person. Die Personen-ID bleibt unverändert. "
        "Alle Änderungen werden gemeinsam gespeichert.\n\n"
        "Beim Trainingsziel „Abnehmen“ müssen Start- und Zielgewicht "
        "vorhanden sein und das Zielgewicht muss niedriger sein. "
        "Die aktuellen Tageswerte wie Gewicht, Schlaf und Schritte "
        "gehören dagegen zum Check-in und nicht zum Stammdatenprofil."
    ),
    responses={
        404: {
            "description": "Die Person wurde nicht gefunden.",
        },
        422: {
            "description": (
                "Die Profilangaben sind ungültig oder verletzen eine fachliche Validierungsregel."
            ),
        },
    },
)
async def update_person_profile(
    person_id: int,
    request: PersonProfileRequest,
) -> PersonProfileResponse:
    person = wiring.person_service.get_person(person_id)

    if person is None:
        raise HTTPException(
            status_code=404,
            detail="Person not found",
        )

    profile = PersonProfile(
        person_id=person_id,
        date_of_birth=request.date_of_birth,
        height_cm=request.height_cm,
        training_goal=request.training_goal,
        max_heart_rate_bpm=request.max_heart_rate_bpm,
        start_weight_kg=request.start_weight_kg,
        target_weight_kg=request.target_weight_kg,
    )

    try:
        updated_person, saved_profile = wiring.person_management_service.update_profile(
            person_id=person_id,
            display_name=request.display_name,
            profile=profile,
        )
    except PersonNotFoundError as exc:
        raise HTTPException(
            status_code=404,
            detail="Person not found",
        ) from exc
    except InvalidPersonProfileError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc

    return PersonProfileResponse(
        person_id=updated_person.id,
        display_name=updated_person.display_name,
        date_of_birth=saved_profile.date_of_birth,
        height_cm=saved_profile.height_cm,
        training_goal=saved_profile.training_goal,
        max_heart_rate_bpm=saved_profile.max_heart_rate_bpm,
        start_weight_kg=saved_profile.start_weight_kg,
        target_weight_kg=saved_profile.target_weight_kg,
    )
