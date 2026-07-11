#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

BOLD='\033[1m'
GREEN='\033[32m'
YELLOW='\033[33m'
RED='\033[31m'
CYAN='\033[36m'
RESET='\033[0m'

ok()   { echo -e "  ${GREEN}✓${RESET} $*"; }
warn() { echo -e "  ${YELLOW}⚠${RESET} $*"; }
err()  { echo -e "  ${RED}✗${RESET} $*"; }
info() { echo -e "    $*"; }

MODE="global"

usage() {
    cat <<EOF
Usage: $0 [--dev] [--help]

Options:
  (default)    Global install — gb-ai-server available everywhere
  --dev        Editable dev install — source changes reflected immediately
  --help       Show this message

The CLI exposes these subcommands:
  gb-ai-server                  Full bootstrap (model download + start + register)
  gb-ai-server --register       Register current model with all coding agents
  gb-ai-server --register-custom <repo>   Register a custom HF model
  gb-ai-server --dry-run        Preview without changes
EOF
    exit 0
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        --dev)  MODE="dev"; shift ;;
        --help) usage ;;
        *)      echo "Unknown option: $1"; usage ;;
    esac
done

echo ""
echo -e "${BOLD}gb-ai-server installer${RESET}"
echo ""


echo -e "${BOLD}Checking prerequisites...${RESET}"

python_ok=0
if command -v python3.14 &>/dev/null; then
    py_ver=$(python3.14 --version 2>&1 | awk '{print $2}')
    ok "Python $py_ver"
elif command -v python3 &>/dev/null; then
    py_ver=$(python3 --version 2>&1 | awk '{print $2}')
    if python3 -c "import sys; sys.exit(0 if sys.version_info >= (3,14) else 1)" 2>/dev/null; then
        ok "Python $py_ver"
    else
        err "Python $py_ver — need >= 3.14"
        exit 1
    fi
else
    err "Python 3.14+ not found. Install via pyenv: pyenv install 3.14.3"
    exit 1
fi

if command -v uv &>/dev/null; then
    uv_ver=$(uv --version 2>&1 | awk '{print $2}')
    ok "uv $uv_ver"
else
    warn "uv not found. Install: curl -LsSf https://astral.sh/uv/install.sh | sh"
    warn "Continuing — will use pip as fallback"
fi

if command -v podman &>/dev/null; then
    ok "Podman $(podman --version 2>&1 | awk '{print $3}')"
else
    warn "Podman not found. Required for running the inference server."
    warn "Install: https://podman.io/docs/installation"
fi

gpu_ok=0
if command -v nvidia-smi &>/dev/null; then
    if nvidia-smi -L &>/dev/null 2>&1; then
        gpu_name=$(nvidia-smi --query-gpu=name --format=csv,noheader 2>/dev/null | head -1)
        ok "GPU detected: $gpu_name"
        gpu_ok=1
    fi
fi
if [ "$gpu_ok" -eq 0 ]; then
    warn "No NVIDIA GPU detected — will run CPU-only"
    warn "  CPU mode: make bootstrap-cpu-container"
fi

echo ""


cd "$REPO_ROOT"

if [ "$MODE" = "dev" ]; then
    echo -e "${BOLD}Installing in dev mode (editable)...${RESET}"
    if command -v uv &>/dev/null; then
        uv sync
        ok "Dependencies synced (uv)"
    else
        pip install -e .
        ok "Installed editable (pip)"
    fi
    echo ""
    echo -e "${BOLD}Dev install complete. Run with:${RESET}"
    echo "  uv run gb-ai-server"
    echo ""
else
    echo -e "${BOLD}Installing globally...${RESET}"
    if command -v uv &>/dev/null; then
        uv tool install --python 3.14 --force .
        ok "gb-ai-server installed globally (uv tool)"
    else
        pip install --user .
        ok "gb-ai-server installed (pip --user)"
        pip_user_bin=$(python3 -m site --user-base)/bin
        if [[ ":$PATH:" != *":$pip_user_bin:"* ]]; then
            warn "Add to your shell profile:"
            echo "    export PATH=\"$pip_user_bin:\$PATH\""
        fi
    fi
    echo ""
    echo -e "${BOLD}Install complete! Verify with:${RESET}"
    echo "  gb-ai-server --help"
    echo ""
fi


echo -e "${BOLD}Next steps:${RESET}"
echo ""
echo "  1. Configure your model:"
echo -e "     ${CYAN}edit .models.yaml${RESET}  (set HuggingFace GGUF repo ID)"
echo ""
echo "  2. Bootstrap (GPU):"
echo -e "     ${CYAN}make bootstrap${RESET}     # download + start + register"
echo ""
echo "  3. Or bootstrap (CPU-only):"
echo -e "     ${CYAN}make bootstrap-cpu-container${RESET}"
echo ""
echo "  4. Register with coding agents:"
echo -e "     ${CYAN}make bootstrap-register${RESET}   # Cline, OpenCode, Vibe, Pi"
echo ""
echo "  5. Health check:"
echo -e "     ${CYAN}curl http://localhost:8081/v1/models${RESET}"
echo ""


completion_hint() {
    local shell_name="$1"
    local rc_file="$2"
    local cmd="$3"

    if [ -f "$HOME/$rc_file" ] && ! grep -q "gb-ai-server" "$HOME/$rc_file" 2>/dev/null; then
        info "Optional: add tab-completion for $shell_name"
        info "  echo '$cmd' >> ~/$rc_file"
    fi
}

completion_hint "bash" ".bashrc"  'eval "$(_GB_AI_SERVER_COMPLETE=bash_source gb-ai-server)"'
completion_hint "zsh"  ".zshrc"   'eval "$(_GB_AI_SERVER_COMPLETE=zsh_source gb-ai-server)"'
completion_hint "fish" ".config/fish/config.fish" 'gb-ai-server --fish-complete | source'

echo ""
echo -e "${GREEN}Done.${RESET}"
echo ""
