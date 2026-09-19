from pathlib import Path

import pytest

from features.speech.adapters.piper_tts import PiperTtsAdapter
from features.speech.domain.tts import TextToSpeechUnavailableError


def test_missing_voice_model_is_reported_as_unavailable(tmp_path: Path) -> None:
    adapter = PiperTtsAdapter(tmp_path / "missing.onnx")

    with pytest.raises(TextToSpeechUnavailableError, match="voice model not found"):
        adapter.synthesize("Pause.")


def test_synthesis_uses_configured_coach_voice_settings(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from features.speech.adapters import piper_tts
    from features.speech.adapters.piper_tts import PiperSynthesisSettings

    model_path = tmp_path / "voice.onnx"
    model_path.write_bytes(b"model")
    Path(f"{model_path}.json").write_text("{}", encoding="utf-8")

    captured: dict[str, object] = {}

    class FakeVoice:
        def synthesize_wav(self, text: str, wav_file: object, **kwargs: object) -> None:
            captured["text"] = text
            captured.update(kwargs)
            wav_file.setframerate(22_050)  # type: ignore[attr-defined]
            wav_file.setsampwidth(2)  # type: ignore[attr-defined]
            wav_file.setnchannels(1)  # type: ignore[attr-defined]
            wav_file.writeframes(b"\\x00\\x00")  # type: ignore[attr-defined]

    class FakePiperVoice:
        @staticmethod
        def load(*_args: object, **_kwargs: object) -> FakeVoice:
            return FakeVoice()

    class FakeSynthesisConfig:
        def __init__(self, **kwargs: object) -> None:
            captured["config"] = kwargs

    class FakePiperModule:
        PiperVoice = FakePiperVoice
        SynthesisConfig = FakeSynthesisConfig

    monkeypatch.setattr(piper_tts, "import_module", lambda _name: FakePiperModule)

    adapter = PiperTtsAdapter(
        model_path,
        settings=PiperSynthesisSettings(
            length_scale=0.9,
            noise_scale=0.72,
            noise_w_scale=0.88,
            volume=1.05,
        ),
    )

    speech = adapter.synthesize("Weiter geht's!")

    assert speech.media_type == "audio/wav"
    assert speech.audio.startswith(b"RIFF")
    assert captured["text"] == "Weiter geht's!"
    assert captured["config"] == {
        "length_scale": 0.9,
        "noise_scale": 0.72,
        "noise_w_scale": 0.88,
        "volume": 1.05,
    }
    assert isinstance(captured["syn_config"], FakeSynthesisConfig)


def test_synthesis_settings_reject_invalid_length_scale() -> None:
    from features.speech.adapters.piper_tts import PiperSynthesisSettings

    with pytest.raises(ValueError, match="length_scale"):
        PiperSynthesisSettings(length_scale=0)
