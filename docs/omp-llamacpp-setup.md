# omp + llama.cpp Local Model Setup

## Overview

omp (Oh My Pi — `can1357/oh-my-pi`) is configured to use the local **llama.cpp** server
running Qwen2.5-Coder-7B-Instruct (Q4_K_M) via Podman.

## Container

| Setting | Value |
|---|---|
| Image | `ghcr.io/ggml-org/llama.cpp:server-cuda` |
| Container | `llama-coder` |
| Runtime | Podman (rootless) |
| GPU | NVIDIA GeForce RTX 5070 (12 GB) |
| Host port | `127.0.0.1:8081` → container `:8080` |
| Model | `qwen2.5-coder-7b-instruct-q4_k_m.gguf` |
| Context | **65536** tokens |
| GPU layers | 999 (all) |

## omp Configuration

### `~/.omp/agent/models.yml` — Provider registration

```yaml
providers:
  llama.cpp:
    baseUrl: http://127.0.0.1:8081
    api: openai-responses
    auth: none
    discovery:
      type: llama.cpp

  # ⚠️ CRITICAL: The advisor subagent is hardcoded to use `openai/gpt-5.5`.
  # Override the openai provider to redirect its calls to the local
  # llama.cpp server (which accepts any model name and maps it to the
  # loaded model).
  openai:
    baseUrl: http://127.0.0.1:8081
    api: openai-responses
    auth: none
```

- **`auth: none`** — correct for unauthenticated local servers
- **`discovery.type: llama.cpp`** — auto-discovers models on startup via `/v1/models`
- **`openai` override** — redirects the advisor's `openai/gpt-5.5` calls to local llama.cpp

### `~/.omp/agent/config.yml` — Model roles

```yaml
modelRoles:
  plan:    llama.cpp/qwen2.5-coder-7b-instruct-q4_k_m.gguf   # Architecture planning
  task:    llama.cpp/qwen2.5-coder-7b-instruct-q4_k_m.gguf   # Subagent work
  smol:    llama.cpp/qwen2.5-coder-7b-instruct-q4_k_m.gguf   # Advisor / fast reviews
  default: openrouter/deepseek/deepseek-v4-pro                # Main implementation
  slow:    opencode-zen/minimax-m2.5-free                     # Deep reasoning

advisor:
  enabled: true
  subagents: true
  syncBacklog: "1"
  model: llama.cpp/qwen2.5-coder-7b-instruct-q4_k_m.gguf

task:
  agentModelOverrides:
    task: llama.cpp/qwen2.5-coder-7b-instruct-q4_k_m.gguf
```

### Role breakdown

| Role | Model | Purpose |
|---|---|---|
| `plan` | llama.cpp (local) | Plan mode architecture |
| `task` | llama.cpp (local) | Subagent work |
| `smol` | llama.cpp (local) | **Advisor reviews**, title gen, classification |
| `default` | OpenRouter DeepSeek V4 | Main coding work |
| `slow` | OpenCode Zen MiniMax | Deep reasoning |

## Commands

```bash
# Bootstrap (start + register)
make bootstrap

# Or manually:
LLAMA_MODEL=qwen2.5-coder-7b-instruct-q4_k_m.gguf \
CTX_SIZE=65536 \
N_GPU_LAYERS=999 \
  podman-compose -f docker-compose.yml up -d

# Test omp with local model
omp -p --model llama.cpp/qwen2.5-coder-7b-instruct-q4_k_m.gguf "hello"

# Run with advisor
omp --advisor --smol llama.cpp/qwen2.5-coder-7b-instruct-q4_k_m.gguf

# Check container
podman logs -f llama-coder
curl http://localhost:8081/health
```

## ⚠️ Known Issue: Sampling Parameters for GGUF Models

The default omp sampling params (`temperature: 0.2, topP: 0.1, repetitionPenalty: -1`)
cause **repetition loops** with llama.cpp GGUF models. The model gets stuck repeating
the same phrase indefinitely.

**Fix:** Use GGUF-friendly sampling params:

```yaml
temperature: 0.7
topP: 0.9
topK: 40
minP: 0.05
presencePenalty: 0
repetitionPenalty: 1.1
```

Also disable `plan.defaultOnStartup` — the 7B model gets confused by plan mode protocol:
```yaml
plan:
  defaultOnStartup: false
```

The `fetch_safe_ctx_size()` function in `src/gb_ai_server/infrastructure/persistence/fetch_hf_ctx.py`
reads `max_position_embeddings` from the HF config.json (32768 for Qwen2.5-Coder-7B base) and clamps
to that value. The GGUF model actually supports **131072** tokens (`n_ctx_train`).

**Workaround:** Set `CTX_SIZE=65536` in `.env` before running bootstrap, and pass it explicitly:

```bash
CTX_SIZE=65536 LLAMA_MODEL=qwen2.5-coder-7b-instruct-q4_k_m.gguf make bootstrap
```

## Cline API Key Investigation

### Finding
The Cline API key (`sk_e0ac...`) is an OpenRouter-compatible key:
- ✅ `/api/v1/models` — works, returns full catalog
- ❌ `/api/v1/chat/completions` — returns `401 Missing Authentication header`

**Likely cause:** Cline keys may require Cline's own proxy endpoint (not raw OpenRouter)
or additional headers (HTTP-Referer, X-Title). OpenRouter free-tier keys can list models
but not make chat requests without payment method.

### Workaround
Use the existing `OPENROUTER_KEY` env var (`sk-or-v1-...`) which already works.
The Cline key might work through Cline's internal proxy but its endpoint is not publicly
documented.

```bash
# Existing key (working):
OPENROUTER_KEY=sk-or-v1-131a41139a2cb0654149e6fb...

# Cline key (models only):
CLINE_API_KEY=sk_e0ac...
```

All tests passed with advisor enabled:

| # | Prompt | Result |
|---|---|---|
| 1 | "Say pong" | `pong` |
| 2 | "2+2=?" | `4` |
| 3 | "Write a haiku" | 3-line haiku |
| 4 | "Count 1 to 5" | `1 2 3 4 5` |
| 5 | JSON prompt | Valid JSON |
| 6 | "Explain project structure" | Correct analysis |
| 7 | With `--advisor`, "Say ok" | `Ok` ✅ |
| 8 | With `--advisor`, "Count 1-3" | `1 2 3` ✅ |

## No Subagents with Local GGUF

The Qwen2.5-Coder GGUF model outputs tool calls as XML tags
(`<function name="...">`) instead of OpenAI's JSON `tool_calls` array.
llama.cpp doesn't translate between the two, so omp subagents/tools
**don't work with the local model**.

**Fix:** Route `task`/`default` roles to OpenRouter (which supports
proper tool calling), keep local model for non-tool work:

```yaml
modelRoles:
  plan:    llama.cpp/qwen2.5-coder-7b-instruct-q4_k_m.gguf  # no tools needed
  smol:    llama.cpp/qwen2.5-coder-7b-instruct-q4_k_m.gguf  # lightweight
  advisor: llama.cpp/qwen2.5-coder-7b-instruct-q4_k_m.gguf  # review only
  task:    openrouter/deepseek/deepseek-v4-pro               # subagents/tools
  default: openrouter/deepseek/deepseek-v4-pro               # main work
```

## Advisor Fix

The omp advisor subagent is **hardcoded** to use `openai/gpt-5.5` regardless of
`modelRoles`. To make it use the local model, the `openai` provider must be
overridden in `models.yml` to point at the local llama.cpp server.

llama.cpp's server accepts any model name and automatically maps it to the
loaded model, so `gpt-5.5` requests are served by `qwen2.5-coder-7b`.
