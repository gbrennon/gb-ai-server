# gb-ai-server

A Python-based bootstrap tool for running local LLM models using llama.cpp with Docker/Podman, with automatic model registration for Cline (VS Code AI assistant).

## Overview

This project provides a complete stack for running local LLMs with GPU acceleration:

- **llama.cpp servers** - High-performance LLM inference servers via Docker/Podman
- **Open WebUI** - Web interface for chatting with models
- **Automatic Cline integration** - Models automatically registered as custom providers in Cline
- **GPU support** - NVIDIA GPU acceleration via CDI
- **Model management** - Download, copy, and manage GGUF models

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      gb-ai-server                           │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐          │
│  │ llama-coder │  │ llama-qwen3 │  │ llama-devs  │  ...     │
│  │  (port 8081)│  │  (port 8082)│  │  (port 8083)│          │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘          │
│         │                │                │                  │
│         └────────────────┼────────────────┘                  │
│                          ▼                                   │
│              ┌─────────────────────┐                         │
│              │   Cline (VS Code)   │                         │
│              │  Custom Providers:  │                         │
│              │  • llama-coder      │                         │
│              │  • llama-qwen3      │                         │
│              │  • llama-devs       │                         │
│              └─────────────────────┘                         │
└─────────────────────────────────────────────────────────────┘
```

## Quick Start

### Prerequisites

- **Podman** or **Docker** with Compose support
- **NVIDIA GPU** with drivers and Container Toolkit (for GPU acceleration)
- **Python 3.12+** with `uv` package manager
- **Make** (optional, for convenience commands)

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd gb-ai-server

# Install Python dependencies
uv sync

# Verify GPU access (optional)
make check-cdi
```

### Configuration

1. **Models**: Edit `scripts/models.conf.sh` to configure which models to download:
   ```bash
   MODELS=(
     "qwen2.5-coder:7b|qwen2.5-coder-7b-instruct-q4_k_m.gguf|https://huggingface.co/..."
     "qwen3:14b|Qwen3-14B-Q4_K_M.gguf|https://huggingface.co/..."
     # Add more models as needed
   )
   ```

2. **Environment**: Copy `.env.example` to `.env` and adjust settings:
   ```bash
   cp .env.example .env
   # Edit .env for custom ports, model paths, etc.
   ```

### Running

#### Full Bootstrap (recommended for first run)
```bash
# Downloads models, starts containers, copies models, verifies health, registers with Cline
make bootstrap

# Or run directly with uv
uv run gb-ai-server
```

#### Quick Start (skip download & health check)
```bash
make bootstrap-quick
# or
uv run gb-ai-server --skip-download --skip-health
```

#### Dry Run (preview actions)
```bash
make bootstrap-dry
# or
uv run gb-ai-server --dry-run
```

#### Register Models Only (no bootstrap)
```bash
make register-models
# or
uv run gb-ai-server --register-models --skip-download --skip-health
```

### Accessing Services

After bootstrap completes:

| Service | URL | Description |
|---------|-----|-------------|
| **llama-coder API** | http://localhost:8081 | Primary llama.cpp server (qwen2.5-coder) |
| **llama-qwen3 API** | http://localhost:8082 | Qwen3 model server (with `--profile extra`) |
| **llama-devs API** | http://localhost:8083 | Devstral model server (with `--profile extra`) |
| **Open WebUI** | http://localhost:3000 | Web chat interface |

### Cline Integration

Models are automatically registered as **custom providers** in Cline with container-based names:

- `llama-coder` → qwen2.5-coder:7b (port 8081)
- `llama-qwen3` → qwen3:14b (port 8082)
- `llama-devs` → devstral-small-2 (port 8083)

In Cline, you'll see these as selectable providers with their respective models pre-configured.

## Commands Reference

### Make Targets

