# Session Changes

## Architecture

**Moved all app code from `scripts/` to `src/gb_ai_server/`**
- `scripts/templates/` → `src/gb_ai_server/infrastructure/persistence/templates/`
- `scripts/fetch-hf-ctx.py` → `src/gb_ai_server/infrastructure/persistence/fetch_hf_ctx.py`
- Deleted: `scripts/register-hf-model.py`, `scripts/models.conf.sh`
- Remaining in scripts/: only benchmarks and legacy bash

## New Files

| File | Purpose |
|------|---------|
| `.models.yaml` | Model config (HF repo ID, optional file/ctx/gpu) |
| `persistence/hf_model_resolver.py` | Lists GGUF files, picks best quant, fetches context |
| `persistence/hardware_prober.py` | Probes GPU VRAM/RAM, fit-check |
| `persistence/gguf_reader.py` | Reads GGUF binary metadata (context, layers, embed dim) |
| `persistence/fetch_hf_ctx.py` | Fetch context window from HF config.json |
| `persistence/templates/` | Agent registration templates (cline, opencode, vibe, pi) |
| `application/services/register_custom_model_service.py` | Register model with all agents |
| `docker-compose.cpu.yml` | CPU-only override for benchmarking |
| `docs/models.md` | Available models reference |
| `docs/CHANGES.md` | This file |

## Key Fixes

1. **Fit-check KV cache formula** — was `ctx * 0.0005` (20 GB for 40960 ctx).
   Now dynamic: reads GGUF metadata (n_layers, n_embd) then Q8_0 (x0.5)
   + rolling buffer (x0.05). Matches observed VRAM usage.

2. **BF16/F16 exclusion** — Resolver now skips raw unquantized weights
   on GPUs < 24 GB VRAM. These are 4x larger than Q4 and never fit.

3. **VRAM-clear delay** — 3-second sleep in `_stop_running_service()`
   prevents CUDA OOM when switching models. Old model's VRAM must be
   fully released before new container starts.

4. **GGUF key names** — Keys are model-prefixed (e.g. `qwen3.block_count`,
   not `llama.block_count`). Reader uses suffix matching for compatibility.

5. **Single model** — Removed multi-model support. `.models.yaml` defines
   one model. No `--model` flag, no `--list-models`, no model selection.

6. **Emoji removal** — All emoji removed from CLI output and Makefile.

## Context Limits (RTX 5070 12 GB, Qwen3-14B Q4_K_M, 999 GPU layers)

| ctx_size | Fits? |
|----------|-------|
| 16384 | Yes |
| 20480 | Yes |
| 24576 | Yes |
| 28672 | Yes |
| 32768 | No — CUDA OOM |
| 40960 | No — CUDA OOM |

## Current Config

```yaml
# .models.yaml
model:
  id: unsloth/Qwen3-14B-GGUF
  file: Qwen3-14B-Q4_K_M.gguf
  gpu_layers: 999
  ctx_size: 28672
```

## Test Results

389 tests pass. `make bootstrap` succeeds end-to-end.
