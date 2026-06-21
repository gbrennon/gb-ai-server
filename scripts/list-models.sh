#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="${SCRIPT_DIR}/.."

source "$REPO_ROOT/scripts/lib/core.sh"

init_container_runtime

echo "=== Registered Local Models ==="
echo ""
source "$REPO_ROOT/scripts/models.conf.sh"
for entry in "${MODELS[@]}"; do
  local name filename
  name=$(echo "$entry" | cut -d'|' -f1)
  filename=$(echo "$entry" | cut -d'|' -f2)
  echo "  $name"
  echo "    GGUF: $filename"
  if [[ -f "/tmp/llama_models/${filename}" ]]; then
    local size
    size=$(ls -lh "/tmp/llama_models/${filename}" | awk '{print $5}')
    echo "    Size: $size (downloaded)"
  else
    echo "    Size: not downloaded"
  fi
  echo ""
done

echo "=== API Endpoints ==="
for port in 8081 8082 8083; do
  local name=""
  case "$port" in
    8081) name="qwen2.5-coder:7b" ;;
    8082) name="qwen3:14b" ;;
    8083) name="devstral-small-2" ;;
  esac
  if curl -sf "http://localhost:${port}/health" >/dev/null 2>&1; then
    echo "  $name : http://localhost:${port} (running)"
  else
    echo "  $name : http://localhost:${port} (stopped)"
  fi
done