```bash
# Core stack
make up              # Start primary services (llama-coder + open-webui)
make up-all          # Start all services including extras
make down            # Stop all services
make restart         # Restart all running services

# Monitoring
make status          # Show service status
make ps              # List running containers
make logs            # Follow logs (all services)
make logs-coder      # Follow llama-coder logs
make logs-webui      # Follow open-webui logs

# GPU & Environment
make check-cdi       # Verify CDI setup and list available GPUs
make models          # List downloaded models in llama_models volume

# Bootstrap
make bootstrap       # Full bootstrap: prerequisites → models → start → copy → health → register
make bootstrap-dry   # Dry-run mode (preview only)
make bootstrap-quick # Skip download & health check (faster)
make bootstrap-register # Register models only

# Maintenance
make clean           # Remove all containers (keeps volumes)
make clean-all       # Remove containers AND volumes (WARNING: data loss)
```

### Direct Python Commands

```bash
# Full bootstrap
uv run gb-ai-server

# With options
uv run gb-ai-server --skip-download --skip-health
uv run gb-ai-server --dry-run
uv run gb-ai-server --register-models --skip-download --skip-health
uv run gb-ai-server --models-dir /custom/path --hf-token YOUR_TOKEN
uv run gb-ai-server --debug
```

## Project Structure

```
gb-ai-server/
├── src/gb_ai_server/           # Python package
│   ├── application/            # Application services (use cases)
│   ├── domain/                 # Domain logic (pure, no I/O)
│   ├── infrastructure/         # Infrastructure implementations
│   │   ├── persistence/        # Cline model registrar
│   │   ├── container_runtime/  # Podman/Docker detection
│   │   ├── compose/            # Compose tool detection
│   │   └── http/               # HTTP client
│   └── presentation/           # CLI, parser, composer
├── scripts/
│   ├── bootstrap.sh            # Legacy bash bootstrap (deprecated)
│   ├── models.conf.sh          # Model definitions
│   └── lib/                    # Shared bash functions
├── tests/                      # Unit & integration tests
├── docker-compose.yml          # Container definitions
├── .env.example                # Environment template
├── Makefile                    # Convenience commands
├── pyproject.toml              # Python project config
└── README.md                   # This file
```

## Adding New Models

1. Add model entry to `scripts/models.conf.sh`:
   ```bash
   MODELS=(
     "existing-model|filename.gguf|https://..."
     "new-model:7b|new-model-7b-q4_k_m.gguf|https://huggingface.co/..."
   )
   ```

2. Add corresponding service to `docker-compose.yml`:
   ```yaml
   services:
     llama-new-model:
       image: ghcr.io/ggml-org/llama.cpp:server-cuda
       container_name: llama-new-model
       profiles:
         - extra
       ports:
         - "8084:8080"
       volumes:
         - llama_models:/models
       command:
         - --model
         - /models/new-model-7b-q4_k_m.gguf
         # ... other llama.cpp args
   ```

3. Update container name mapping in `src/gb_ai_server/presentation/composer.py`:
   ```python
   def _get_container_names(self, model_count: int) -> list[str]:
       default_containers = ["llama-coder", "llama-qwen3", "llama-devs", "llama-new-model"]
       return default_containers[:model_count]
   ```

4. Run bootstrap:
   ```bash
   make bootstrap
   ```

## GPU Requirements

For GPU acceleration, ensure:
- NVIDIA drivers installed
- NVIDIA Container Toolkit installed (`nvidia-ctk`)
- CDI configured (`nvidia-ctk cdi list` should show GPUs)
- `nvidia-cdi-refresh.service` active

Verify with:
```bash
make check-cdi
```

## Troubleshooting

### Container won't start
```bash
# Check logs
make logs-coder

# Verify GPU access
podman run --rm --device nvidia.com/gpu=all ubuntu nvidia-smi
```

### Models not registering with Cline
```bash
# Manual registration
make register-models

# Check Cline data directory
ls -la ~/.cline/data/settings/
```

### Port conflicts
Edit `.env` or `docker-compose.yml` to change ports:
```yaml
ports:
  - "8081:8080"  # Change 8081 to another port
```

## License

MIT License - see LICENSE file for details.

