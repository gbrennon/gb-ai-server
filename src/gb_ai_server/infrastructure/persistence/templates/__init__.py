"""Template registry — discover and run all agent registration templates.

Add a new agent by dropping a .py file here with a register() function:

    def register(display_name: str, container_name: str, ctx_size: int, port: int) -> bool:
        ...

Return True on success, False if the agent is not installed (skip silently).
"""

from __future__ import annotations

import importlib
import pkgutil
from pathlib import Path


def discover_templates() -> list:
    """Discover all template modules in this directory (excluding __init__)."""
    modules = []
    package_dir = Path(__file__).parent
    for _, name, is_pkg in pkgutil.iter_modules([str(package_dir)]):
        if name == "__init__" or is_pkg:
            continue
        try:
            mod = importlib.import_module(f"gb_ai_server.infrastructure.persistence.templates.{name}")
            if hasattr(mod, "register"):
                modules.append((name, mod))
        except ImportError:
            pass
    return modules


def register_all(
    display_name: str,
    container_name: str,
    ctx_size: int,
    port: int = 8081,
) -> dict[str, bool]:
    """Run register() on all discovered templates. Returns {agent_name: success}."""
    results: dict[str, bool] = {}
    for name, mod in discover_templates():
        try:
            results[name] = mod.register(display_name, container_name, ctx_size, port)
        except Exception:
            results[name] = False
    return results
