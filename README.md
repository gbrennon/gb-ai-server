# gb-ai-server

Local LLM inference server using llama.cpp with Podman. Auto-detects models
from HuggingFace and registers them with AI coding tools.

## Overview

- **llama.cpp server** — GPU-accelerated inference via Podman
- **Auto-detection** — model file, quantization, context window from HuggingFace
- **Fit check** — verifies GPU VRAM before downloading
- **Agent registration** — registers model with OpenCode, Mistral Vibe, Pi, Cline
- **CPU mode** — fallback for machines without NVIDIA GPUs

## Quick Start

### Prerequisites

- Podman with Compose support
- NVIDIA GPU with drivers and Container Toolkit (or CPU-only mode)
- Python 3.14+ with `uv`

### Install as a global CLI

```bash
git clone <repo-url>
cd gb-ai-server
./scripts/install.sh
```

This installs `gb-ai-server` globally. After install, the command is available
from any directory:

```bash
gb-ai-server --help
```

For editable dev install (source changes reflected immediately):

```bash
./scripts/install.sh --dev
uv run gb-ai-server
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
# GPU mode (default)
make bootstrap          # download, start, health check, register

# CPU-only mode
make bootstrap-cpu-container
```

After bootstrap, the API is available at `http://localhost:8081/v1`
(OpenAI-compatible).

### Select model in your coding agent

After bootstrap, open your agent and select the provider **"local llama.cpp"**.
See [docs/using-models-in-agents.md](docs/using-models-in-agents.md) for
per-agent instructions.

## Make Commands

```bash
# Core
make up                  # start llama service (GPU)
make down                # stop everything
make restart             # restart services

# Register
make register HF_MODEL=org/repo    # register a HF model

# Bootstrap
make bootstrap           # full: download + start + health + register (GPU)
make bootstrap-quick     # skip download and health
make bootstrap-register  # register from .models.yaml
make bootstrap-cpu-container  # full bootstrap CPU-only

# CPU-only
make cpu-up              # start CPU container
make cpu-down            # stop CPU container
make cpu-logs            # follow CPU container logs

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
├── docker-compose.yml          # GPU container definition
├── docker-compose.cpu.yml      # CPU container definition
├── .env.example                # Environment template
├── Makefile
├── pyproject.toml
├── scripts/
│   └── install.sh              # CLI installer
├── docs/                       # Full documentation
│   ├── installation.md
│   ├── bootstrap-flow.md
│   ├── cpu-gpu-modes.md
│   ├── context-window.md
│   ├── agent-registration.md
│   ├── troubleshooting.md
│   └── ...
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

### "request exceeds the available context size"

The model ran out of context window. Your agent is sending more tokens than
the server can hold in VRAM.

**GPU mode** — the max context is limited by VRAM. Q4_K_M at 12 GB gets
~12k tokens. To increase it:

```yaml
model:
  id: unsloth/Qwen3-14B-GGUF
  gpu_layers: 20
```

Restart after changing: `make down && CTX_SIZE=12288 make up`

**CPU mode** — context is limited by system RAM. Bump `CTX_SIZE` in `.env`:

```bash
echo "CTX_SIZE=32768" >> .env
make bootstrap-cpu-container
```

For a full explanation see [docs/using-models-in-agents.md](docs/using-models-in-agents.md).

## License

MIT
