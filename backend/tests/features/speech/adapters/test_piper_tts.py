from pathlib import Path

import pytest

from features.speech.adapters.piper_tts import PiperTtsAdapter
from features.speech.domain.tts import TextToSpeechUnavailableError


def test_missing_voice_model_is_reported_as_unavailable(tmp_path: Path) -> None:
    adapter = PiperTtsAdapter(tmp_path / "missing.onnx")

    with pytest.raises(TextToSpeechUnavailableError, match="voice model not found"):
        adapter.synthesize("Pause.")
