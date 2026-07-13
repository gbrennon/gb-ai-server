"""Model configuration file parser (YAML .models.yaml)."""

from __future__ import annotations

from pathlib import Path

from gb_ai_server.domain import ModelEntry


def load_models(config_path: Path) -> list[ModelEntry]:
    """Parse .models.yaml into ModelEntry instances.

    Format:
        model:
          id: unsloth/Qwen3-14B-GGUF     # required
          file: Qwen3-14B-Q4_K_M.gguf    # optional (auto-detected)
          gpu_layers: 999                # optional (ignored — calculated at runtime)
          ctx_size: 0                    # optional (ignored — calculated at runtime)
    """
    import yaml

    if not config_path.exists():
        raise ValueError(f"Model config not found: {config_path}")

    with open(config_path) as f:
        data = yaml.safe_load(f)

    if not data or "model" not in data:
        raise ValueError(f"Invalid model config: missing 'model' key in {config_path}")

    m = data["model"]
    repo_id = m.get("id", "")
    if not repo_id:
        raise ValueError(f"Invalid model config: missing 'id' in {config_path}")

    # If file is specified, use it. Otherwise resolve best quant from HF.
    # gpu_layers and ctx_size from YAML are ignored — both are calculated
    # at runtime from HF config.json + available VRAM.
    filename = m.get("file", "")
    url = ""

    if not filename:
        from gb_ai_server.infrastructure.persistence.hf_model_resolver import resolve_model
        from gb_ai_server.infrastructure.persistence.hardware_prober import probe_hardware

        hw = probe_hardware()
        vram_gb = hw.vram_total_mb / 1024 if hw.vram_total_mb > 0 else 12.0
        resolved = resolve_model(repo_id, vram_gb=vram_gb)

        if resolved is None:
            raise ValueError(
                f"Could not load model from '{repo_id}'. "
                f"GGUF repos on HuggingFace usually end with '-GGUF' "
                f"(e.g. unsloth/Qwen3-14B-GGUF)."
            )

        filename = resolved.filename
        url = resolved.download_url

        print(f"  Resolved from HF: {resolved.filename}")
        print(f"    Size: {resolved.size_gb:.1f} GB")
        print(f"    Quant: {resolved.quantization}")

    if not url:
        url = f"https://huggingface.co/{repo_id}/resolve/main/{filename}"

    display_name = repo_id.split("/")[-1]

    return [ModelEntry(
        display_name=display_name,
        filename=filename,
        url=url,
    )]
