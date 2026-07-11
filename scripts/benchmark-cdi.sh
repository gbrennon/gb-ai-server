#!/usr/bin/env bash
# Benchmark CDI (GPU) vs no-CDI (CPU) for local llama model.
# Run: bash scripts/benchmark-cdi.sh
set -euo pipefail

API="http://localhost:8081/v1/chat/completions"
OUTDIR="docs/benchmarks"
mkdir -p "$OUTDIR"
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
GFILE="$OUTDIR/gpu-${TIMESTAMP}.json"
CFILE="$OUTDIR/cpu-${TIMESTAMP}.json"

PROMPTS=(
  '{"model":"local","messages":[{"role":"user","content":"Review this Python for bugs: def add(a,b): return a-b"}],"max_tokens":50,"temperature":0.2}'
  '{"model":"local","messages":[{"role":"user","content":"Explain Docker volumes in one sentence."}],"max_tokens":50,"temperature":0.2}'
  '{"model":"local","messages":[{"role":"user","content":"Fix this TS bug: function greet(n: string|null) { return n.toUpperCase() }"}],"max_tokens":50,"temperature":0.2}'
)

call_api() {
  local payload="$1"
  local start end elapsed
  start=$(date +%s%N)
  curl -s --max-time 120 "$API" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer dummy" \
    -d "$payload" 2>/dev/null
  end=$(date +%s%N)
  elapsed=$(( (end - start) / 1000000 ))  # ms
  echo "__ELAPSED_MS__=${elapsed}"
}

echo "🔥 CDI Benchmark"
echo "==============="
echo ""

# GPU mode (current)
echo ">>> GPU Mode (CDI active, N_GPU_LAYERS=10)"
echo ""
{
  for p in "${PROMPTS[@]}"; do
    echo "--- Prompt: $(echo $p | python3 -c 'import sys,json; print(json.load(sys.stdin)["messages"][0]["content"][:40])')"
    call_api "$p"
    sleep 2
  done
} | tee "$GFILE"

echo ""
echo ">>> Now switching to CPU mode (CDI inactive)..."
echo "    Stopping container..."
podman-compose -f docker-compose.yml down 2>/dev/null || true
sleep 3

echo "    Starting with N_GPU_LAYERS=0 (CPU only)..."
N_GPU_LAYERS=0 podman-compose -f docker-compose.yml --env-file .env up -d

echo "    Waiting for health check..."
for i in $(seq 1 30); do
  if curl -sf http://localhost:8081/health >/dev/null 2>&1; then
    echo "    Server ready"
    break
  fi
  sleep 2
done

echo ""
echo ">>> CPU Mode (CDI inactive, N_GPU_LAYERS=0)"
echo ""
{
  for p in "${PROMPTS[@]}"; do
    echo "--- Prompt: $(echo $p | python3 -c 'import sys,json; print(json.load(sys.stdin)["messages"][0]["content"][:40])')"
    call_api "$p"
    sleep 2
  done
} | tee "$CFILE"

echo ""
echo ">>> Restoring GPU mode..."
podman-compose -f docker-compose.yml --env-file .env down 2>/dev/null || true
sleep 3
podman-compose -f docker-compose.yml --env-file .env up -d
echo ""
echo "✅ Benchmark complete. Results saved to:"
echo "   GPU: $GFILE"
echo "   CPU: $CFILE"
