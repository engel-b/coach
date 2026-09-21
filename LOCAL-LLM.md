# Local LLM runtime

The Health Coach can optionally use a local OpenAI-compatible LLM for wording or explaining already determined coaching information. **Workout decisions, safety rules, readiness logic and live-coaching decisions are never delegated to the LLM.** The deterministic generator remains the fallback.

## Runtime and model

Current baseline for the Lenovo ThinkCentre M900z / Intel i3-6100 / 16 GB RAM:

- runtime: `llama.cpp` / `llama-server`
- model: `Qwen3.5-0.8B` GGUF, `Q4_0`
- context: 2048 tokens
- CPU threads: 4
- bind address: `127.0.0.1:8080`
- model alias: `health-coach-local`

The default model file is:

```text
data/models/llm/qwen3.5-0.8b-q4_0.gguf
```

Production uses the corresponding absolute path below `/opt/health-coach/data/models/llm/`.

## Provision the model

Download/verify the configured model once:

```bash
make llm-model
```

`backend/scripts/ensure_llm_model.py` is the single provisioning implementation. The model URL can be overridden with `HEALTH_COACH_LLM_MODEL_URL`; the model path can be overridden with `HEALTH_COACH_LLM_MODEL_PATH`. Relative project paths are resolved against the repository root.

Normal backend startup and normal appliance boot never download the model. Downloads belong to explicit provisioning.

## Development

On Windows, `llama.cpp` can for example be installed once with:

```powershell
winget install llama.cpp
```

Start the local model server:

```bash
make llm-server
```

The server executable can be overridden with `HEALTH_COACH_LLAMA_SERVER` if it is not on `PATH`.

Enable LLM wording for the backend (PowerShell example):

```powershell
$env:HEALTH_COACH_LLM_ENABLED="1"
$env:HEALTH_COACH_LLM_BASE_URL="http://127.0.0.1:8080"
$env:HEALTH_COACH_LLM_MODEL="health-coach-local"
$env:HEALTH_COACH_LLM_TIMEOUT_SECONDS="15"
make backend
```

On Bash use the same variable names with `export`.

For Qwen3.5 the request adapter disables model-side thinking for this wording use case (`enable_thinking = false`) so the local runtime returns the intended concise completion instead of an additional reasoning phase.

## Production

Expected executable:

```text
/usr/local/bin/llama-server
```

Expected environment file:

```text
/etc/health-coach/llm.env
```

Example:

```ini
HEALTH_COACH_LLM_MODEL_PATH=/opt/health-coach/data/models/llm/qwen3.5-0.8b-q4_0.gguf
HEALTH_COACH_LLM_MODEL=health-coach-local
```

Backend configuration lives in `/etc/health-coach/backend.env`:

```ini
HEALTH_COACH_LLM_ENABLED=1
HEALTH_COACH_LLM_BASE_URL=http://127.0.0.1:8080
HEALTH_COACH_LLM_MODEL=health-coach-local
HEALTH_COACH_LLM_TIMEOUT_SECONDS=15
```

`health-coach-llm.service` starts `llama-server` on loopback. The API uses the LLM only as an optional dependency (`Wants`, not a hard functional dependency). If the LLM is disabled, unavailable, times out or returns unusable text, deterministic wording remains available.

## Verify the runtime

```bash
/usr/local/bin/llama-server --version
curl http://127.0.0.1:8080/v1/models
systemctl status health-coach-llm.service
journalctl -u health-coach-llm.service -f
```

The LLM must not be exposed directly to the LAN; FastAPI remains the integration/control boundary.

## Architecture rule

```text
Deterministic planner / coaching engine
        -> explicit facts + reason codes
        -> CoachMessageContext
        -> optional LocalLlmCoachMessageGenerator
        -> text

On any LLM problem:
        -> FallbackCoachMessageGenerator
```

Do not pass unrestricted persistence/domain internals to the model and do not use model output as the authoritative source for training or health facts.
