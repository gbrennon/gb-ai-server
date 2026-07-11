"""Probe hardware capabilities — VRAM, RAM, GPU availability."""

from __future__ import annotations

import subprocess
from dataclasses import dataclass


@dataclass
class HardwareInfo:
    gpu_name: str = ""
    vram_total_mb: int = 0
    vram_free_mb: int = 0
    ram_total_mb: int = 0
    gpu_available: bool = False
    cdi_active: bool = False


def probe_hardware() -> HardwareInfo:
    """Detect GPU and system RAM for model fit checking."""
    info = HardwareInfo()

    # GPU via nvidia-smi
    try:
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=name,memory.total,memory.free",
             "--format=csv,noheader,nounits"],
            capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0:
            parts = result.stdout.strip().split(",")
            if len(parts) >= 3:
                info.gpu_name = parts[0].strip()
                info.vram_total_mb = int(parts[1].strip())
                info.vram_free_mb = int(parts[2].strip())
                info.gpu_available = True
    except (FileNotFoundError, subprocess.TimeoutExpired, ValueError):
        pass

    # CDI check
    try:
        result = subprocess.run(
            ["nvidia-ctk", "cdi", "list"],
            capture_output=True, text=True, timeout=5
        )
        info.cdi_active = result.returncode == 0 and "gpu" in result.stdout.lower()
    except FileNotFoundError:
        pass

    # System RAM
    try:
        with open("/proc/meminfo") as f:
            for line in f:
                if line.startswith("MemTotal:"):
                    info.ram_total_mb = int(line.split()[1]) // 1024
                    break
    except OSError:
        pass

    return info


def model_fits(hw: HardwareInfo, model_size_gb: float, ctx_size: int,
               gguf_path: str = "") -> tuple[bool, str]:
    """Check if a model fits on this hardware.

    Returns (fits, reason).
    Uses GGUF metadata for accurate KV cache estimation when available.
    Falls back to ~0.05 MB/token heuristic.
    """
    # Try dynamic KV cache estimate from GGUF metadata
    # llama.cpp uses rolling buffer + Q8_0 KV cache — only a fraction of
    # full ctx_size is allocated at any time. Empirical: ~0.4 GB for 40960 ctx.
    kv_cache_gb = 1.0
    if gguf_path:
        try:
            from gb_ai_server.infrastructure.persistence.gguf_reader import kv_cache_mb_per_token
            mb_per_token = kv_cache_mb_per_token(gguf_path)
            if mb_per_token:
                # Q8_0 (x0.5) + rolling buffer (x0.05 of full context)
                kv_cache_gb = max(0.5, (mb_per_token * 0.5 * 0.05 * ctx_size) / 1024)
        except Exception:
            pass
    else:
        kv_cache_gb = max(0.5, ctx_size * 0.00001)

    vram_needed_gb = model_size_gb + kv_cache_gb + 0.5
    vram_free_gb = hw.vram_free_mb / 1024

    if hw.gpu_available and hw.cdi_active:
        if vram_needed_gb <= vram_free_gb:
            return True, f"GPU: {vram_needed_gb:.1f} GB needed, {vram_free_gb:.1f} GB free"
        else:
            return False, (
                f"GPU: {vram_needed_gb:.1f} GB needed, "
                f"only {vram_free_gb:.1f} GB free. "
                f"Try a smaller quantization (e.g. Q3_K_M, Q2_K)"
            )

    ram_free_gb = hw.ram_total_mb / 1024 * 0.5
    if model_size_gb <= ram_free_gb:
        return True, f"CPU: {model_size_gb:.1f} GB model, {ram_free_gb:.0f} GB RAM free (slow)"
    return False, f"CPU: {model_size_gb:.1f} GB model too large for {ram_free_gb:.0f} GB free RAM"
