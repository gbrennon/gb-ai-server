# Makefile Reference

All available `make` targets.

## GPU

| Target | Description |
|--------|-------------|
| `make bootstrap` | Full bootstrap: download, start, health-check, register |
| `make bootstrap-dry` | Preview without making changes |
| `make bootstrap-quick` | Skip download and health check |
| `make bootstrap-register` | Register model from `.models.yaml` with all agents |
| `make up` | Start GPU container |
| `make down` | Stop GPU container |
| `make restart` | Restart GPU container |

## CPU

| Target | Description |
|--------|-------------|
| `make bootstrap-cpu-container` | Full CPU bootstrap: start, health-check, register |
| `make cpu-up` | Start CPU container |
| `make cpu-down` | Stop CPU container |
| `make cpu-logs` | Follow CPU container logs |

## Registration

| Target | Description |
|--------|-------------|
| `make register HF_MODEL=org/repo` | Register a HuggingFace model with all agents |

## Monitoring

| Target | Description |
|--------|-------------|
| `make status` | Show compose service status |
| `make ps` | List running containers |
| `make logs` | Follow all service logs |
| `make logs-coder` | Follow llama container logs |
| `make models` | List GGUF files in the models volume |

## GPU & Environment

| Target | Description |
|--------|-------------|
| `make check-cdi` | Verify CDI setup and GPU access |

## Maintenance

| Target | Description |
|--------|-------------|
| `make clean` | Remove containers, keep volumes |
| `make clean-all` | Remove containers and volumes |

## Help

| Target | Description |
|--------|-------------|
| `make help` | Show all targets with descriptions |
