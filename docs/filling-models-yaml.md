# How to Fill `.models.yaml` from a HuggingFace Page

## The File

```yaml
model:
  id: ORG/REPO          # required — HuggingFace repo ID (GGUF repos only)
  file: model.gguf      # optional — specific GGUF file to use
  gpu_layers: 999       # optional — GPU layers to offload (default 999)
  ctx_size: 0           # optional — 0 = auto-detect from model metadata
```

---

## Field-by-Field Guide

### `model.id` (required)

The HuggingFace **repository ID** — two segments separated by a slash.

**Where to find it:**

Look at the URL bar of the HuggingFace model page:

```
https://huggingface.co/Qwen/Qwen2.5-Coder-7B-Instruct-GGUF
                    └──────────┬──────────┘
                         model.id
```

Or the top of the page:

```
Qwen / Qwen2.5-Coder-7B-Instruct-GGUF
└─┬─┘ └──────────────┬────────────────┘
  org              repo name
```

**Must be a GGUF-quantized repo.** The repo name usually ends with `-GGUF`. If you point to a non-GGUF repo (e.g. `Qwen/Qwen2.5-Coder-7B-Instruct`), the resolver will fail because there are no `.gguf` files to download.

### `model.file` (optional — recommended)

The specific GGUF filename to download. If omitted, the system auto-selects the best quantization that fits your VRAM.

**Where to find it:**

On the HuggingFace model page, scroll down to the **Files and versions** tab. Look for `.gguf` files:

```
┌─────────────────────────────────────────────┐
│ Files and versions                           │
│                                              │
│ ☐ qwen2.5-coder-7b-instruct-q4_k_m.gguf     │  ← pick this
│ ☐ qwen2.5-coder-7b-instruct-q8_0.gguf       │
│ ☐ qwen2.5-coder-7b-instruct-fp16.gguf       │
└─────────────────────────────────────────────┘
```

**Quantization guide (Q4_K_M is safest for most setups):**

| Quant | Quality | VRAM needed (7B) | When to use |
|-------|---------|-------------------|-------------|
| Q2_K | Lowest | ~3 GB | Very limited VRAM |
| Q3_K_M | Low | ~4 GB | 4-6 GB VRAM |
| **Q4_K_M** | **Good** | **~5 GB** | **Default — best quality/speed balance** |
| Q5_K_M | Better | ~6 GB | 8+ GB VRAM |
| Q8_0 | High | ~8 GB | 12+ GB VRAM |
| F16 | Full | ~14 GB | 24+ GB VRAM |

### `model.gpu_layers` (optional — default 999)

How many transformer layers to offload to the GPU. Default `999` offloads all layers.

You only need to change this if:
- You run out of VRAM (lower the number)
- You want partial CPU offloading for a very large model

### `model.ctx_size` (optional — default 0)

Context window in tokens. `0` = auto-detect from the model's `config.json` on HuggingFace, then clamped to fit your VRAM.

You only need to set this if auto-detection gives wrong results (very rare).

---

## Visual Walkthrough: Real Example

Say you want to add the model `unsloth/Qwen3-14B-GGUF`.

**Step 1:** Go to `https://huggingface.co/unsloth/Qwen3-14B-GGUF`

```
┌────────────────────────────────────────────────┐
│  unsloth / Qwen3-14B-GGUF                      │
│  └───┬──┘ └──────┬──────┘                     │
│      org        repo name                      │
│                                                 │
│  ● You need a HuggingFace token to download     │
│    this model.                                  │
└────────────────────────────────────────────────┘
```

model.id = `unsloth/Qwen3-14B-GGUF`

**Step 2:** Scroll to **Files and versions**

```
┌────────────────────────────────────────────────┐
│ Files and versions                              │
│                                                 │
│ Qwen3-14B-Q4_K_M.gguf   · 8.29 GB              │
│ Qwen3-14B-Q6_K.gguf     · 11.1 GB              │
│ Qwen3-14B-Q8_0.gguf     · 14.3 GB              │
│ Qwen3-14B-F16.gguf      · 26.6 GB              │
└────────────────────────────────────────────────┘
```

Pick the file that fits your VRAM and quality needs.

model.file = `Qwen3-14B-Q4_K_M.gguf`

**Step 3:** Write `.models.yaml`

```yaml
model:
  id: unsloth/Qwen3-14B-GGUF
  file: Qwen3-14B-Q4_K_M.gguf
```

---

## Complete Example: All Fields

```yaml
model:
  id: Qwen/Qwen2.5-Coder-7B-Instruct-GGUF
  file: qwen2.5-coder-7b-instruct-q4_k_m.gguf
  gpu_layers: 999
  ctx_size: 32768
```

---

## What Happens Next

When you run `make bootstrap-register` (or `gb-ai-server --register`):

```
.models.yaml  ──>  parser.py  ──>  ModelEntry  ──>  register_model()
                                                      │
                                                      ▼
                                              Agent configs updated:
                                                cline, omp, vibe, pi
                                              Container restarted with:
                                                new model GGUF file
```

The system:
1. Reads your `.models.yaml`
2. If you omitted `file`, it queries HuggingFace to pick the best quantization
3. Downloads the model
4. Probes your VRAM and computes a safe context window
5. Registers the model with all agents
6. Updates the container config
