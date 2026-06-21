#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="${SCRIPT_DIR}/.."
source "$SCRIPT_DIR/lib/core.sh"
source "$SCRIPT_DIR/lib/llama.sh"
DRY_RUN=false

usage() {
  cat <<EOF
Usage: $0 [OPTIONS]

Options:
  --dry-run       Run without making changes
  -h, --help      Show this help message
EOF
}

parse_args() {
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --dry-run)
        DRY_RUN=true
        shift
        ;;
      -h|--help)
        usage
        exit 0
        ;;
      *)
        echo "Unknown option: $1"
        usage
        exit 1
        ;;
    esac
  done
}

verify_prerequisites() {
  log_section "Prerequisites Check"
  local required_cmds=("$CONTAINER_RUNTIME" "curl")
  for cmd in "${required_cmds[@]}"; do
    require_command "$cmd" || exit 1
  done
  log_section "${CONTAINER_RUNTIME^} Health Check"
  if ! $CONTAINER_RUNTIME ps >/dev/null 2>&1; then
    log_error "$CONTAINER_RUNTIME is not responding. Check your setup."
    exit 1
  fi
  log_ok "$CONTAINER_RUNTIME is healthy"
}

download_gguf_models() {
  log_section "Download GGUF Models"
  source "$SCRIPT_DIR/models.conf.sh"
  mkdir -p /tmp/llama_models
  for entry in "${MODELS[@]}"; do
    local name filename url
    name=$(get_model_display_name "$entry")
    filename=$(get_model_filename "$entry")
    url=$(get_model_url "$entry")
    if [[ -f "/tmp/llama_models/${filename}" ]]; then
      log_info "$name already downloaded"
    else
      log_info "Downloading $name..."
      if ! is_dry_run; then
        download_gguf "$filename" "$url" || log_warn "Failed to download $name"
      else
        dry_run_info "Would download: $url -> $filename"
      fi
    fi
  done
}

start_container_stack() {
  log_section "Container Stack"

  if is_dry_run; then
    log_info "[dry-run] Would execute: $COMPOSE_CMD down"
    log_info "[dry-run] Would execute: $COMPOSE_CMD up -d"
  else
    run_compose() {
      "$@" 2>&1 | grep -v "^Error: no container with" | grep -v "^Error: cannot remove" | grep -v "^WARN\[0" || true
      return 0
    }

    run_compose $COMPOSE_CMD down --timeout 0
    run_compose $COMPOSE_CMD up -d llama web

    log_ok "Stack started"
  fi
}

copy_models_to_container() {
  log_section "Copy Models to Container"
  source "$SCRIPT_DIR/models.conf.sh"
  local container="llama-coder"

  if ! container_is_running "$container"; then
    log_warn "Container $container not running, skipping model copy"
    return 1
  fi

  for entry in "${MODELS[@]}"; do
    local name filename
    name=$(get_model_display_name "$entry")
    filename=$(get_model_filename "$entry")
    if gguf_exists_in_container "$filename" "$container"; then
      log_info "$name already in container"
    elif [[ -f "/tmp/llama_models/${filename}" ]]; then
      log_info "Copying $name to container..."
      podman cp "/tmp/llama_models/${filename}" "${container}:/models/${filename}" || log_warn "Failed to copy $name"
    else
      log_warn "$name not downloaded, skipping"
    fi
  done
  log_ok "Models copied to container"
}

restart_llama_container() {
  log_section "Restart llama.cpp"
  if ! is_dry_run; then
    log_info "Restarting llama-coder to load model..."
    podman restart llama-coder 2>&1 || log_warn "Failed to restart llama-coder"
  fi
}

wait_for_llama_server() {
  log_section "Waiting for llama.cpp"
  dry_run_info "Would wait for llama.cpp"
  if ! is_dry_run; then
    wait_for_llama "http://localhost:8081" 60 5 || {
      log_error "llama.cpp did not become healthy in time."
      log_error "Check: podman logs llama-coder"
      exit 1
    }
  fi
}

verify_via_api() {
  log_section "Verify Models via HTTP API"
  source "$SCRIPT_DIR/models.conf.sh"
  local all_ready=true
  local ports=("8081" "8082" "8083")
  local idx=0
  for entry in "${MODELS[@]}"; do
    local name port
    name=$(get_model_display_name "$entry")
    port="${ports[$idx]}"
    local http_code
    http_code=$(curl -sf "http://localhost:${port}/health" -o /dev/null -w "%{http_code}" 2>/dev/null || echo "000")
    if [[ "$http_code" == "200" ]]; then
      log_ok "$name is available on :${port}"
    else
      log_warn "$name not yet available on :${port} (HTTP $http_code)"
      all_ready=false
    fi
    idx=$((idx + 1))
  done
  $all_ready
}

finalize() {
  log_section "Done"
  log_ok "Bootstrap complete."
  echo ""
  log_info "Services:"
  echo "    llama.cpp (coder) : http://localhost:8081"
  echo "    Open WebUI        : http://localhost:3000"
  echo ""
  log_info "Extra models (make up-extra):"
  echo "    llama.cpp (qwen3) : http://localhost:8082"
  echo "    llama.cpp (devs)  : http://localhost:8083"
  echo ""
}

main() {
  parse_args "$@"
  detect_compose_tool
  verify_prerequisites
  download_gguf_models
  start_container_stack
  copy_models_to_container
  restart_llama_container
  wait_for_llama_server
  verify_via_api || true
  finalize
}

main "$@"
