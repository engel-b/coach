from __future__ import annotations

import io
import threading
import wave
from dataclasses import dataclass
from importlib import import_module
from pathlib import Path
from typing import Any, Protocol, cast

from features.speech.domain.tts import (
    SynthesizedSpeech,
    TextToSpeechUnavailableError,
)


@dataclass(frozen=True)
class PiperSynthesisSettings:
    """Runtime-Einstellungen fuer die Coach-Stimme.

    Kleinere ``length_scale``-Werte sprechen schneller. ``noise_scale`` und
    ``noise_w_scale`` erhoehen die Variation, sollten aber nur moderat vom
    Voice-Default abweichen, damit die Verstaendlichkeit stabil bleibt.
    """

    length_scale: float = 0.92
    noise_scale: float = 0.70
    noise_w_scale: float = 0.85
    volume: float = 1.0

    def __post_init__(self) -> None:
        if self.length_scale <= 0:
            raise ValueError("length_scale must be greater than zero")
        if self.noise_scale < 0:
            raise ValueError("noise_scale must not be negative")
        if self.noise_w_scale < 0:
            raise ValueError("noise_w_scale must not be negative")
        if self.volume <= 0:
            raise ValueError("volume must be greater than zero")


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

    def __init__(
        self,
        model_path: Path,
        *,
        settings: PiperSynthesisSettings | None = None,
    ) -> None:
        self._model_path = model_path
        self._settings = settings or PiperSynthesisSettings()
        self._voice: _PiperVoice | None = None
        self._synthesis_config: object | None = None
        self._lock = threading.Lock()

    def synthesize(self, text: str) -> SynthesizedSpeech:
        with self._lock:
            voice = self._get_voice()
            synthesis_config = self._get_synthesis_config()
            buffer = io.BytesIO()

            with wave.open(buffer, "wb") as wav_file:
                voice.synthesize_wav(
                    text,
                    wav_file,
                    syn_config=synthesis_config,
                )

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

        piper = self._import_piper()

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

    def _get_synthesis_config(self) -> object:
        if self._synthesis_config is not None:
            return self._synthesis_config

        piper = self._import_piper()
        self._synthesis_config = piper.SynthesisConfig(
            length_scale=self._settings.length_scale,
            noise_scale=self._settings.noise_scale,
            noise_w_scale=self._settings.noise_w_scale,
            volume=self._settings.volume,
        )
        return self._synthesis_config

    @staticmethod
    def _import_piper() -> Any:
        try:
            return cast(Any, import_module("piper"))
        except ImportError as exc:
            raise TextToSpeechUnavailableError(
                "Piper is not installed. Install the backend dependencies again."
            ) from exc
