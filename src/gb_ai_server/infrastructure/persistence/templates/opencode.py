"""OpenCode agent template — opencode.json (project root)"""

from __future__ import annotations

import json
import os
import urllib.request
from pathlib import Path

PROVIDER_ID = "local llama.cpp"


def _find_project_root() -> Path | None:
    """Find the project root where opencode.json should live."""
    cwd = Path.cwd().resolve()
    for p in [cwd, *cwd.parents]:
        if (p / ".git").exists() or (p / "opencode.json").exists():
            return p
    return cwd


def _read_json(path: Path) -> dict:
    if path.exists():
        try:
            return json.loads(path.read_text())
        except json.JSONDecodeError:
            pass
    return {}


def _probe_server_ctx(port: int) -> int | None:
    """Ask the running llama.cpp server what n_ctx it actually started with."""
    try:
        with urllib.request.urlopen(f"http://localhost:{port}/props", timeout=3) as resp:
            data = json.loads(resp.read())
            gen = data.get("default_generation_settings", {})
            n_ctx = gen.get("n_ctx") or gen.get("params", {}).get("n_ctx")
            return int(n_ctx) if n_ctx else None
    except Exception:
        return None


def register(display_name: str, container_name: str, ctx_size: int, port: int = 8081) -> bool:
    project_root = _find_project_root()
    if project_root is None:
        return False

    # Use the actual server n_ctx when available — it's the ground truth.
    # Falls back to the configured ctx_size if the server isn't reachable yet.
    actual_ctx = _probe_server_ctx(port) or ctx_size

    config_path = project_root / "opencode.json"
    config = _read_json(config_path)

    config.setdefault("$schema", "https://opencode.ai/config.json")
    config.setdefault("provider", {})

    # Preserve existing provider entry, create if new
    existing = config["provider"].get(PROVIDER_ID, {})

    config["provider"][PROVIDER_ID] = {
        "npm": "@ai-sdk/openai-compatible",
        "name": "Llama Coder (local)",
        "options": {
            **existing.get("options", {}),
            "baseURL": f"http://localhost:{port}/v1",
        },
        "models": {
            container_name: {
                "name": display_name,
                "limit": {
                    "context": actual_ctx,
                    "output": min(actual_ctx, 65536),
                },
            },
        },
    }

    config_path.write_text(json.dumps(config, indent=2) + "\n")

    # Auth file
    auth_dir = Path.home() / ".local" / "share" / "opencode"
    auth_dir.mkdir(parents=True, exist_ok=True)
    auth_file = auth_dir / "auth.json"

    auth = _read_json(auth_file)
    auth.setdefault(PROVIDER_ID, {})
    auth[PROVIDER_ID] = {
        **auth[PROVIDER_ID],
        "key": os.environ.get("OPENAI_API_KEY", "dummy"),
    }
    auth_file.write_text(json.dumps(auth, indent=2) + "\n")

    return True
