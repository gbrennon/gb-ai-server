# Adding a Model

Models are configured in `.models.yaml` at the repo root. The server runs
**one model at a time**.

## Quick Start

```yaml
# .models.yaml
model:
  id: unsloth/Qwen3-14B-GGUF
```

That's it. Everything else — file name, download URL, context window —
is auto-detected from HuggingFace.

## Configuration Fields

| Field | Required | Default | Description |
|-------|----------|---------|-------------|
| `id` | yes | — | HuggingFace repo ID (must be a GGUF-quantized repo) |
| `file` | no | auto | Specific GGUF file to use |
| `gpu_layers` | no | 999 | GPU layers to offload (999 = all) |
| `ctx_size` | no | 0 | Context window (0 = auto-detect from GGUF metadata) |

## Finding a Model

### Step 1: Find a GGUF repo on HuggingFace

GGUF repos follow the pattern `{org}/{model-name}-GGUF`. Popular sources:
- `unsloth` — [huggingface.co/unsloth](https://huggingface.co/unsloth)
- `bartowski` — [huggingface.co/bartowski](https://huggingface.co/bartowski)
- `Qwen` — [huggingface.co/Qwen](https://huggingface.co/Qwen)

Example GGUF repos:
```
unsloth/Qwen3-14B-GGUF
unsloth/DeepSeek-V4-Pro-GGUF
bartowski/mistralai_Devstral-Small-2-24B-Instruct-2512-GGUF
Qwen/Qwen2.5-Coder-7B-Instruct-GGUF
```

### Step 2: Copy the repo ID into `.models.yaml`

```yaml
model:
  id: unsloth/DeepSeek-V4-Pro-GGUF
```

### Step 3: Run bootstrap

```bash
make bootstrap
```

The application will:
1. List available GGUF files in the repo
2. Select the best quantization for your GPU (Q4_K_M preferred)
3. Fetch the context window from the model's config
4. Check if the model fits in available VRAM
5. Download only if it fits
6. Start the inference server

## Auto-Detection

When only `id` is set, the resolver:

1. **Lists files** — queries HuggingFace for all `.gguf` files in the repo
2. **Picks quantization** — selects the best quality that fits GPU VRAM:
   - Priority: Q4_K_M > Q4_K_S > Q3_K_M > Q2_K
   - Falls back to smaller quants if VRAM is limited
3. **Gets context window** — reads `config.json` from the repo, then local GGUF metadata
4. **Checks fit** — probes GPU VRAM and system RAM before downloading

## Picking a Specific File

To use a specific GGUF file (e.g. for a particular quantization):

```yaml
model:
  id: unsloth/DeepSeek-V4-Pro-GGUF
  file: DeepSeek-V4-Pro-Q4_K_M.gguf
```

The `file` field overrides auto-detection. The download URL is
automatically built from `id` and `file`.

## Context Window

The application reads the context window from:
1. GGUF binary metadata (`llama.context_length` key)
2. HuggingFace `config.json` (`max_position_embeddings`)
3. Environment variable `CTX_SIZE`
4. Default: 8192

Set it explicitly to override auto-detection:

```yaml
model:
  id: unsloth/Qwen3-14B-GGUF
  ctx_size: 32768
```

Set to `0` (default) to auto-detect.

## GPU Layers

```yaml
model:
  id: unsloth/Qwen3-14B-GGUF
  gpu_layers: 999   # all layers on GPU
```

- `999` — all layers on GPU (requires enough VRAM)
- `0` — CPU only
- Partial — e.g. `20` for 20 layers on GPU, rest on CPU

The model's size and your GPU VRAM determine how many layers fit.
The fit check warns if the model won't fit before downloading.

## Bootstrap

```bash
make bootstrap           # full: download + start + health check
make bootstrap-quick     # skip download and health check
make bootstrap-dry       # preview without changes
```

## Registration

After the server is running, register the model with AI coding tools
so they can use it via the OpenAI-compatible API:

```bash
make bootstrap-register  # from .models.yaml

# Or register a specific HF model:
make register HF_MODEL=unsloth/Qwen3-14B-GGUF
```

This adds the model to OpenCode, Mistral Vibe, Pi, and Cline.

## Common Errors

**"Repo has no GGUF files"**

You used a non-GGUF repo ID. Append `-GGUF` to the model name:
```yaml
# Wrong
model:
  id: unsloth/DeepSeek-V4-Pro

# Correct
model:
  id: unsloth/DeepSeek-V4-Pro-GGUF
```

**"Model does not fit on this hardware"**

The model is too large for your GPU VRAM. Options:
- Pick a smaller quantization by specifying `file`
- Use a smaller model
- Reduce `gpu_layers`

**Container crashes (exit code 139)**

The model loads but CUDA runs out of memory for the KV cache.
Reduce `ctx_size` — each model has a max context that fits in VRAM.

```bash
podman logs llama-coder | grep -i "error\|oom\|cuda"
# cudaMalloc failed: out of memory → reduce ctx_size
# failed to open GGUF file → model not in volume
```

**Health check retries indefinitely**

The container keeps restarting and failing. Common causes:
- `ctx_size` too large for available VRAM
- Model file missing from /models/ volume
- GPU not accessible (run `make check-cdi`)

**BF16/F16 selected instead of Q4_K_M**

The resolver picked the unquantized weights. These are excluded
on GPUs < 24 GB VRAM. If it still happens, add explicit `file:`:

```yaml
model:
  id: unsloth/Qwen3-14B-GGUF
  file: Qwen3-14B-Q4_K_M.gguf
```

## Fit Check Internals

The fit check runs before any download and uses dynamic hardware probing:

| Component | Source | Notes |
|-----------|--------|-------|
| VRAM free | nvidia-smi --query-gpu | Runtime on any GPU |
| Model size | HF API or local file | HF model_info.siblings.size |
| KV cache | GGUF binary metadata | Reads n_layers, n_embd, n_kv_heads |
| Context | GGUF or config.json | max_position_embeddings |

GGUF metadata uses model-specific key prefixes (e.g. qwen3.block_count),
matched by suffix for cross-architecture compatibility.
## Gated Repositories

Models requiring authentication need a HuggingFace token:

```bash
make bootstrap HF_TOKEN=hf_...
# or set in .env:
HF_TOKEN=hf_...
```
