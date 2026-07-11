# Using llama.cpp Models in AI Coding Agents

This document explains what you need to do in each supported agent to use the
models that are registered and served by this project's llama.cpp server.

---

## How Registration Works

When you run:

```bash
make bootstrap-register
# or
make register HF_MODEL=org/repo
```

The system automatically writes the active model's connection details into
**every supported agent's configuration files**. After that, the model is
immediately available without any manual steps.

The registration pipeline:
1. Derives a `container_name` from the HuggingFace repo ID
   (e.g. `unsloth/Qwen3-14B-GGUF` → `unsloth-qwen3-14b-gguf`)
2. Resolves the context window from the GGUF binary metadata or HuggingFace
   `config.json`
3. Writes agent-specific config files pointing to `http://localhost:8081/v1`
   (OpenAI-compatible API)

---

## What Each Agent Needs

### Cline

**Config files written automatically:**

| File | Purpose |
|------|---------|
| `~/.cline/data/settings/providers.json` | Provider URL and API key |
| `~/.cline/data/settings/models.json` | Model catalog with context window |
| `~/.cline/data/globalState.json` | Active provider and model selection |
| `~/.cline/data/secrets.json` | API key storage |

**What registration sets:**

- **Provider:** `local llama.cpp` (type: `openai-compatible`)
- **Base URL:** `http://localhost:8081/v1`
- **Model ID:** e.g. `unsloth-qwen3-14b-gguf`
- **API Key:** value of `OPENAI_API_KEY` env var (defaults to `dummy`)

**After registration — verify in Cline:**

1. Open VSCode with Cline installed
2. Open the Cline panel → click the provider selector (top of the panel)
3. Confirm the active provider is **"local llama.cpp"**
4. Confirm the active model is the `container_name` that was registered
   (e.g. `unsloth-qwen3-14b-gguf`)

**If Cline doesn't pick up the new model automatically:**

- Reload VSCode (`Ctrl+Shift+P` → "Developer: Reload Window")
- Or switch providers manually in the Cline UI and select the model from the dropdown

> **Note:** Cline reads `~/.cline/data/` — if you use a non-standard
> installation path, set `CLINE_DATA_DIR` in `.env` before registering.

---

### OpenCode

**Config files written automatically:**

| File | Purpose |
|------|---------|
| `opencode.json` (project root) | Provider and model definitions |
| `~/.local/share/opencode/auth.json` | API key for the provider |

**What registration sets in `opencode.json`:**

```json
{
  "$schema": "https://opencode.ai/config.json",
  "provider": {
    "local llama.cpp": {
      "npm": "@ai-sdk/openai-compatible",
      "name": "Llama Coder (local)",
      "options": {
        "baseURL": "http://localhost:8081/v1"
      },
      "models": {
        "unsloth-qwen3-14b-gguf": {
          "name": "Qwen3-14B-GGUF",
          "limit": {
            "context": 20480,
            "output": 20480
          }
        }
      }
    }
  }
}
```

**After registration — select the model in OpenCode:**

```bash
opencode
```

Then in the OpenCode TUI:
1. Press the model selector key (usually `/` or `m`)
2. Navigate to **"local llama.cpp"** provider
3. Select the registered model (e.g. `Qwen3-14B-GGUF`)

Or pass it via flag:

```bash
opencode --model "local llama.cpp/unsloth-qwen3-14b-gguf"
```

> **Note:** `opencode.json` is placed in the **project root** (the directory
> containing `.git/`). Run the registration command from inside a Git
> repository to ensure the file lands in the right place.

---

### Mistral Vibe

**Config files written automatically:**

| File | Purpose |
|------|---------|
| `~/.vibe/config.toml` | Provider and model definitions |
| `~/.vibe/.env` | `OPENAI_API_KEY` for the local provider |

**What registration writes to `~/.vibe/config.toml`:**

```toml
[[providers]]
name = "local llama.cpp"
api_base = "http://localhost:8081"
api_key_env_var = "OPENAI_API_KEY"
api_style = "openai"
backend = "generic"

[[models]]
name = "unsloth-qwen3-14b-gguf"
provider = "local llama.cpp"
alias = "Qwen3-14B-GGUF"
temperature = 0.2
input_price = 0.0
output_price = 0.0
thinking = "off"
supports_images = false
auto_compact_threshold = 20480
```

**After registration — select the model in Vibe:**

```bash
vibe
```

Then in the Vibe UI, open the model picker and select the model by its `alias`
(e.g. `Qwen3-14B-GGUF`) or `name` (`unsloth-qwen3-14b-gguf`).

