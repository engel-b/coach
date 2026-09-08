from fastapi import APIRouter

router = APIRouter(tags=["System"])


@router.get(
    "/health",
    summary="Backend-Zustand prüfen",
    description=(
        "Ein einfacher technischer Health-Check. Liefert HTTP 200 mit "
        "dem Status ok, wenn die HTTP-Anwendung erreichbar ist. "
        "Der Endpunkt prüft keine Datenbankverbindung und keine "
        "angeschlossenen Trainingsgeräte."
    ),
    responses={
        200: {
            "description": "Die HTTP-Anwendung ist erreichbar.",
            "content": {
                "application/json": {
                    "example": {"status": "ok"},
                },
            },
        },
    },
)
async def health() -> dict[str, str]:
    return {
        "status": "ok",
    }
