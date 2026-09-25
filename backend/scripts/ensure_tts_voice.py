from __future__ import annotations

import os
import shutil
import subprocess
import sys
from importlib import import_module
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any, cast
from uuid import uuid4

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


def _validate_voice(model_path: Path) -> None:
    """A present file is not necessarily a loadable ONNX model."""
    if not voice_is_installed(model_path):
        raise RuntimeError(f"Piper model/config missing: {model_path} / {_config_path(model_path)}")

    piper = cast(Any, import_module("piper"))
    piper.PiperVoice.load(model_path, config_path=_config_path(model_path), use_cuda=False)


def _install_staged_voice(model_path: Path) -> None:
    voice_dir = model_path.parent
    voice_dir.mkdir(parents=True, exist_ok=True)

    # Download and load in the same filesystem before touching a working installation.
    with TemporaryDirectory(prefix=".piper-voice-", dir=voice_dir) as temporary:
        staged_dir = Path(temporary)
        staged_model = staged_dir / f"{VOICE_NAME}.onnx"
        subprocess.run(
            [
                sys.executable,
                "-m",
                "piper.download_voices",
                "--data-dir",
                str(staged_dir),
                VOICE_NAME,
            ],
            cwd=BACKEND_ROOT,
            check=True,
        )
        _validate_voice(staged_model)

        staged_files = (
            (staged_model, model_path),
            (_config_path(staged_model), _config_path(model_path)),
        )
        replaced: list[tuple[Path, Path | None]] = []
        try:
            for source, target in staged_files:
                backup = Path(f"{target}.bak.{uuid4().hex}") if target.exists() else None
                if backup is not None:
                    shutil.copy2(target, backup)
                    print(f"Previous Piper file saved: {backup}")
                replaced.append((target, backup))
                source.replace(target)
        except OSError:
            for target, backup in reversed(replaced):
                if backup is None:
                    target.unlink(missing_ok=True)
                else:
                    shutil.copy2(backup, target)
            raise


def ensure_tts_voice(model_path: Path | None = None) -> None:
    model_path = (model_path or _configured_model_path()).resolve()
    voice_dir = model_path.parent

    if voice_is_installed(model_path):
        try:
            _validate_voice(model_path)
        # Piper, ONNX Runtime und ihre nativen Bindings melden Ladefehler
        # mit unterschiedlichen Exception-Typen. Jeder davon erfordert Ersatz.
        except Exception as exc:  # noqa: BLE001
            print(
                f"Piper voice cannot be loaded ({exc}); trying a validated replacement.",
                file=sys.stderr,
            )
        else:
            print(f"Piper voice checked and loadable: {model_path}")
            return
    else:
        print(f"Piper voice missing; downloading {VOICE_NAME} to {voice_dir} ...")

    # If download or validation fails, the original voice stays untouched and
    # provisioning stops before restarting the services.
    _install_staged_voice(model_path)

    print(f"Piper voice installed and verified: {model_path}")


if __name__ == "__main__":
    ensure_tts_voice()
