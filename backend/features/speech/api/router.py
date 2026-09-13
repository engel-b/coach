import logging

from fastapi import APIRouter, HTTPException, Response

from apps.api import wiring
from features.speech.api.contracts.speech import SynthesizeSpeechRequest
from features.speech.domain.tts import TextToSpeechUnavailableError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/speech", tags=["Speech"])


@router.post(
    "/synthesize",
    response_class=Response,
    responses={
        200: {
            "content": {"audio/wav": {}},
            "description": "Lokal synthetisierte WAV-Audiodaten.",
        },
        503: {"description": "Die lokale TTS-Engine ist nicht verfuegbar."},
    },
    summary="Text lokal als Sprache synthetisieren",
)
def synthesize_speech(request: SynthesizeSpeechRequest) -> Response:
    try:
        speech = wiring.speech_service.synthesize(request.text)
    except TextToSpeechUnavailableError as exc:
        logger.warning("Local TTS unavailable: %s", exc)
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    return Response(
        content=speech.audio,
        media_type=speech.media_type,
        headers={"Cache-Control": "no-store"},
    )
