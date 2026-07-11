# Troubleshooting

## Container crashes on start (exit code 139)

The model loads but CUDA runs out of memory for the KV cache. Cause:
`CTX_SIZE` is too large for available VRAM.

```bash
podman logs llama-coder | grep "cudaMalloc failed"
```

Reduce GPU layers or context in `.models.yaml`:

```yaml
model:
  id: unsloth/Qwen3-14B-GGUF
  gpu_layers: 20
```

Then restart:

```bash
CTX_SIZE=8192 make down && CTX_SIZE=8192 make up
```

## Repo has no GGUF files

Used a non-GGUF HuggingFace repo. Append `-GGUF`:

```yaml
model:
  id: unsloth/DeepSeek-V4-Pro-GGUF
```

## Model does not fit on this hardware

The model is too large for the GPU. Options:

```yaml
model:
  id: unsloth/Qwen3-14B-GGUF
  file: Qwen3-14B-Q2_K.gguf    # smaller quantization
  gpu_layers: 10                 # fewer layers on GPU
```

Or use CPU mode:

```bash
make bootstrap-cpu-container
```

## Health check retries indefinitely

The container keeps restarting. Common causes:

- `CTX_SIZE` too large for available VRAM
- Model file missing from `/models/` volume
- GPU not accessible

```bash
make check-cdi
podman logs llama-coder | tail -20
```

## request exceeds the available context size

The agent is sending more tokens than the server's context window.

GPU mode:

```yaml
model:
  id: unsloth/Qwen3-14B-GGUF
  gpu_layers: 20
```

```bash
CTX_SIZE=16384 make down && CTX_SIZE=16384 make up
make bootstrap-register
```

CPU mode:

```bash
echo "CTX_SIZE=32768" >> .env
make bootstrap-cpu-container
```

## 401 Unauthorized

Set a non-empty API key in `.env`:

```bash
echo "OPENAI_API_KEY=local" >> .env
make bootstrap-register
```

Any non-empty string works — llama.cpp does not validate API keys.

## Model not found (404)

llama.cpp serves exactly one model at a time. Re-register:

```bash
make bootstrap-register
```

## BF16/F16 selected instead of Q4_K_M

The resolver picked unquantized weights. These are excluded on GPUs
under 24 GB. If it still happens, specify the file explicitly:

```yaml
model:
  id: unsloth/Qwen3-14B-GGUF
  file: Qwen3-14B-Q4_K_M.gguf
```

## Port 8081 already in use

Both GPU and CPU containers use port 8081. Only one can run at a time.

```bash
make down             # stop GPU
make cpu-down         # stop CPU
```

## Container uses wrong CTX_SIZE

The shell environment variable `CTX_SIZE` takes priority over `.env`.
Unset it before starting:

```bash
CTX_SIZE=12288 make down && CTX_SIZE=12288 make up
```

## Agent does not pick up the model

After registration:

- **Cline:** Reload VSCode window
- **OpenCode:** Select provider "local llama.cpp" in the TUI
- **Vibe:** Open model picker, select by alias
- **Pi:** Model appears automatically at startup

See `docs/agent-registration.md` for per-agent details.
