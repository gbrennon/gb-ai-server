#!/usr/bin/env bash
# Self-documenting help parser for the Makefile.
# Reads the Makefile and pretty-prints targets tagged with ## comments.
# ##@ Section Name   → section header
# target: ## desc    → target with description

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MAKEFILE="$SCRIPT_DIR/../Makefile"

BOLD='\033[1m'
CYAN='\033[36m'
RESET='\033[0m'

echo -e "${BOLD}AI Code Models Stack — Podman Compose${RESET}"
echo ""
echo "Usage: make [target]"
echo ""

while IFS= read -r line; do
    # Section headers: ##@ Section Name
    if [[ "$line" =~ ^##@[[:space:]]+(.*) ]]; then
        echo ""
        echo -e "${BOLD}${BASH_REMATCH[1]}${RESET}"
        continue
    fi

    # Target with ## comment: target: ... ## description
    if [[ "$line" =~ ^([a-zA-Z_][a-zA-Z0-9_-]*):.*##[[:space:]]+(.*) ]]; then
        printf "  ${CYAN}%-22s${RESET} %s\n" "${BASH_REMATCH[1]}" "${BASH_REMATCH[2]}"
    fi
done < "$MAKEFILE"

echo ""