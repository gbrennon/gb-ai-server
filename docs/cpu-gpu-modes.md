# GPU vs CPU Modes

The project supports two inference modes. GPU mode uses NVIDIA CUDA
acceleration. CPU mode runs entirely on system RAM.

## GPU Mode (default)

```bash
make bootstrap
```

| Property | Value |
|----------|-------|
| Container image | `ghcr.io/ggml-org/llama.cpp:server-cuda` |
| Container name | `llama-coder` |
| Compose file | `docker-compose.yml` |
| GPU layers | 999 (all layers on GPU) |
| Context window | ~12k tokens (14B Q4_K_M on 12 GB VRAM) |
| Speed | 108-129 t/s (RTX 5070) |

### Requirements

- NVIDIA GPU with drivers
- NVIDIA Container Toolkit (CDI)
- `nvidia-ctk cdi generate` must have been run

### Verify GPU Access

```bash
make check-cdi
```

## CPU Mode

```bash
make bootstrap-cpu-container
```

| Property | Value |
|----------|-------|
| Container image | `ghcr.io/ggml-org/llama.cpp:server` |
| Container name | `llama-coder-cpu` |
| Compose file | `docker-compose.cpu.yml` |
| GPU layers | 0 |
| Threads | 16 |
| Context window | Configurable via `CTX_SIZE` in `.env` |
| Speed | Slower (~5-15 t/s depending on model and CPU) |

### Requirements

- No GPU required
- Sufficient system RAM (model size + KV cache)

## Switching Between Modes

Both containers share the same `llama_models` volume, so downloaded models
are available to both modes. Only one container can run at a time (both use
port 8081).

```bash
make down                        # stop GPU
make bootstrap-cpu-container     # start CPU

make cpu-down                    # stop CPU
make up                          # start GPU
```

## Makefile Targets

| Target | Mode | Description |
|--------|------|-------------|
| `make bootstrap` | GPU | Full bootstrap |
| `make up` | GPU | Start container only |
| `make down` | GPU | Stop container only |
| `make restart` | GPU | Restart container |
| `make bootstrap-cpu-container` | CPU | Full bootstrap |
| `make cpu-up` | CPU | Start container only |
| `make cpu-down` | CPU | Stop container only |
| `make cpu-logs` | CPU | Follow logs |

## Resource Limits

### GPU (`docker-compose.yml`)

```yaml
deploy:
  resources:
    limits:
      cpus: '4'
      memory: 12G
    reservations:
      cpus: '2'
      memory: 8G
```

### CPU (`docker-compose.cpu.yml`)

No deploy resource limits. Uses `--threads 16` and `--threads-batch 16`
via the llama.cpp CLI arguments.

## When to Use Which

| Scenario | Mode |
|----------|------|
| Development / coding agents | GPU (fast iteration) |
| Large context windows | CPU (RAM is cheaper than VRAM) |
| No NVIDIA GPU | CPU |
| Power efficiency | GPU |
| Background batch processing | CPU |
