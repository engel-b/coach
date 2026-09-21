# Local LLM runtime

The Health Coach can optionally use a local OpenAI-compatible LLM for wording pre-workout coaching messages. The deterministic template generator remains the fallback and the workout decision itself is never delegated to the LLM.

Recommended first runtime for the Lenovo ThinkCentre M900z / Intel i3-6100 / 16 GB RAM:

- runtime: `llama.cpp` / `llama-server`
- model: `Qwen3.5-0.8B` GGUF, `Q4_0`
- context: 2048 tokens
- CPU threads: 4
- bind address: `127.0.0.1:8080`

On Windows, install llama.cpp once:

```powershell
winget install llama.cpp
```

Download the model once:

```bash
make llm-model
```

Start the local model server:

```bash
make llm-server
```

Then start the backend with LLM wording enabled:

```powershell
$env:HEALTH_COACH_LLM_ENABLED="1"
$env:HEALTH_COACH_LLM_BASE_URL="http://127.0.0.1:8080"
$env:HEALTH_COACH_LLM_MODEL="health-coach-local"
$env:HEALTH_COACH_LLM_TIMEOUT_SECONDS="8"
make backend
```

Normal backend startup never downloads the model. If the LLM is disabled, unavailable, times out, or returns no usable text, the deterministic template generator remains available as fallback.

By default the GGUF model is stored in `data/models/llm/qwen3.5-0.8b-q4_0.gguf`.

The model URL can be overridden with `HEALTH_COACH_LLM_MODEL_URL`. The server executable can be overridden with `HEALTH_COACH_LLAMA_SERVER` if it is not on `PATH`.
