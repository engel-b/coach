from __future__ import annotations

import os
import urllib.request
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_MODEL_PATH = Path("data/models/llm/qwen3.5-0.8b-q4_0.gguf")
MODEL_URL = os.environ.get(
    "HEALTH_COACH_LLM_MODEL_URL",
    "https://huggingface.co/ggml-org/Qwen3.5-0.8B-GGUF/resolve/main/Qwen3.5-0.8B-Q4_0.gguf",
)


def _configured_model_path() -> Path:
    configured = Path(
        os.environ.get("HEALTH_COACH_LLM_MODEL_PATH", str(DEFAULT_MODEL_PATH))
    ).expanduser()
    return configured if configured.is_absolute() else PROJECT_ROOT / configured


def ensure_llm_model() -> None:
    model_path = _configured_model_path().resolve()
    model_dir = model_path.parent

    if model_path.is_file() and model_path.stat().st_size > 0:
        print(f"Local LLM model already installed: {model_path}")
        return

    model_dir.mkdir(parents=True, exist_ok=True)
    temporary_path = model_path.with_suffix(model_path.suffix + ".part")

    print(f"Downloading local LLM model to {model_path} ...")

    try:
        urllib.request.urlretrieve(MODEL_URL, temporary_path)
        temporary_path.replace(model_path)
    finally:
        if temporary_path.exists():
            temporary_path.unlink()

    if not model_path.is_file() or model_path.stat().st_size == 0:
        raise RuntimeError(f"LLM model download failed: {model_path}")

    print(f"Local LLM model installed: {model_path}")


if __name__ == "__main__":
    ensure_llm_model()
