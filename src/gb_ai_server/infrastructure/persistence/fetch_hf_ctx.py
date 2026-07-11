"""Fetch and compute context window from HuggingFace model config."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

# Keys tried in order when reading max native context from config.json
_CTX_KEYS = [
    "max_position_embeddings",
    "model_max_length",
    "n_positions",
    "n_ctx",
    "max_sequence_length",
]


def _load_hf_config(repo_id: str) -> dict | None:
    """Download and parse config.json from a HuggingFace repo."""
    try:
        from huggingface_hub import hf_hub_download
        config_path = hf_hub_download(repo_id=repo_id, filename="config.json")
        return json.loads(Path(config_path).read_text())
    except Exception:
        return None


def fetch_context_window(repo_id: str) -> int | None:
    """Return the native (maximum) context window for a HF repo.

    Priority:
      1. config.json from HuggingFace (authoritative)
      2. model_info card_data (fallback for repos without config.json)
      3. Local GGUF binary metadata (offline fallback)
    """
    config = _load_hf_config(repo_id)
    if config:
        for key in _CTX_KEYS:
            if key in config:
                return int(config[key])

    try:
        from huggingface_hub import model_info
        info = model_info(repo_id)
        if info.card_data:
            for key in ("max_position_embeddings", "context_length", "model_max_length"):
                if key in info.card_data:
                    return int(info.card_data[key])
    except Exception:
        pass

    from .gguf_reader import read_context_window
    vol = os.path.expanduser("~/.local/share/containers/storage/volumes/llama_models/_data")
    if os.path.isdir(vol):
        for f in os.listdir(vol):
            if f.endswith(".gguf"):
                ctx = read_context_window(os.path.join(vol, f))
                if ctx:
                    return ctx

    return None


def _find_local_gguf(repo_id: str) -> str | None:
    """Return the path to the local GGUF file for this repo.

    Matches by repo name fragment (case-insensitive) across all configured
    model directories and the podman volume path.
    """
    # Build a lowercase search token from the repo name (strip '-GGUF')
    repo_name = repo_id.split("/")[-1].replace("-GGUF", "").replace("-gguf", "").lower()

    search_dirs: list[str] = []
    raw = os.environ.get("MODEL_DIRS") or os.environ.get("MODELS_DIR") or ""
    for d in raw.split(":"):
        d = d.strip()
        if d:
            search_dirs.append(os.path.expanduser(d))
    search_dirs.append(
        os.path.expanduser("~/.local/share/containers/storage/volumes/llama_models/_data")
    )

    best: str | None = None
    for directory in search_dirs:
        if not os.path.isdir(directory):
            continue
        for f in os.listdir(directory):
            if not f.endswith(".gguf"):
                continue
            # Prefer files whose name contains the repo name fragment
            if repo_name in f.lower():
                return os.path.join(directory, f)
            # Keep as fallback (any .gguf)
            if best is None:
                best = os.path.join(directory, f)
    return best


def _estimate_model_size_mb(repo_id: str) -> int:
    """Return size in MiB of the local GGUF file for this repo, or 0."""
    path = _find_local_gguf(repo_id)
    if path:
        try:
            size_mb = os.path.getsize(path) // (1024 * 1024)
            if size_mb > 100:
                return size_mb
        except OSError:
            pass
    return 0


def fetch_safe_ctx_size(repo_id: str) -> int:
    """Compute the largest context that fits in VRAM using HF config.json.

    Uses the model architecture from config.json (fetched via huggingface_hub)
    to derive the exact KV cache cost per token:

      bytes_per_token = 2 × n_layers × n_kv_heads × head_dim × 2  (fp16 K+V)

    Then computes:
      available_for_kv = vram_total - model_weights_size - 256 MiB overhead
      safe_ctx = floor(available_for_kv / mb_per_token), aligned to 256 tokens

    Clamped to the model's native max_position_embeddings.
    Falls back to fetch_context_window() when config data is missing.
    """
    # Probe GPU — use total VRAM so the calculation is independent of
    # whether the server is currently running or not.
    vram_total_mb = 0
    try:
        from .hardware_prober import probe_hardware
        hw = probe_hardware()
        vram_total_mb = hw.vram_total_mb if hw.vram_total_mb > 0 else 0
    except Exception:
        pass

    # Try GGUF repo config first, then base repo (strips '-GGUF' suffix)
    config = _load_hf_config(repo_id)
    if config is None and repo_id.upper().endswith("-GGUF"):
        config = _load_hf_config(repo_id[: -len("-GGUF")])

    if config is None or vram_total_mb <= 0:
        native = fetch_context_window(repo_id)
        return native if native else 8192

    n_layers: int | None = config.get("num_hidden_layers")
    n_kv_heads: int | None = config.get("num_key_value_heads")
    n_heads: int | None = config.get("num_attention_heads")
    head_dim: int | None = config.get("head_dim")
    native_ctx: int = int(config.get("max_position_embeddings", 0))

    if head_dim is None and n_heads and config.get("hidden_size"):
        head_dim = config["hidden_size"] // n_heads

    if not all([n_layers, n_kv_heads, head_dim, native_ctx]):
        native = fetch_context_window(repo_id)
        return native if native else 8192

    model_size_mb = _estimate_model_size_mb(repo_id)
    bytes_per_token = 2 * n_layers * n_kv_heads * head_dim * 2  # fp16 K+V
    mb_per_token = bytes_per_token / (1024 * 1024)

    # 1024 MiB safety margin: CUDA runtime, activations, scratch buffers.
    # Empirical testing showed 256 MiB is insufficient for 14B models on 12 GB GPUs.
    available_for_kv_mb = vram_total_mb - model_size_mb - 1024
    if available_for_kv_mb <= 0:
        return 2048

    max_ctx_from_vram = int(available_for_kv_mb / mb_per_token)
    safe_ctx = min(max_ctx_from_vram, native_ctx)
    safe_ctx = (safe_ctx // 256) * 256  # align to 256-token boundary
    return max(safe_ctx, 2048)


def main() -> int:
    """CLI entry point for standalone usage."""
    if len(sys.argv) < 2:
        print("Usage: fetch-hf-ctx <repo_id>", file=sys.stderr)
        return 1
    ctx = fetch_context_window(sys.argv[1])
    if ctx is None:
        return 1
    print(ctx)
    return 0


if __name__ == "__main__":
    sys.exit(main())
