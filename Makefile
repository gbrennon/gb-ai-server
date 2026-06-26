.PHONY: help up down logs status ps models check-cdi clean restart bootstrap bootstrap-dry bootstrap-quick bootstrap-coder bootstrap-qwen3 bootstrap-devs register-models register-models-quick clean-all list-models

COMPOSE_FILE := docker-compose.yml
ENV_FILE := .env
COMPOSE := podman-compose --env-file $(ENV_FILE) -f $(COMPOSE_FILE)

help:
	@echo "AI Code Models Stack - Podman Compose"
	@echo ""
	@echo "Usage: make [target]"
	@echo ""
	@echo "Core targets:"
	@echo "  up              Start llama-coder service"
	@echo "  down            Stop all services"
	@echo "  restart         Restart all running services"
	@echo ""
	@echo "Monitoring:"
	@echo "  status          Show service status"
	@echo "  ps              List running containers"
	@echo "  logs            Follow logs (all services)"
	@echo "  logs-coder      Follow llama-coder logs"
	@echo ""
	@echo "GPU & Environment:"
	@echo "  check-cdi       Verify CDI setup and list available GPUs"
	@echo "  models          List downloaded models in llama_models volume"
	@echo ""
	@echo "Bootstrap (uv run gb-ai-server):"
	@echo "  bootstrap       Default model (qwen2.5-coder)"
	@echo "  bootstrap-coder Qwen2.5 Coder 7B"
	@echo "  bootstrap-qwen3 Qwen3 14B"
	@echo "  bootstrap-devs  Devstral Small 2 24B"
	@echo "  bootstrap-dry   Dry-run mode (preview only)"
	@echo "  bootstrap-quick Skip download & health check (faster)"
	@echo ""
	@echo "Maintenance:"
	@echo "  clean           Remove all containers (keeps volumes)"
	@echo "  clean-all       Remove containers AND volumes (WARNING: data loss)"
	@echo "  list-models     Show available models"
	@echo ""

# Start service
up:
	$(COMPOSE) up -d
	@echo "✓ Service started"
	$(MAKE) register-models-quick

down:
	$(COMPOSE) down
	@echo "✓ Stack stopped"

restart:
	$(COMPOSE) restart
	@echo "Services restarted"

status:
	@echo "=== Service Status ==="
	$(COMPOSE) ps

ps:
	@podman ps --filter "label=com.docker.compose.project" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

logs:
	$(COMPOSE) logs -f

logs-coder:
	$(COMPOSE) logs -f llama-coder

# GPU verification
check-cdi:
	@echo "=== CDI Status ==="
	@nvidia-ctk cdi list || echo "Error: nvidia-ctk not found. Install NVIDIA Container Toolkit."
	@echo ""
	@echo "=== Systemd Service Status ==="
	@systemctl is-active nvidia-cdi-refresh.service && echo "nvidia-cdi-refresh.service is active" || echo "nvidia-cdi-refresh.service is NOT active"
	@echo ""
	@echo "=== Test GPU Access ==="
	@podman run --rm --device nvidia.com/gpu=all --security-opt=label=disable ubuntu nvidia-smi -L 2>/dev/null && echo "GPU accessible via CDI" || echo "GPU not accessible"

# Models management
models:
	@echo "=== Downloaded Models ==="
	@podman run --rm -v llama_models:/models alpine ls -lh /models || echo "No models found yet"

clean:
	$(COMPOSE) down
	@echo "Containers removed (volumes retained)"

# Register models with Cline
register-models:
	uv run gb-ai-server --register-models --skip-download --skip-health

register-models-quick:
	uv run gb-ai-server --register-models --skip-download --skip-health 2>/dev/null || true

# List available models
list-models:
	uv run gb-ai-server --list-models

# Bootstrap — orchestrate the full llama.cpp bootstrap via uv
bootstrap:
	uv run gb-ai-server

bootstrap-coder:
	uv run gb-ai-server --model qwen2.5-coder:7b

bootstrap-qwen3:
	uv run gb-ai-server --model qwen3:14b

bootstrap-devs:
	uv run gb-ai-server --model devstral-small-2

bootstrap-dry:
	uv run gb-ai-server --dry-run

bootstrap-quick:
	uv run gb-ai-server --skip-download --skip-health

bootstrap-register:
	uv run gb-ai-server --register-models

clean-all:
	@read -p "WARNING: This will delete all containers AND volumes. Continue? [y/N] " -n 1 -r; \
	echo; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		$(COMPOSE) down -v; \
		echo "All containers and volumes removed"; \
	else \
		echo "Cancelled."; \
	fi
