from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

VOICE_NAME = "de_DE-thorsten-medium"
PROJECT_ROOT = Path(__file__).resolve().parents[2]
BACKEND_ROOT = PROJECT_ROOT / "backend"
DEFAULT_MODEL_PATH = PROJECT_ROOT / "data" / "models" / "piper-tts" / f"{VOICE_NAME}.onnx"

configured_model_path = Path(
    os.environ.get("HEALTH_COACH_PIPER_MODEL", str(DEFAULT_MODEL_PATH))
).expanduser()
MODEL_PATH = (
    configured_model_path
    if configured_model_path.is_absolute()
    else (PROJECT_ROOT / configured_model_path).resolve()
)
VOICE_DIR = MODEL_PATH.parent
CONFIG_PATH = MODEL_PATH.with_suffix(MODEL_PATH.suffix + ".json")


def voice_is_installed() -> bool:
    return MODEL_PATH.is_file() and CONFIG_PATH.is_file()


def ensure_tts_voice() -> None:
    if voice_is_installed():
        print(f"Piper voice already installed: {MODEL_PATH}")
        return

    VOICE_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Piper voice missing; downloading {VOICE_NAME} to {VOICE_DIR} ...")

    subprocess.run(
        [
            sys.executable,
            "-m",
            "piper.download_voices",
            "--data-dir",
            str(VOICE_DIR),
            VOICE_NAME,
        ],
        cwd=BACKEND_ROOT,
        check=True,
    )

    if not voice_is_installed():
        raise RuntimeError(
            "Piper voice download completed, but model/config files are still missing: "
            f"{MODEL_PATH} / {CONFIG_PATH}"
        )

    print(f"Piper voice installed: {MODEL_PATH}")


if __name__ == "__main__":
    ensure_tts_voice()
