#!/usr/bin/env bash
set -uo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="${SCRIPT_DIR}/.."

source "$REPO_ROOT/scripts/lib/core.sh"

init_container_runtime

echo "=== Container Status ==="
for container in llama-coder llama-qwen3 llama-devs; do
  if container_is_running "$container"; then
    echo "  $container: running"
  else
    echo "  $container: not running"
  fi
done
echo ""

echo "=== API Status ==="
for port in 8081 8082 8083; do
  if curl -sf "http://localhost:${port}/health" >/dev/null 2>&1; then
    echo "  :${port} - healthy"
  else
    echo "  :${port} - not responding"
  fi
done
echo ""

echo "=== GGUF Models ==="
source "$REPO_ROOT/scripts/models.conf.sh"
for entry in "${MODELS[@]}"; do
  local name filename
  name=$(echo "$entry" | cut -d'|' -f1)
  filename=$(echo "$entry" | cut -d'|' -f2)
  if container_is_running llama-coder; then
    local size
    size=$(podman exec llama-coder sh -c "ls -lh /models/${filename} 2>/dev/null | awk '{print \$5}'" 2>/dev/null || echo "not found")
    echo "  $name ($filename): $size"
  else
    local local_size
    local_size=$(ls -lh "/tmp/llama_models/${filename}" 2>/dev/null | awk '{print $5}' || echo "not downloaded")
    echo "  $name ($filename): $local_size (local)"
  fi
done
