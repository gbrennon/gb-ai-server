# CDI Benchmark: GPU vs CPU for Local Llama Inference

**Model:** Qwen3-14B Q4_K_M (9.0 GB)
**Hardware:** NVIDIA GeForce RTX 5070 (12 GB VRAM), AMD Ryzen 7 7700X (64 GB RAM)
**Server:** llama.cpp server-cuda (`ghcr.io/ggml-org/llama.cpp:server-cuda`)

## Context Window Limits

Tested Qwen3-14B Q4_K_M with N_GPU_LAYERS=999 (all layers on GPU):

| CTX_SIZE | VRAM Used | Tokens/sec | Status |
|----------|-----------|------------|--------|
| 16384 | 6.4 GB | 118 | OK |
| 20480 | 6.4 GB | 129 | OK |
| 24576 | 6.7 GB | 126 | OK |
| **28672** | **7.1 GB** | **128** | **OK (recommended)** |
| 32768 | — | — | OOM — CUDA malloc fails for KV cache |
| 40960 | — | — | OOM — auto-detected model max |

**Finding:** The model's native context window is 40960, but at 999 GPU layers
the KV cache allocation for 32768+ tokens exceeds 12 GB VRAM. Stable max is 28672.

Container exits with code 139 (SIGSEGV) when CUDA OOM occurs — the error is
`cudaMalloc failed: out of memory` in the llama.cpp server logs.

## Fit-Check Formula

The fit check is dynamic — works on any hardware by probing at runtime:

1. **VRAM:** `nvidia-smi --query-gpu=memory.free` — read at runtime
2. **Model size:** HF API (`model_info.siblings.size`) or local file (`os.path.getsize`)
3. **KV cache:** Reads GGUF metadata (`n_layers`, `n_embd`, `n_kv_heads`)
   from the GGUF binary header. Model-specific, not hardcoded.
   - GGUF keys use model-specific prefixes (e.g. `qwen3.block_count`, not `llama.block_count`)
   - KV cache = `2 * n_layers * n_kv_heads * head_dim * 2 (fp16)` per token
   - Realistic: Q8_0 quantization (0.5x) + rolling buffer (0.05x of full context)
4. **Total VRAM needed:** `model_size + kv_cache + 0.5` (CUDA overhead)
5. **Fallback** (no GGUF): `kv_cache = max(0.5, ctx * 0.00001)` GB

### Quantization Auto-Selection

The HF resolver picks the best quantization that fits VRAM:
- Q4_K_M > Q4_K_S > Q3_K_M > Q2_K (descending quality)
- BF16/F16 excluded when VRAM < 24 GB (raw unquantized, 4x larger than Q4)
- If Q4_K_M doesn't fit, automatically downgrades to Q3_K_M or Q2_K

## GPU vs CPU Performance

| Mode | N_GPU_LAYERS | Tokens/sec | VRAM | CPU |
|------|-------------|-----------|------|-----|
| Full GPU | 999 | 108-129 | 7.0 GB | <5% |
| Pure CPU | 0 | 4.7 | 0 | ~200% |
| Hybrid (broken) | 10 | 0.34 | 5.2 GB | 117% |

Full GPU is **25x faster** than CPU. Hybrid mode (10 GPU layers) is actively
harmful — PCIe transfer overhead makes it slower than pure CPU.

## CDI

```bash
make check-cdi
# Found 3 CDI devices: nvidia.com/gpu=0, gpu=all, gpu=GPU-{uuid}
# GPU accessible via CDI
```

Required for GPU access. `nvidia-cdi-refresh.service` being inactive is harmless —
it only auto-refreshes definitions on driver updates. Current CDI device
definitions persist until the next driver update. If definitions are lost,
run `nvidia-ctk cdi generate`.

## Debugging Container Crashes

```bash
# Check exit code
podman ps -a --filter name=llama-coder --format '{{.Status}}'
# Exit 139 = SIGSEGV (CUDA OOM or model loading error)

# Check logs
podman logs llama-coder | grep -i "error\|fail\|oom\|cuda"

# Key error patterns:
#   cudaMalloc failed: out of memory  → reduce ctx_size or gpu_layers
#   failed to open GGUF file           → model not in /models/ volume
#   failed to fit params               → model too large for VRAM
```
