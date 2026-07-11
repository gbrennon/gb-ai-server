# Bootstrap Flow

What happens when you run `make bootstrap` or `gb-ai-server`.

## Pipeline

```
.models.yaml  →  parse  →  resolve  →  download  →  start  →  health  →  register
```

## Step by Step

### 1. Parse `.models.yaml`

Reads the model configuration:

```yaml
model:
  id: unsloth/Qwen3-14B-GGUF
  file: Qwen3-14B-Q4_K_M.gguf
  gpu_layers: 999
```

If `file` is omitted, the best quantization is auto-detected from HuggingFace.

### 2. Resolve from HuggingFace

When `file` is not specified, the resolver:

1. Lists all `.gguf` files in the HF repo via `huggingface_hub.list_repo_files()`
2. Ranks quantizations by quality: Q4_K_M > Q4_K_S > Q3_K_M > Q2_K
3. Excludes BF16/F16 on GPUs with less than 24 GB VRAM
4. Selects the highest quality that fits in available VRAM
5. Resolves the download URL automatically

### 3. Hardware Probe

Reads GPU info via `nvidia-smi --query-gpu=name,memory.total,memory.free` and
system RAM from `/proc/meminfo`. Used for fit-check before downloading.

### 4. Compute Safe Context Window

Uses `huggingface_hub.hf_hub_download()` to fetch the model's `config.json`,
extracting `num_hidden_layers`, `num_key_value_heads`, `head_dim`, and
`max_position_embeddings`. The KV cache cost per token is:

```
bytes_per_token = 2 × n_layers × n_kv_heads × head_dim × 2  (fp16 K+V)
```

Then divides available VRAM by this cost to find the largest context that fits.

### 5. Write Environment

The resolved values are written to `.env`:

```
LLAMA_MODEL=Qwen3-14B-Q4_K_M.gguf
N_GPU_LAYERS=999
CTX_SIZE=12288
```

These are consumed by `podman-compose` when starting the container.

### 6. Download Model

Downloads the GGUF file from HuggingFace using `huggingface_hub.hf_hub_download()`.
Supports accelerated downloads via `hf_transfer`. Falls back to `curl` if the
HF library is unavailable.

### 7. Prerequisites Check

Verifies the container runtime (Podman/Docker), compose tool, and GPU access
before starting.

### 8. Start Container

Stops any existing container, then runs `podman-compose up -d`.
The container uses the image `ghcr.io/ggml-org/llama.cpp:server-cuda` (GPU)
or `ghcr.io/ggml-org/llama.cpp:server` (CPU).

### 9. Copy Model

Copies the downloaded GGUF file into the running container's `/models/`
directory via `podman cp`.

### 10. Restart Container

Restarts the container so llama.cpp loads the newly copied model.

### 11. Health Check

Polls `http://localhost:8081/health` until the server responds healthy.
The container healthcheck is configured with 3s intervals and 10 retries.

### 12. Register with Agents

Registers the running model with all supported AI coding agents.
See `docs/agent-registration.md` for details.

## Dry Run

```bash
make bootstrap-dry
# or
gb-ai-server --dry-run
```

Prints what would happen without making any changes.

## Skip Steps

```bash
gb-ai-server --skip-download         # assume model already downloaded
gb-ai-server --skip-health           # skip health verification
gb-ai-server --skip-download --skip-health  # both
```
