"""Pi agent template — ~/.pi/agent/models.json"""

from __future__ import annotations

import json
import os
import urllib.request
from pathlib import Path

PROVIDER_ID = "llama.cpp"

# Old provider IDs to clean up from previous registrations
STALE_PROVIDER_IDS = {"llama-coder", "local llama.cpp"}


def _pi_dir() -> Path:
    env = os.environ.get("PI_CONFIG_DIR", "")
    return Path(env) / "agent" if env else Path.home() / ".pi" / "agent"


def _read_json(path: Path) -> dict:
    if path.exists():
        try:
            return json.loads(path.read_text())
        except json.JSONDecodeError:
            pass
    return {}


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


def register(display_name: str, container_name: str, ctx_size: int, port: int = 8081, n_gpu_layers: int = 999) -> bool:
    pi_dir = _pi_dir()
    pi_dir.mkdir(parents=True, exist_ok=True)

    config_path = pi_dir / "models.json"
    config = _read_json(config_path)
    config.setdefault("providers", {})

    # Remove stale providers left from previous registrations
    for stale in STALE_PROVIDER_IDS:
        config["providers"].pop(stale, None)

    # Use actual server ctx if reachable, fallback to configured value
    actual_ctx = _probe_server_ctx(port) or ctx_size

    model_entry = {
        "id": container_name,
        "name": display_name,
        "reasoning": False,
        "input": ["text"],
        "cost": {"input": 0, "output": 0, "cacheRead": 0, "cacheWrite": 0},
        "contextWindow": actual_ctx,
        "maxTokens": min(actual_ctx, 65536),
    }

    config["providers"][PROVIDER_ID] = {
        "baseUrl": f"http://localhost:{port}/v1",
        "apiKey": os.environ.get("OPENAI_API_KEY", "dummy"),
        "api": "openai-completions",
        "models": [model_entry],
    }

    config_path.write_text(json.dumps(config, indent=2) + "\n")

    # Auth
    auth_file = pi_dir / "auth.json"
    auth = _read_json(auth_file)
    auth[PROVIDER_ID] = {
        **auth.get(PROVIDER_ID, {}),
        "key": os.environ.get("OPENAI_API_KEY", "dummy"),
    }
    auth_file.write_text(json.dumps(auth, indent=2) + "\n")

    return True
