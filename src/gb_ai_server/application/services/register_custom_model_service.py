"""Register a custom HuggingFace model with all supported AI coding agents."""

from __future__ import annotations

from gb_ai_server.infrastructure.persistence.templates import register_all
from gb_ai_server.infrastructure.persistence.fetch_hf_ctx import (
    fetch_safe_ctx_size,
    fetch_model_metadata,
)


def _calculate_gpu_layers(repo_id: str) -> int:
    """Calculate how many transformer layers fit on GPU for this model.

    Uses GPULayerCalculator with metadata from HuggingFace config.json
    and available VRAM from hardware probing. Returns 999 (all layers)
    when metadata or VRAM is unavailable.
    """
    from gb_ai_server.domain.gpu_layer_calculator import GPULayerCalculator
    from gb_ai_server.infrastructure.persistence.hardware_prober import probe_hardware

    metadata = fetch_model_metadata(repo_id)
    if metadata is None:
        return 999

    hw = probe_hardware()
    if hw.vram_total_mb <= 0:
        return 999

    calc = GPULayerCalculator(metadata)
    result = calc.calculate_gpu_layers(hw.vram_total_mb)
    return result.gpu_layers


def register_custom_model(repo_id: str, ctx_size: int = 0) -> dict[str, bool]:
    """Register a HuggingFace model with all agents.

    Args:
        repo_id: HuggingFace repo (e.g. 'unsloth/Qwen3-14B-GGUF')
        ctx_size: Context window override (0 = compute from HF config + VRAM)

    When ctx_size is 0 (default), the context window is computed from the
    model's HuggingFace config.json using the actual KV cache formula against
    the available VRAM. GPU layer count is also calculated from model
    architecture metadata and available VRAM.

    Returns {agent_name: success}.
    """
    display_name = repo_id.split("/")[-1]
    container_name = repo_id.replace("/", "-").lower()

    if ctx_size == 0:
        ctx_size = fetch_safe_ctx_size(repo_id)

    n_gpu_layers = _calculate_gpu_layers(repo_id)

    return register_all(display_name, container_name, ctx_size, n_gpu_layers=n_gpu_layers)
