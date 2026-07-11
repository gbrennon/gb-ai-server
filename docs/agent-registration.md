# Agent Registration

How models are registered with AI coding agents after bootstrap.

## Overview

After the llama.cpp server is running, `make bootstrap-register` writes
the model's connection details into each agent's configuration files.
The agents then see the model as a local OpenAI-compatible provider.

## Registration Pipeline

```
server running  →  discover templates  →  probe /props  →  write configs  →  agent sees model
```

## Template System

Agent registration uses a plugin architecture. Each agent is a single Python
file in `src/gb_ai_server/infrastructure/persistence/templates/`.

| File | Agent | Config written |
|------|-------|---------------|
| `cline.py` | Cline | `~/.cline/data/settings/{providers,models,globalState,secrets}.json` |
| `opencode.py` | OpenCode | `opencode.json` (project root) |
| `vibe.py` | Mistral Vibe | `~/.vibe/config.toml` |
| `pi.py` | Pi | `~/.pi/agent/models.json` |

Each file implements:

```python
def register(display_name: str, container_name: str, ctx_size: int, port: int = 8081) -> bool:
    ...
```

Return `True` on success, `False` if the agent is not installed (silently skipped).

## Context Window Probing

Before writing agent configs, the server's actual `n_ctx` is read from
`http://localhost:8081/props`. This is the ground truth — what the container
actually started with. If the server isn't reachable, falls back to the
value computed by `fetch_safe_ctx_size()` from HF config data.

## Provider Identity

| Agent | Provider name | Base URL |
|-------|--------------|----------|
| Cline | `local llama.cpp` | `http://localhost:8081/v1` |
| OpenCode | `local llama.cpp` | `http://localhost:8081/v1` |
| Vibe | `local llama.cpp` | `http://localhost:8081` |
| Pi | `llama.cpp` | `http://localhost:8081/v1` |

## Model ID Format

The HuggingFace repo ID is transformed into a model identifier:

```
unsloth/Qwen3-14B-GGUF  →  unsloth-qwen3-14b-gguf
```

`/` becomes `-`, everything is lowercased.

## Per-Agent Details

### Cline

Writes four JSON files in `~/.cline/data/`:

- `settings/providers.json` — provider entry with base URL and API key
- `settings/models.json` — model catalog with context window
- `globalState.json` — active provider and model selection (kebab + camelCase)
- `secrets.json` — API key

After registration, reload VSCode (`Ctrl+Shift+P` → "Developer: Reload Window")
and confirm the provider is "local llama.cpp".

### OpenCode

Writes `opencode.json` in the project root (directory containing `.git/`).

```json
{
  "provider": {
    "local llama.cpp": {
      "npm": "@ai-sdk/openai-compatible",
      "name": "Llama Coder (local)",
      "options": { "baseURL": "http://localhost:8081/v1" },
      "models": {
        "unsloth-qwen3-14b-gguf": {
          "name": "Qwen3-14B-GGUF",
          "limit": { "context": 12288, "output": 12288 }
        }
      }
    }
  }
}
```

Select the model in the OpenCode TUI or via `opencode --model "local llama.cpp/<id>"`.

### Mistral Vibe

Writes `~/.vibe/config.toml` with TOML sections for provider and model.
Replaces existing `local llama.cpp` model entries but preserves models
from other providers.

### Pi

Writes `~/.pi/agent/models.json` and `~/.pi/agent/auth.json`.
Probes the server's `/props` endpoint for the actual `n_ctx` before writing.
No manual model selection required — Pi reads the config at startup.

## Adding a New Agent

Create a Python file in `src/gb_ai_server/infrastructure/persistence/templates/<name>.py`
with a `register` function. It is auto-discovered via `pkgutil` and called
on every registration run.
