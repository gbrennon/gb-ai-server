.PHONY: help up down logs status ps models check-cdi clean restart

COMPOSE_FILE := docker-compose.yml
ENV_FILE := .env
COMPOSE := podman-compose --env-file $(ENV_FILE) -f $(COMPOSE_FILE)

help:
	@echo "AI Code Models Stack - Podman Compose"
	@echo ""
	@echo "Usage: make [target]"
	@echo ""
	@echo "Core targets:"
	@echo "  up              Start primary services (llama-coder + open-webui)"
	@echo "  up-all          Start all services including extras (Devstral, Qwen3, Gemma4)"
	@echo "  down            Stop all services"
	@echo "  restart         Restart all running services"
	@echo ""
	@echo "Monitoring:"
	@echo "  status          Show service status"
	@echo "  ps              List running containers"
	@echo "  logs            Follow logs (all services)"
	@echo "  logs-coder      Follow llama-coder logs"
	@echo "  logs-webui      Follow open-webui logs"
	@echo ""
	@echo "GPU & Environment:"
	@echo "  check-cdi       Verify CDI setup and list available GPUs"
	@echo "  models          List downloaded models in llama_models volume"
	@echo ""
	@echo "Maintenance:"
	@echo "  clean           Remove all containers (keeps volumes)"
	@echo "  clean-all       Remove containers AND volumes (WARNING: data loss)"
	@echo ""

# Primary stack
up:
	$(COMPOSE) up -d
	@echo "✓ Primary stack started (llama-coder + open-webui)"
	@echo ""
	@echo "Access Open WebUI: http://localhost:3000"
	@echo "API endpoint: http://localhost:8081 (llama-coder)"

# Full stack with extras
up-all:
	$(COMPOSE) --profile extra up -d
	@echo "✓ Full stack started (all LLM services + open-webui)"
	@echo ""
	@echo "Endpoints:"
	@echo "  Open WebUI:     http://localhost:3000"
	@echo "  Qwen2.5 Coder:  http://localhost:8081"
	@echo "  Qwen3:          http://localhost:8082"
	@echo "  Devstral:       http://localhost:8083"
	@echo "  Gemma4:         http://localhost:8084"

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

logs-webui:
	$(COMPOSE) logs -f open-webui

# GPU verification
check-cdi:
	@echo "=== CDI Status ==="
	@nvidia-ctk cdi list || echo "Error: nvidia-ctk not found. Install NVIDIA Container Toolkit."
	@echo ""
	@echo "=== Systemd Service Status ==="
	@systemctl is-active nvidia-cdi-refresh.service && echo "nvidia-cdi-refresh.service is active" || echo "✗ nvidia-cdi-refresh.service is NOT active"
	@echo ""
	@echo "=== Test GPU Access ==="
	@podman run --rm --device nvidia.com/gpu=all --security-opt=label=disable ubuntu nvidia-smi -L 2>/dev/null && echo "✓ GPU accessible via CDI" || echo "✗ GPU not accessible"

# Models management
models:
	@echo "=== Downloaded Models ==="
	@podman run --rm -v llama_models:/models alpine ls -lh /models || echo "No models found yet"

clean:
	$(COMPOSE) down
	@echo "Containers removed (volumes retained)"

clean-all:
	@read -p "WARNING: This will delete all containers AND volumes. Continue? [y/N] " -n 1 -r; \
	echo; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		$(COMPOSE) down -v; \
		echo "All containers and volumes removed"; \
	else \
		echo "Cancelled."; \
	fi
