from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

from ensure_llm_model import MODEL_PATH

BACKEND_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ALIAS = "health-coach-local"


def main() -> None:
    executable = os.environ.get("HEALTH_COACH_LLAMA_SERVER") or shutil.which("llama-server")
    if executable is None:
        raise RuntimeError(
            "llama-server was not found. Install llama.cpp first "
            "(Windows: winget install llama.cpp) or set HEALTH_COACH_LLAMA_SERVER."
        )

    if not MODEL_PATH.is_file():
        raise RuntimeError(f"Local LLM model not found: {MODEL_PATH}. Run 'make llm-model' first.")

    alias = os.environ.get("HEALTH_COACH_LLM_MODEL", DEFAULT_ALIAS)
    host = os.environ.get("HEALTH_COACH_LLM_HOST", "127.0.0.1")
    port = os.environ.get("HEALTH_COACH_LLM_PORT", "8080")
    context_size = os.environ.get("HEALTH_COACH_LLM_CONTEXT_SIZE", "2048")
    threads = os.environ.get("HEALTH_COACH_LLM_THREADS", "4")

    command = [
        executable,
        "-m",
        str(MODEL_PATH),
        "--alias",
        alias,
        "--host",
        host,
        "--port",
        port,
        "-c",
        context_size,
        "-t",
        threads,
    ]

    print("Starting local LLM server ...")
    print(" ".join(command))
    subprocess.run(command, cwd=BACKEND_ROOT, check=True)


if __name__ == "__main__":
    main()
