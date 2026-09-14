from fastapi.testclient import TestClient
from pytest import MonkeyPatch

from apps.api import wiring
from apps.api.main import app
from features.speech.domain.tts import SynthesizedSpeech
from features.speech.service.speech_service import SpeechService


class FakeTts:
    def synthesize(self, text: str) -> SynthesizedSpeech:
        assert text == "Pause."
        return SynthesizedSpeech(audio=b"RIFF-test", media_type="audio/wav")


def test_synthesize_returns_wav(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setattr(wiring, "speech_service", SpeechService(FakeTts()))
    client = TestClient(app)

    response = client.post("/api/speech/synthesize", json={"text": "Pause."})

    assert response.status_code == 200
    assert response.headers["content-type"] == "audio/wav"
    assert response.content == b"RIFF-test"
