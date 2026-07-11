# gb-ai-server

Local LLM inference server using llama.cpp with Podman. Auto-detects models
from HuggingFace and registers them with AI coding tools.

## Overview

- **llama.cpp server** — GPU-accelerated inference via Podman
- **Auto-detection** — model file, quantization, context window from HuggingFace
- **Fit check** — verifies GPU VRAM before downloading
- **Agent registration** — registers model with OpenCode, Mistral Vibe, Pi, Cline

## Quick Start

### Prerequisites

- Podman with Compose support
- NVIDIA GPU with drivers and Container Toolkit
- Python 3.14+ with `uv`

### Install

```bash
git clone <repo-url>
cd gb-ai-server
uv sync
make check-cdi    # verify GPU
```

### Configure

1. Copy `.env.example` to `.env`
2. Edit `.models.yaml` with a HuggingFace GGUF repo:

```yaml
model:
  id: unsloth/Qwen3-14B-GGUF
```

See [docs/adding-models.md](docs/adding-models.md) for details.

### Run

```bash
make bootstrap          # download, start, health check
make bootstrap-quick    # skip download and health check
make bootstrap-register # register model with AI coding tools
```

After bootstrap, the API is available at `http://localhost:8081/v1`
(OpenAI-compatible).

## Make Commands

```bash
# Core
make up                  # start llama service
make down                # stop everything
make restart             # restart services

# Register
make register HF_MODEL=org/repo    # register a HF model
make register HF_MODEL=org/repo CTX_SIZE=32768

# Bootstrap
make bootstrap           # full: download + start + health
make bootstrap-quick     # skip download and health
make bootstrap-register  # register from .models.yaml

# Monitoring
make status ps logs      # status / containers / logs
make logs-coder          # llama container logs
make models              # list downloaded GGUF files

# GPU
make check-cdi           # verify GPU access

# Maintenance
make clean               # remove containers (keeps volumes)
make clean-all           # remove everything
```

## Adding a Model

1. Find a GGUF repo on HuggingFace (`{org}/{model}-GGUF`)
2. Paste the ID into `.models.yaml`:

```yaml
model:
  id: unsloth/DeepSeek-V4-Pro-GGUF
```

3. Optionally specify a file, GPU layers, or context window:

```yaml
model:
  id: unsloth/DeepSeek-V4-Pro-GGUF
  file: DeepSeek-V4-Pro-Q4_K_M.gguf
  gpu_layers: 999
  ctx_size: 0    # auto-detect
```

The application auto-detects everything when only `id` is set.
See [docs/adding-models.md](docs/adding-models.md) for the full guide.

## Project Structure

```
gb-ai-server/
├── src/gb_ai_server/           # Python package
│   ├── application/            # Use cases and services
│   ├── domain/                 # Pure domain logic
│   ├── infrastructure/         # Implementations
│   │   └── persistence/        # HF resolver, GGUF reader, templates
│   └── presentation/           # CLI, parser, composer
├── .models.yaml                # Model configuration
├── docker-compose.yml          # Container definition
├── .env.example                # Environment template
├── Makefile
├── pyproject.toml
├── docs/
│   └── adding-models.md        # Model setup guide
└── tests/
```

## GPU

```bash
make check-cdi
```

Requires NVIDIA drivers and Container Toolkit. CDI device definitions
must exist (`nvidia-ctk cdi generate`). The `nvidia-cdi-refresh.service`
being inactive is harmless — it only auto-refreshes on driver updates.

See [docs/benchmarks/cdi-comparison.md](docs/benchmarks/cdi-comparison.md)
for measured performance data (GPU vs CPU).

## Troubleshooting

### Container won't start
```bash
make logs-coder
podman run --rm --device nvidia.com/gpu=all ubuntu nvidia-smi
```

### "Repo has no GGUF files"
You used a non-GGUF repo. Append `-GGUF` to the model name.

### "Model does not fit"
The model is too large for your GPU. Try a smaller quantization
by specifying `file: model-Q2_K.gguf` or reduce `gpu_layers`.

### Port conflicts
Edit `.env` or `docker-compose.yml` to change ports.

## License

MIT
