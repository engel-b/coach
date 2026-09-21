from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

VOICE_NAME = "de_DE-thorsten-medium"
PROJECT_ROOT = Path(__file__).resolve().parents[2]
BACKEND_ROOT = PROJECT_ROOT / "backend"
DEFAULT_MODEL_PATH = Path(f"data/models/piper-tts/{VOICE_NAME}.onnx")


def _configured_model_path() -> Path:
    configured = Path(
        os.environ.get("HEALTH_COACH_PIPER_MODEL", str(DEFAULT_MODEL_PATH))
    ).expanduser()
    return configured if configured.is_absolute() else PROJECT_ROOT / configured


def _config_path(model_path: Path) -> Path:
    return model_path.with_suffix(model_path.suffix + ".json")


def voice_is_installed(model_path: Path) -> bool:
    return model_path.is_file() and _config_path(model_path).is_file()


def ensure_tts_voice() -> None:
    model_path = _configured_model_path().resolve()
    voice_dir = model_path.parent
    config_path = _config_path(model_path)

    if voice_is_installed(model_path):
        print(f"Piper voice already installed: {model_path}")
        return

    voice_dir.mkdir(parents=True, exist_ok=True)
    print(f"Piper voice missing; downloading {VOICE_NAME} to {voice_dir} ...")

    subprocess.run(
        [
            sys.executable,
            "-m",
            "piper.download_voices",
            "--data-dir",
            str(voice_dir),
            VOICE_NAME,
        ],
        cwd=BACKEND_ROOT,
        check=True,
    )

    if not voice_is_installed(model_path):
        raise RuntimeError(
            "Piper voice download completed, but model/config files are still missing: "
            f"{model_path} / {config_path}"
        )

    print(f"Piper voice installed: {model_path}")


if __name__ == "__main__":
    ensure_tts_voice()