> **Note:** Registration **replaces** existing `local llama.cpp` model entries
> in `config.toml` but preserves models belonging to other providers.

---

### Pi

**Config files written automatically:**

| File | Purpose |
|------|---------|
| `~/.pi/agent/models.json` | Provider URL, API key, and model catalog |
| `~/.pi/agent/auth.json` | API key for the provider |

**What registration writes to `~/.pi/agent/models.json`:**

```json
{
  "providers": {
    "llama.cpp": {
      "baseUrl": "http://localhost:8081/v1",
      "apiKey": "dummy",
      "api": "openai-completions",
      "models": [
        {
          "id": "unsloth-qwen3-14b-gguf",
          "name": "Qwen3-14B-GGUF",
          "reasoning": false,
          "input": ["text"],
          "cost": { "input": 0, "output": 0, "cacheRead": 0, "cacheWrite": 0 },
          "contextWindow": 20480,
          "maxTokens": 20480
        }
      ]
    }
  }
}
```

> **Note:** Pi registration probes the running llama.cpp server at
> `http://localhost:8081/props` to read the **actual** `n_ctx` the server
> started with. If the server is not yet running, it falls back to the
> configured `ctx_size`. Always register **after** the server is up.

**After registration — select the model in Pi:**

Pi reads `models.json` at startup. The registered model appears automatically
under the `llama.cpp` provider — no manual selection required.

---

## Quick Reference

| Agent | Provider name | Base URL | Model ID format |
|-------|--------------|----------|-----------------|
| Cline | `local llama.cpp` | `http://localhost:8081/v1` | `{org}-{repo-name}` (lowercased, `/` → `-`) |
| OpenCode | `local llama.cpp` | `http://localhost:8081/v1` | same |
| Vibe | `local llama.cpp` | `http://localhost:8081` | same |
| Pi | `llama.cpp` | `http://localhost:8081/v1` | same |

**Model ID derivation example:**

```
HuggingFace repo ID:  unsloth/Qwen3-14B-GGUF
                       ↓
Model ID (agent key): unsloth-qwen3-14b-gguf
```

---

## Troubleshooting

### The model doesn't appear after registration

1. **Verify the server is running:**
   ```bash
   make status
   curl http://localhost:8081/v1/models
   ```

2. **Re-run registration:**
   ```bash
   make bootstrap-register
   ```

3. **Check the config files were written** for the agent you use:
   ```bash
   cat ~/.cline/data/settings/models.json        # Cline
   cat opencode.json                              # OpenCode (project root)
   cat ~/.vibe/config.toml                        # Vibe
   cat ~/.pi/agent/models.json                    # Pi
   ```

### The agent connects but gets errors

- **401 Unauthorized** — the agent requires a non-empty API key. Set
  `OPENAI_API_KEY` in `.env` before registering (any non-empty string works
  for llama.cpp).

- **"request exceeds the available context size"** — your agent is sending
  more tokens than the server's context window. Solutions:

  **GPU mode:** Reduce GPU layers to free VRAM for KV cache. Edit
  `.models.yaml`:

  ```yaml
  model:
    id: unsloth/Qwen3-14B-GGUF
    gpu_layers: 20
  ```

  Then restart:
  ```bash
  CTX_SIZE=16384 make down && CTX_SIZE=16384 make up
  make bootstrap-register
  ```

  **CPU mode:** Increase `CTX_SIZE` directly in `.env`:
  ```bash
  echo "CTX_SIZE=32768" >> .env
  make bootstrap-cpu-container
  ```

- **Model not found (404)** — llama.cpp serves exactly one model at a time.
  The model ID returned by `/v1/models` must match what the agent sends.
  Re-run registration to sync the ID.

### Changing models

1. Edit `.models.yaml` with the new HuggingFace repo
2. Run the full bootstrap:
   ```bash
   make bootstrap
   ```
   This downloads, starts, and re-registers the new model across all agents.

---

## Adding Support for a New Agent

Drop a Python file in:

```
src/gb_ai_server/infrastructure/persistence/templates/<agent_name>.py
```

Implement a single function:

```python
def register(display_name: str, container_name: str, ctx_size: int, port: int = 8081) -> bool:
    """Write agent-specific config. Return True on success, False if not installed."""
    ...
```

The template is **auto-discovered** via `pkgutil` and called on every
`make bootstrap-register` or `make register` run. Return `False` (not an
exception) if the agent is simply not installed on the machine — it will be
skipped silently. See the existing templates for reference:
`cline.py`, `opencode.py`, `vibe.py`, `pi.py`.
