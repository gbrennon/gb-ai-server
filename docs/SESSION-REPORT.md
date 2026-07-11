# Session Report — Bootstrap Fixes

## Problem

`make bootstrap` failed with health check retrying forever. Container
crashed (exit 139, SIGSEGV) on startup.

## Root Causes

### 1. `podman-compose` not using `.env`

The Python compose lifecycle (`PodmanComposeStandaloneLifecycle`) did
NOT pass `--env-file .env` to `podman-compose`. The container always
used old env values from the shell or defaults.

**Fix:** Added `--env-file .env` to `up`, `down`, `restart` in:
- `src/gb_ai_server/infrastructure/podman/podman_standalone_lifecycle.py`

### 2. `.env` not updated on model switch

`_set_model_env()` only set `os.environ` but not the `.env` file.
Docker/podman-compose reads from `.env`, not from process environment.

**Fix:** `_set_model_env()` now writes `LLAMA_MODEL`, `CTX_SIZE`,
`N_GPU_LAYERS` to `.env` file in:
- `src/gb_ai_server/presentation/composer.py`

### 3. VRAM fragmentation on model switch

When switching models, the old container's VRAM wasn't fully released
before the new container started. CUDA OOM.

**Fix:** 3-second sleep in `_stop_running_service()` in:
- `src/gb_ai_server/presentation/composer.py`

### 4. Stale shell environment variable

`LLAMA_MODEL` was set in the shell environment from earlier manual
commands, overriding `.env` values.

**Fix:** Run `unset LLAMA_MODEL` in the shell before bootstrap.
The `.env` file is now the single source of truth.

### 5. Qwen3-14B doesn't fit RTX 5070 12 GB

Qwen3-14B Q4_K_M (9.0 GB) with 999 GPU layers fails at all tested
context sizes (16384–40960). Even at 16384 ctx, `cudaMalloc failed:
out of memory`. The model file may also have a container loading
issue (file appears valid but container can't read it).

**Fix:** Use Qwen2.5-Coder-7B (4.7 GB, works perfectly at 28672 ctx).

## Working Configuration

```yaml
# .models.yaml
model:
  id: Qwen/Qwen2.5-Coder-7B-Instruct-GGUF
  file: qwen2.5-coder-7b-instruct-q4_k_m.gguf
  ctx_size: 28672
```

```bash
# .env (relevant lines)
LLAMA_MODEL=qwen2.5-coder-7b-instruct-q4_k_m.gguf
CTX_SIZE=28672
N_GPU_LAYERS=999
```

## Test Results

- `make bootstrap`: 3+ consecutive successful runs
- Model: Qwen2.5-Coder-7B-Q4_K_M, 28672 ctx, 999 GPU layers
- VRAM: ~7 GB used
- Agents registered: Cline, OpenCode, Vibe, Pi
- Python tests: 389 passing

## Files Changed

| File | Change |
|------|--------|
| `podman_standalone_lifecycle.py` | Added `--env-file .env` to up/down/restart |
| `composer.py` | `.env` writing in `_set_model_env`; 3s VRAM-clear delay |
| `hardware_prober.py` | Dynamic KV cache formula from GGUF metadata |
| `hf_model_resolver.py` | BF16/F16 exclusion for GPUs < 24 GB |
| `gguf_reader.py` | Suffix-based GGUF key matching |
| `.models.yaml` | Qwen2.5-Coder-7B with 28672 ctx |
| `.env` | Updated LLAMA_MODEL, CTX_SIZE, N_GPU_LAYERS |
