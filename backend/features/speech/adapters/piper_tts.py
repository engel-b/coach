from __future__ import annotations

import io
import threading
import wave
from importlib import import_module
from pathlib import Path
from typing import Any, Protocol, cast

from features.speech.domain.tts import (
    SynthesizedSpeech,
    TextToSpeechUnavailableError,
)


class _PiperVoice(Protocol):
    def synthesize_wav(
        self,
        text: str,
        wav_file: wave.Wave_write,
        *args: object,
        **kwargs: object,
    ) -> object | None: ...


class PiperTtsAdapter:
    """Lokaler Piper-Adapter mit lazy geladenem Voice-Modell.

    Das Modell wird erst beim ersten Syntheseaufruf geladen und danach fuer
    weitere kurze Coach-Ansagen wiederverwendet. Die Synthese wird serialisiert,
    damit parallele Requests nicht gleichzeitig dieselbe Voice-Instanz nutzen.
    """

    def __init__(self, model_path: Path) -> None:
        self._model_path = model_path
        self._voice: _PiperVoice | None = None
        self._lock = threading.Lock()

    def synthesize(self, text: str) -> SynthesizedSpeech:
        with self._lock:
            voice = self._get_voice()
            buffer = io.BytesIO()

            with wave.open(buffer, "wb") as wav_file:
                voice.synthesize_wav(text, wav_file)

            return SynthesizedSpeech(
                audio=buffer.getvalue(),
                media_type="audio/wav",
            )

    def _get_voice(self) -> _PiperVoice:
        if self._voice is not None:
            return self._voice

        if not self._model_path.is_file():
            raise TextToSpeechUnavailableError(f"Piper voice model not found: {self._model_path}")

        config_path = Path(f"{self._model_path}.json")
        if not config_path.is_file():
            raise TextToSpeechUnavailableError(f"Piper voice config not found: {config_path}")

        try:
            piper = cast(Any, import_module("piper"))
        except ImportError as exc:
            raise TextToSpeechUnavailableError(
                "Piper is not installed. Install the backend dependencies again."
            ) from exc

        try:
            self._voice = cast(
                _PiperVoice,
                piper.PiperVoice.load(
                    self._model_path,
                    config_path=config_path,
                    use_cuda=False,
                ),
            )
        except Exception as exc:
            raise TextToSpeechUnavailableError(
                f"Could not load Piper voice model: {self._model_path}"
            ) from exc

        return self._voice
