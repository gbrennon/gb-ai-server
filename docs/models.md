# Available Models

Reference of models tested or discoverable via HuggingFace.
Copy the `id` into `.models.yaml` to use.

## Working (tested on RTX 5070 12 GB)

### Qwen3 14B

| Field | Value |
|-------|-------|
| GGUF repo | `unsloth/Qwen3-14B-GGUF` |
| File | `Qwen3-14B-Q4_K_M.gguf` |
| Parameters | 14B |
| Quantization | Q4_K_M |
| Size | 9.0 GB |
| Max context (native) | 40,960 |
| Max context (12 GB VRAM) | 28,672 |
| VRAM at 28672 ctx | 7.1 GB |
| Speed | 108-129 t/s |
| Status | Stable |

```yaml
# .models.yaml
model:
  id: unsloth/Qwen3-14B-GGUF
  file: Qwen3-14B-Q4_K_M.gguf
  ctx_size: 28672
```

Context limits tested:

| ctx_size | Fits? |
|----------|-------|
| 16384 | Yes |
| 20480 | Yes |
| 24576 | Yes |
| **28672** | **Yes (recommended)** |
| 32768 | No — CUDA OOM |
| 40960 | No — CUDA OOM |

### Qwen2.5 Coder 7B

| Field | Value |
|-------|-------|
| GGUF repo | `Qwen/Qwen2.5-Coder-7B-Instruct-GGUF` |
| Parameters | 7B |
| Size | 4.7 GB |
| Max context | 131,072 |
| Status | Fits easily |

```yaml
model:
  id: Qwen/Qwen2.5-Coder-7B-Instruct-GGUF
```

## Mistral Devstral Small 2 (24B)

| Field | Value |
|-------|-------|
| Original | `mistralai/Devstral-Small-2-24B-Instruct-2512` |
| GGUF repo | `bartowski/mistralai_Devstral-Small-2-24B-Instruct-2512-GGUF` |
| Architecture | mistral3 |
| Parameters | 24B |
| Max context | 393,216 |
| License | Apache 2.0 |

**Quantizations available (bartowski):**

| Quant | Approx Size | Fits 12 GB? |
|-------|------------|-------------|
| bf16 | ~48 GB | No |
| Q8_0 | ~25 GB | No |
| Q6_K, Q6_K_L | ~18 GB | No |
| Q5_K_L, Q5_K_M, Q5_K_S | ~15 GB | No |
| Q4_K_L, Q4_K_M, Q4_K_S | ~14 GB | No |
| Q4_0, Q4_1 | ~13 GB | No |
| Q3_K_L, Q3_K_XL | ~11 GB | Edge |
| Q3_K_M, Q3_K_S | ~9 GB | Yes |
| IQ4_NL, IQ4_XS | ~11 GB | Edge |
| IQ3_M, IQ3_XS, IQ3_XXS | ~8 GB | Yes |
| IQ2_M, IQ2_S | ~6 GB | Yes |
| IQ2_XS, IQ2_XXS | ~5 GB | Yes |
| Q2_K, Q2_K_L | ~6 GB | Yes |

**For 12 GB VRAM:** use Q3_K_M or smaller. The auto-resolver will pick
Q2_K when Q4_K_M doesn't fit.

```yaml
model:
  id: bartowski/mistralai_Devstral-Small-2-24B-Instruct-2512-GGUF
  file: mistralai_Devstral-Small-2-24B-Instruct-2512-Q3_K_M.gguf
```

## DeepSeek V4 Pro

| Field | Value |
|-------|-------|
| Original | `deepseek-ai/DeepSeek-V4-Pro` |
| Architecture | Mixture of Experts (MoE), 1.6T total params |
| License | MIT |
| Downloads | 1.3M |

**GGUF repos:**

| Repo | Downloads | Notes |
|------|-----------|-------|
| `teamblobfish/DeepSeek-V4-Pro-GGUF` | 4,768 | Main community quant |
| `batiai/DeepSeek-V4-Pro-GGUF` | 573 | Alternative quant |
| `unsloth/DeepSeek-V4-Pro-GGUF` | — | Not published (401) |

**Does not fit consumer GPUs.** 1.6T MoE means even Q2_K is 80-100+ GB.
Use cloud inference providers (Together, Fireworks, Novita, DeepInfra).

## How Model Info Is Resolved

1. **Files:** `huggingface_hub.list_repo_files()` — lists all `.gguf` files
2. **Sizes:** `huggingface_hub.model_info().siblings` — API returns file sizes;
   falls back to estimation: `params * 2 GB (BF16) * quantization_ratio`
   where param count is extracted from repo name (e.g. `14B`)
3. **Context:** `config.json` from repo → `max_position_embeddings`;
   falls back to GGUF binary metadata (`*.context_length` key)
4. **Hardware:** `nvidia-smi --query-gpu` at runtime — dynamic, works on any GPU
5. **Quantization selection:** fits-in-VRAM first, then quality;
   BF16/F16 excluded when VRAM < 24 GB

## How to Find More Models

1. Search HuggingFace for `{model-name}-GGUF`
2. Popular quantizers: `unsloth`, `bartowski`, `lmstudio-community`
3. GGUF repos always end with `-GGUF`
4. Non-GGUF repos (e.g. `deepseek-ai/DeepSeek-V4-Pro`) contain the
   original weights — append `-GGUF` or search for community quants
5. Paste the repo ID into `.models.yaml` and run `make bootstrap`
