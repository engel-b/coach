from __future__ import annotations

import os
import urllib.request
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_MODEL_PATH = PROJECT_ROOT / "data" / "models" / "llm" / "qwen3.5-0.8b-q4_0.gguf"

configured_model_path = Path(
    os.environ.get("HEALTH_COACH_LLM_MODEL_PATH", str(DEFAULT_MODEL_PATH))
).expanduser()
MODEL_PATH = (
    configured_model_path
    if configured_model_path.is_absolute()
    else (PROJECT_ROOT / configured_model_path).resolve()
)
MODEL_DIR = MODEL_PATH.parent
MODEL_URL = os.environ.get(
    "HEALTH_COACH_LLM_MODEL_URL",
    "https://huggingface.co/ggml-org/Qwen3.5-0.8B-GGUF/resolve/main/Qwen3.5-0.8B-Q4_0.gguf",
)


def ensure_llm_model() -> None:
    if MODEL_PATH.is_file() and MODEL_PATH.stat().st_size > 0:
        print(f"Local LLM model already installed: {MODEL_PATH}")
        return

    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    temporary_path = MODEL_PATH.with_suffix(MODEL_PATH.suffix + ".part")

    print(f"Downloading local LLM model to {MODEL_PATH} ...")

    try:
        urllib.request.urlretrieve(MODEL_URL, temporary_path)
        temporary_path.replace(MODEL_PATH)
    finally:
        if temporary_path.exists():
            temporary_path.unlink()

    if not MODEL_PATH.is_file() or MODEL_PATH.stat().st_size == 0:
        raise RuntimeError(f"LLM model download failed: {MODEL_PATH}")

    print(f"Local LLM model installed: {MODEL_PATH}")


if __name__ == "__main__":
    ensure_llm_model()
