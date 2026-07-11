# Installation

Install `gb-ai-server` as a global CLI command.

## Prerequisites

- Python 3.14+
- uv (package manager)
- Podman with Compose support
- NVIDIA GPU with Container Toolkit (for GPU mode)

## Quick Install

```bash
git clone <repo-url>
cd gb-ai-server
./scripts/install.sh
```

After install, the `gb-ai-server` command is available from any directory:

```bash
gb-ai-server --help
```

## Dev Install

Editable install — source changes reflected immediately:

```bash
./scripts/install.sh --dev
uv run gb-ai-server
```

## Manual Install

```bash
uv sync
uv run gb-ai-server
```

Or with pip:

```bash
pip install .
gb-ai-server --help
```

## CLI Subcommands

| Command | Description |
|---------|-------------|
| `gb-ai-server` | Full bootstrap: download, start, health-check, register |
| `gb-ai-server --dry-run` | Preview without making changes |
| `gb-ai-server --skip-download` | Skip model download |
| `gb-ai-server --skip-health` | Skip health verification |
| `gb-ai-server --register` | Register model from `.models.yaml` with all agents |
| `gb-ai-server --register-custom <repo>` | Register a custom HF model |
| `gb-ai-server --models-dir <path>` | Override model storage directory |

## Shell Completion

The CLI supports tab-completion for bash, zsh, and fish.

```bash
eval "$(_GB_AI_SERVER_COMPLETE=bash_source gb-ai-server)"
eval "$(_GB_AI_SERVER_COMPLETE=zsh_source gb-ai-server)"
gb-ai-server --fish-complete | source
```

Add the appropriate line to your shell profile for permanent completion.
