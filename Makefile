.PHONY: help up down logs status ps models check-cdi enable-cdi clean restart bootstrap bootstrap-dry bootstrap-quick bootstrap-register clean-all register

COMPOSE_FILE := docker-compose.yml
ENV_FILE := .env
COMPOSE := podman-compose --env-file $(ENV_FILE) -f $(COMPOSE_FILE)

help: ## Show this help
	@grep -E '^[a-zA-Z_][a-zA-Z0-9_-]+:.*?## .*$$|^##@' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## |##@"}; \
		/^##@/ { printf "\n\033[1m%s\033[0m\n", substr($$0, 5) ; next } \
		{ printf "  \033[36m%-26s\033[0m %s\n", $$1, $$2 }'

##@ Core

up: ## Start llama service
	$(COMPOSE) up -d
	@echo "✓ Service started"

down: ## Stop all services
	$(COMPOSE) down
	@echo "✓ Stack stopped"

restart: ## Restart all running services
	$(COMPOSE) restart
	@echo "Services restarted"

##@ Register Custom Model

register: ## Register HF model (HF_MODEL=org/repo [CTX_SIZE=N])
	@[ -n "$(HF_MODEL)" ] || { echo "ERROR: HF_MODEL is required" >&2; exit 1; }
	uv run gb-ai-server --register-custom $(HF_MODEL) --ctx-size $${CTX_SIZE:-0}

##@ Monitoring

status: ## Show service status
	@echo "=== Service Status ==="
	$(COMPOSE) ps

ps: ## List running containers
	@podman ps --filter "label=com.docker.compose.project" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

logs: ## Follow logs (all services)
	$(COMPOSE) logs -f

logs-coder: ## Follow llama logs
	$(COMPOSE) logs -f llama

##@ GPU & Environment

enable-cdi: ## Generate CDI specs if missing (auto-enabled by bootstrap)
	@if command -v nvidia-ctk &>/dev/null; then \
		if nvidia-ctk cdi list 2>/dev/null | grep -qi gpu; then \
			echo "✓ CDI already active"; \
		else \
			echo "Generating CDI specs..."; \
			nvidia-ctk cdi generate 2>/dev/null && echo "✓ CDI enabled" || echo "⚠ Could not enable CDI"; \
		fi; \
	else \
		echo "⚠ nvidia-ctk not found — GPU passthrough unavailable"; \
	fi

check-cdi: ## Verify CDI setup and list GPUs
	@echo "=== CDI Status ==="
	@nvidia-ctk cdi list || echo "Error: nvidia-ctk not found"
	@echo ""
	@echo "=== Systemd Service Status ==="
	@systemctl is-active nvidia-cdi-refresh.service && echo "active" || echo "inactive"
	@echo ""
	@echo "=== Test GPU Access ==="
	@podman run --rm --device nvidia.com/gpu=all --security-opt=label=disable ubuntu nvidia-smi -L 2>/dev/null && echo "GPU accessible" || echo "GPU not accessible"

models: ## List models in llama_models volume
	@echo "=== Downloaded Models ==="
	@podman run --rm -v llama_models:/models alpine ls -lh /models || echo "No models found"

##@ Bootstrap

bootstrap: enable-cdi ## Start server (enables CDI first)
	uv run gb-ai-server

bootstrap-dry: ## Dry-run (preview only)
	uv run gb-ai-server --dry-run

bootstrap-quick: ## Skip download & health check
	uv run gb-ai-server --skip-download --skip-health

bootstrap-register: ## Register model from .models.yaml with all agents
	uv run gb-ai-server --register

##@ CPU-Only

bootstrap-cpu-container: ## Bootstrap CPU-only container + register model
	@echo "=== CPU-Only Bootstrap ==="
	@[ -f ".env" ] || cp .env.example .env
	@echo "Stopping any running containers..."
	@$(COMPOSE) down 2>/dev/null || true
	@podman stop llama-coder-cpu 2>/dev/null || true
	@podman rm llama-coder-cpu 2>/dev/null || true
	@echo "Starting CPU container..."
	podman-compose --env-file .env -f docker-compose.cpu.yml up -d
	@echo "Waiting for model to load on CPU (up to 160s for large models)..."
	@sleep 10
	@success=0; for i in $$(seq 1 30); do \
		if curl -sf http://localhost:8081/health >/dev/null 2>&1; then \
			echo "✓ CPU server healthy (after ~$$((10 + i * 5))s)"; \
			success=1; break; \
		fi; \
		sleep 5; \
	done; \
	if [ $$success -eq 0 ]; then \
		echo "ERROR: CPU server did not become healthy"; \
		podman logs llama-coder-cpu 2>&1 | tail -20; \
		exit 1; \
	fi
	@echo "Registering model with agents..."
	uv run gb-ai-server --register
	@echo ""
	@echo "=== CPU Bootstrap Complete ==="
	@echo "API: http://localhost:8081/v1"
	@echo "Logs: podman logs llama-coder-cpu"
cpu-up: ## Start CPU-only container (no bootstrap)
	@echo "Stopping GPU container (if running)..."
	@$(COMPOSE) down 2>/dev/null || true
	podman-compose --env-file .env -f docker-compose.cpu.yml up -d

cpu-down: ## Stop CPU container
	podman-compose --env-file .env -f docker-compose.cpu.yml down
	@echo "CPU container stopped"

cpu-logs: ## CPU container logs
	podman logs -f llama-coder-cpu

##@ Maintenance

clean: ## Remove containers (keeps volumes)
	$(COMPOSE) down
	podman-compose --env-file .env -f docker-compose.cpu.yml down 2>/dev/null || true
	@echo "Containers removed (volumes retained)"

clean-all: ## Remove containers AND volumes
	@read -p "WARNING: Delete all data? [y/N] " -n 1 -r; \
	echo; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		$(COMPOSE) down -v; \
		echo "All removed"; \
	else \
		echo "Cancelled."; \
	fi
