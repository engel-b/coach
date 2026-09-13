import pytest

from features.speech.domain.tts import SynthesizedSpeech
from features.speech.service.speech_service import SpeechService


class FakeTts:
    def __init__(self) -> None:
        self.received_text: str | None = None

    def synthesize(self, text: str) -> SynthesizedSpeech:
        self.received_text = text
        return SynthesizedSpeech(audio=b"RIFF-test", media_type="audio/wav")


def test_synthesize_normalizes_text_and_delegates_to_tts() -> None:
    tts = FakeTts()
    service = SpeechService(tts)

    result = service.synthesize("  Pause.  ")

    assert tts.received_text == "Pause."
    assert result.audio == b"RIFF-test"
    assert result.media_type == "audio/wav"


def test_synthesize_rejects_empty_text() -> None:
    service = SpeechService(FakeTts())

    with pytest.raises(ValueError, match="must not be empty"):
        service.synthesize("   ")
