"""Resolve model info from HuggingFace — files, sizes, context window, best quant."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ...application.ports.outbound.logger import Logger


@dataclass
class ResolvedModel:
    repo_id: str
    filename: str
    download_url: str
    size_gb: float
    context_window: int
    quantization: str


def _parse_size(size_str: str) -> float | None:
    """Parse '8.4 GB' or '12345678' to GB float."""
    if not size_str:
        return None
    try:
        return float(size_str) / 1e9
    except ValueError:
        m = re.match(r"([\d.]+)\s*(GB|MB|TB)?", size_str, re.IGNORECASE)
        if m:
            val = float(m.group(1))
            unit = (m.group(2) or "GB").upper()
            if unit == "TB":
                return val * 1000
            if unit == "MB":
                return val / 1000
            return val
    return None


def _rank_quant(filename: str) -> int:
    """Rank quantization quality — lower is smaller/faster."""
    upper = filename.upper()
    if "Q4_K_M" in upper:
        return 3
    if "Q4_K_S" in upper:
        return 2
    if "Q3_K_M" in upper:
        return 1
    if "Q2_K" in upper:
        return 0
    if "Q5_K_M" in upper:
        return 4
    if "Q6_K" in upper:
        return 5
    if "Q8_0" in upper:
        return 6
    if "BF16" in upper or "F16" in upper:
        return 7
    return -1


def _fetch_context_window(repo_id: str) -> int:
    """Get the native max context window for a HF repo via fetch_hf_ctx."""
    from .fetch_hf_ctx import fetch_context_window
    return fetch_context_window(repo_id) or 32768


def resolve_model(repo_id: str, vram_gb: float = 12.0) -> ResolvedModel | None:
    """Resolve a HuggingFace model: find best GGUF, get size, context window.

    Args:
        repo_id: HuggingFace repo (e.g. 'unsloth/Qwen3-14B-GGUF')
        vram_gb: Available VRAM for fit-based quantization selection

    Returns ResolvedModel or None if nothing suitable found.
    """
    try:
        from huggingface_hub import list_repo_files, model_info
    except ImportError:
        return None

    # List GGUF files
    try:
        files = [f for f in list_repo_files(repo_id) if f.endswith(".gguf")]
    except Exception as e:
        # Check if the repo exists but has no GGUFs
        error_msg = str(e).lower()
        if "404" in error_msg or "not found" in error_msg:
            print(f"  Repo '{repo_id}' not found on HuggingFace")
        else:
            try:
                all_files = list(list_repo_files(repo_id))
                non_gguf = [f for f in all_files if not f.endswith(".gguf")][:5]
                print(f"  Repo '{repo_id}' has no GGUF files")
                print(f"    Found: {', '.join(non_gguf)}...")
                if not repo_id.endswith("-GGUF"):
                    suggested = f"{repo_id}-GGUF"
                    print(f"    Try: {suggested}")
            except Exception:
                print(f"  Cannot access repo '{repo_id}': {e}")
        return None

    if not files:
        # Repo exists but has no GGUF files
        if not repo_id.endswith("-GGUF"):
            suggested = f"{repo_id}-GGUF"
            print(f"  Repo '{repo_id}' has no GGUF files.")
            print(f"  Try: {suggested}")
        return None

    # Get file sizes from model_info
    file_sizes: dict[str, float] = {}
    try:
        info = model_info(repo_id)
        if hasattr(info, "siblings") and info.siblings:
            for s in info.siblings:
                if s.rfilename in files:
                    sz = getattr(s, "size", 0) or 0
                    if sz > 0:
                        file_sizes[s.rfilename] = sz / 1e9
    except Exception:
        pass

    # Fallback: estimate sizes from quantization + model parameter count
    if not file_sizes:
        # Extract parameter count from repo name (e.g. "7B", "14B", "24B")
        params_gb = 29.0  # default for 14B
        for token in repo_id.upper().replace("-", " ").split():
            if token.endswith("B") and token[:-1].isdigit():
                b = int(token[:-1])
                params_gb = b * 2.0  # ~2 GB per billion params in BF16
                break
        for f in files:
            upper = f.upper()
            if "Q4_K_M" in upper or "Q4_K_S" in upper:
                file_sizes[f] = params_gb * 0.28
            elif "Q3_K" in upper:
                file_sizes[f] = params_gb * 0.22
            elif "Q2_K" in upper:
                file_sizes[f] = params_gb * 0.17
            elif "Q5_K" in upper:
                file_sizes[f] = params_gb * 0.33
            elif "Q6_K" in upper:
                file_sizes[f] = params_gb * 0.38
            elif "Q8_0" in upper:
                file_sizes[f] = params_gb * 0.50
            elif "BF16" in upper or "F16" in upper:
                file_sizes[f] = params_gb * 1.0
            else:
                file_sizes[f] = params_gb * 0.28

    # Sort by: fits in VRAM first, then best quality
    # Exclude BF16/F16 for small GPUs (they're the raw unquantized weights)
    ranked = []
    for f in files:
        sz = file_sizes.get(f, 999)
        rank = _rank_quant(f)
        # Skip BF16/F16 if VRAM is limited (< 24 GB)
        if rank >= 6 and vram_gb < 24:
            continue
        fits = sz + 2.0 <= vram_gb  # model + KV cache overhead
        ranked.append((fits, rank, sz, f))

    ranked.sort(key=lambda x: (-x[0], -x[1]))  # fits first, then quality

    if not ranked:
        return None

    best_file = ranked[0][3]
    best_size = ranked[0][2]
    best_quant = _rank_quant(best_file)
    ctx = _fetch_context_window(repo_id)

    quant_names = {0: "Q2_K", 1: "Q3_K_M", 2: "Q4_K_S", 3: "Q4_K_M",
                   4: "Q5_K_M", 5: "Q6_K", 6: "Q8_0", 7: "BF16"}

    return ResolvedModel(
        repo_id=repo_id,
        filename=best_file,
        download_url=f"https://huggingface.co/{repo_id}/resolve/main/{best_file}",
        size_gb=best_size,
        context_window=ctx,
        quantization=quant_names.get(best_quant, "unknown"),
    )
