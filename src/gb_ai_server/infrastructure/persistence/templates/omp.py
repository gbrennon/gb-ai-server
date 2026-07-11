"""omp (Oh My Pi) agent template — ~/.omp/agent/models.yml + config.yml

Registers:
  - llama.cpp local provider with discovery
  - openai → localhost override (redirects advisor's gpt-5.5 calls)
  - cline provider (if CLINE_USER_KEY env var is set)
  - Model roles: plan/smol → local, default/task/slow → cline (or local fallback)
  - Advisor: local model, subagents enabled
  - Sampling params tuned for GGUF models
  - Plan mode off on startup (7B models get confused)
"""

from __future__ import annotations

import json
import os
import urllib.request
from pathlib import Path

LLAMA_PROVIDER = "llama.cpp"
CLINE_PROVIDER = "cline"
OPENAI_PROVIDER = "openai"

# Sampling params tuned for GGUF models — avoids repetition loops
GGUF_SAMPLING = {
    "temperature": 0.7,
    "topP": 0.9,
    "topK": 40,
    "minP": 0.05,
    "presencePenalty": 0,
    "repetitionPenalty": 1.1,
}


def _omp_dir() -> Path:
    env = os.environ.get("OMP_CONFIG_DIR", "")
    return Path(env) / "agent" if env else Path.home() / ".omp" / "agent"


def _read_yaml(path: Path) -> dict:
    """Read a YAML file, returning {} if missing/invalid."""
    if not path.exists():
        return {}
    try:
        import yaml  # type: ignore[import-untyped]
        with open(path) as f:
            return yaml.safe_load(f) or {}
    except Exception:
        return {}


def _write_yaml(path: Path, data: dict) -> None:
    """Write a dict as YAML, preserving block style for readability."""
    import yaml  # type: ignore[import-untyped]

    class _BlockStr(str):
        pass

    def _block_representer(dumper, data):
        return dumper.represent_scalar("tag:yaml.org,2002:str", data, style="|")

    yaml.add_representer(_BlockStr, _block_representer)

    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        yaml.dump(data, f, default_flow_style=False, allow_unicode=True, sort_keys=False, width=120)


def _probe_server_ctx(port: int) -> int | None:
    """Ask llama.cpp server what n_ctx it actually runs with."""
    try:
        with urllib.request.urlopen(f"http://localhost:{port}/props", timeout=3) as resp:
            data = json.loads(resp.read())
            gen = data.get("default_generation_settings", {})
            n_ctx = gen.get("n_ctx") or gen.get("params", {}).get("n_ctx")
            return int(n_ctx) if n_ctx else None
    except Exception:
        return None


def _probe_model_id(port: int) -> str | None:
    """Ask llama.cpp /v1/models for the actual model ID (GGUF filename)."""
    try:
        with urllib.request.urlopen(f"http://localhost:{port}/v1/models", timeout=3) as resp:
            data = json.loads(resp.read())
            models = data.get("data", [])
            if models:
                return models[0].get("id") or models[0].get("model")
    except Exception:
        pass
    return None


def _has_cline_key() -> bool:
    return bool(os.environ.get("CLINE_USER_KEY", "").startswith("sk_"))


def register(display_name: str, container_name: str, ctx_size: int, port: int = 8081) -> bool:
    omp_dir = _omp_dir()
    omp_dir.mkdir(parents=True, exist_ok=True)

    actual_ctx = _probe_server_ctx(port) or ctx_size
    model_id = _probe_model_id(port) or container_name

    # ── models.yml ──────────────────────────────────────────────
    models_path = omp_dir / "models.yml"
    models = _read_yaml(models_path)
    models.setdefault("providers", {})
    models.setdefault("equivalence", {}).setdefault("overrides", {})

    # llama.cpp provider — always present, with discovery
    models["providers"][LLAMA_PROVIDER] = {
        "baseUrl": f"http://127.0.0.1:{port}",
        "api": "openai-responses",
        "auth": "none",
        "discovery": {"type": "llama.cpp"},
    }

    # openai → localhost override — redirects advisor's gpt-5.5 calls
    models["providers"][OPENAI_PROVIDER] = {
        "baseUrl": f"http://127.0.0.1:{port}",
        "api": "openai-responses",
        "auth": "none",
    }

    # cline provider — only if CLINE_USER_KEY is set
    if _has_cline_key():
        models["providers"].setdefault(CLINE_PROVIDER, {})
        models["providers"][CLINE_PROVIDER] = {
            "baseUrl": "https://api.cline.bot/api/v1",
            "api": "openai-completions",
            "apiKey": "CLINE_USER_KEY",
            "auth": "apiKey",
            "models": [
                {
                    "id": "deepseek/deepseek-v4-pro",
                    "name": "DeepSeek V4 Pro (Cline)",
                    "reasoning": True,
                    "input": ["text"],
                    "contextWindow": 128000,
                    "maxTokens": 32000,
                }
            ],
        }

    _write_yaml(models_path, models)

    # ── config.yml ──────────────────────────────────────────────
    config_path = omp_dir / "config.yml"
    config = _read_yaml(config_path)

    local_full = f"{LLAMA_PROVIDER}/{model_id}"
    cline_full = f"{CLINE_PROVIDER}/deepseek/deepseek-v4-pro" if _has_cline_key() else local_full

    # Model roles
    config.setdefault("modelRoles", {})
    roles = config["modelRoles"]
    roles.setdefault("plan", local_full)
    roles.setdefault("smol", local_full)
    roles.setdefault("task", cline_full)
    roles.setdefault("default", cline_full)
    roles.setdefault("slow", cline_full)

    # Advisor
    config.setdefault("advisor", {})
    advisor = config["advisor"]
    advisor.setdefault("enabled", True)
    advisor.setdefault("subagents", True)
    advisor.setdefault("model", local_full)

    # Sampling params (GGUF-friendly)
    for key, value in GGUF_SAMPLING.items():
        config.setdefault(key, value)

    # Plan mode off on startup
    config.setdefault("plan", {})
    config["plan"].setdefault("defaultOnStartup", False)

    _write_yaml(config_path, config)

    return True
