"""CLI entry point for the llama.cpp bootstrap."""

import os
import argparse
import sys
from pathlib import Path

from gb_ai_server.infrastructure import Environment
from gb_ai_server.infrastructure.di.container import (
    InfrastructureRegistry,
    VerifierFactory,
    ComposeServiceFactory,
    ModelServiceFactory,
)
from gb_ai_server.presentation.composer import BootstrapCompositionRoot
from gb_ai_server.presentation.parser import load_models


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="gb-ai-server",
        description="Initialize llama.cpp stack with Docker/Podman",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview actions without making changes",
    )
    parser.add_argument(
        "--skip-download",
        action="store_true",
        help="Skip model downloading (assume already downloaded)",
    )
    parser.add_argument(
        "--skip-health",
        action="store_true",
        help="Skip health verification (faster startup)",
    )
    parser.add_argument(
        "--models-dir",
        type=str,
        default=None,
        help="Colon-separated list of model directories (first is writable). "
             "Overrides MODEL_DIRS and MODELS_DIR env vars.",
    )
    parser.add_argument(
        "--hf-token",
        type=str,
        default=None,
        help="HuggingFace token for gated repositories",
    )
    parser.add_argument(
        "--register",
        action="store_true",
        help="Register model from .models.yaml with all agents",
    )
    parser.add_argument(
        "--register-custom",
        type=str,
        default=None,
        metavar="REPO_ID",
        help="Register a custom HF model with all agents (e.g. unsloth/Qwen3-14B-GGUF)",
    )
    parser.add_argument(
        "--ctx-size",
        type=int,
        default=0,
        help="Context window size for --register-custom (0 = auto-detect)",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging",
    )
    return parser


def _normalize_models_dirs(args: argparse.Namespace) -> None:
    raw: str | None = args.models_dir
    raw = raw or os.getenv("MODEL_DIRS") or os.getenv("MODELS_DIR")
    if not raw:
        raw = "/tmp/llama_models"
    parts = [Path(d.strip()) for d in raw.split(":") if d.strip()]
    if not parts:
        parts = [Path("/tmp/llama_models")]
    args.models_dirs = parts
    args.models_dir = parts[0]


def main(argv: list[str] | None = None) -> int:
    Environment.load_env_file(Path(".env"))
    parser = build_parser()
    args = parser.parse_args(argv)
    _normalize_models_dirs(args)

    # Custom model registration (all agents)
    if args.register_custom:
        return _register_custom(args)

    # Register from .models.yaml (all agents)
    if args.register:
        return _register_from_config(args)

    infra = InfrastructureRegistry()
    root = BootstrapCompositionRoot(
        infrastructure=infra,
        verifiers=VerifierFactory(infra),
        compose=ComposeServiceFactory(infra),
        models=ModelServiceFactory(infra),
    )
    return root.run(args)


def _register_custom(args: argparse.Namespace) -> int:
    """Register a custom HuggingFace model with all agents."""
    from gb_ai_server.application.services.register_custom_model_service import (
        register_custom_model,
    )

    results = register_custom_model(args.register_custom, args.ctx_size)
    if not results:
        print("No agents registered")
        return 1

    for agent, ok in sorted(results.items()):
        print(f"  [OK] {agent}" if ok else f"  [--] {agent}")
    print(f"\nModel registered with {sum(results.values())}/{len(results)} agents")
    return 0


def _register_from_config(args: argparse.Namespace) -> int:
    """Register the model from .models.yaml with all agents."""
    env_root = Path(".").resolve()
    config_path = env_root / ".models.yaml"
    if not config_path.exists():
        print("No .models.yaml found", file=sys.stderr)
        return 1

    models = load_models(config_path)
    if not models:
        print("No model configured", file=sys.stderr)
        return 1

    model = models[0]

    from gb_ai_server.application.services.register_custom_model_service import (
        register_custom_model,
    )

    # Extract repo ID from URL or display name
    repo_id = model.url.split("huggingface.co/")[-1].split("/resolve/")[0] if "huggingface.co" in model.url else model.display_name

    # Pass 0 so register_custom_model computes the safe context from HF config +
    # available VRAM. The explicit ctx_size in .models.yaml is for the server
    # startup only; for registration we always want the hardware-aware value.
    results = register_custom_model(repo_id, 0)
    if not results:
        print("No agents registered")
        return 1

    for agent, ok in sorted(results.items()):
        print(f"  {'✅' if ok else '❌'} {agent}")
    print(f"\nModel {model.display_name} registered with {sum(results.values())}/{len(results)} agents")
    return 0


if __name__ == "__main__":
    sys.exit(main())
