# Context Window

How the application determines the context window size for a model.

## Source of Truth

The HuggingFace Hub library is the single source of truth. The application
downloads `config.json` from the model's HF repo via `huggingface_hub` and
extracts the architecture parameters:

| Field | Purpose |
|-------|---------|
| `num_hidden_layers` | Number of transformer layers (n_layers) |
| `num_key_value_heads` | KV attention heads (n_kv_heads) |
| `num_attention_heads` | Total attention heads |
| `head_dim` | Dimension per head |
| `hidden_size` | Used to derive head_dim if not explicit |
| `max_position_embeddings` | Native maximum context |

## KV Cache Formula

Each token consumes memory for the Key and Value tensors (fp16):

```
bytes_per_token = 2 × n_layers × n_kv_heads × head_dim × 2
                   ^                            ^           ^
                   K+V tensors                 fp16       bytes
```

### Example: Qwen3-14B

```
n_layers        = 40
n_kv_heads      = 8
head_dim        = 128
bytes_per_token = 2 × 40 × 8 × 128 × 2 = 163,840 bytes (0.156 MiB)
```

## Safe Context Computation

```python
from gb_ai_server.infrastructure.persistence.fetch_hf_ctx import fetch_safe_ctx_size

fetch_safe_ctx_size("unsloth/Qwen3-14B-GGUF")
```

This function:

1. Loads `config.json` from HuggingFace
2. Finds the local GGUF file to get its size on disk
3. Probes GPU total VRAM via `nvidia-smi`
4. Computes `available_for_kv = vram_total - model_size - 1024 MiB margin`
5. Computes `max_ctx = available_for_kv / mb_per_token`
6. Clamps to `max_position_embeddings` and aligns to 256-token boundary

### Real Numbers (RTX 5070, 12 GB)

| Component | Value |
|-----------|-------|
| Total VRAM | 12,227 MiB |
| Model (Q4_K_M) | 8,584 MiB |
| Safety margin | 1,024 MiB |
| Available for KV | 2,619 MiB |
| KV cost per token | 0.156 MiB |
| Max safe context | 16,384 tokens |

## Fallbacks

If `config.json` is unavailable:
1. `model_info.card_data` from HuggingFace Hub API
2. Local GGUF binary metadata (`llama.context_length` key)
3. Conservative default: 8,192

## No Env Var Dependency

The application does not rely on `CTX_SIZE` environment variable for context
window computation. The HF library is always consulted first. The `CTX_SIZE`
env var is written during bootstrap only as a container startup parameter and
is regenerated from HF data on every run.

## Increasing Context on GPU

Free VRAM for KV cache by reducing GPU layers:

```yaml
model:
  id: unsloth/Qwen3-14B-GGUF
  gpu_layers: 20
```

Fewer layers on GPU means more VRAM available for context.

## Increasing Context on CPU

Set `CTX_SIZE` in `.env` and restart:

```bash
echo "CTX_SIZE=32768" >> .env
make bootstrap-cpu-container
```

CPU mode uses system RAM which is typically much larger than VRAM.
