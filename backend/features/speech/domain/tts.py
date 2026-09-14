from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class SynthesizedSpeech:
    audio: bytes
    media_type: str


class TextToSpeech(Protocol):
    """Technischer Port fuer lokale Sprachsynthese."""

    def synthesize(self, text: str) -> SynthesizedSpeech: ...


class TextToSpeechUnavailableError(RuntimeError):
    """Die konfigurierte TTS-Engine ist aktuell nicht nutzbar."""
