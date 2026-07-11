"""Register a custom HuggingFace model with all supported AI coding agents."""

from __future__ import annotations

from gb_ai_server.infrastructure.persistence.templates import register_all
from gb_ai_server.infrastructure.persistence.fetch_hf_ctx import fetch_safe_ctx_size


def register_custom_model(repo_id: str, ctx_size: int = 0) -> dict[str, bool]:
    """Register a HuggingFace model with all agents.

    Args:
        repo_id: HuggingFace repo (e.g. 'unsloth/Qwen3-14B-GGUF')
        ctx_size: Context window override (0 = compute from HF config + VRAM)

    When ctx_size is 0 (default), the context window is computed from the
    model's HuggingFace config.json using the actual KV cache formula against
    the available VRAM — so the registered limit always matches what the server
    can actually run.

    Returns {agent_name: success}.
    """
    display_name = repo_id.split("/")[-1]
    container_name = repo_id.replace("/", "-").lower()

    if ctx_size == 0:
        ctx_size = fetch_safe_ctx_size(repo_id)

    return register_all(display_name, container_name, ctx_size)
