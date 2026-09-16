from __future__ import annotations

import subprocess
import sys
from pathlib import Path

VOICE_NAME = "de_DE-thorsten-medium"
BACKEND_ROOT = Path(__file__).resolve().parents[1]
VOICE_DIR = BACKEND_ROOT / "models" / "piper"
MODEL_PATH = VOICE_DIR / f"{VOICE_NAME}.onnx"
CONFIG_PATH = VOICE_DIR / f"{VOICE_NAME}.onnx.json"


def voice_is_installed() -> bool:
    return MODEL_PATH.is_file() and CONFIG_PATH.is_file()


def ensure_tts_voice() -> None:
    if voice_is_installed():
        print(f"Piper voice already installed: {VOICE_NAME}")
        return

    VOICE_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Piper voice missing; downloading {VOICE_NAME} ...")

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
