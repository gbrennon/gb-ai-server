"""CLI entry point for the llama.cpp bootstrap."""

import os
import argparse
import sys
from pathlib import Path

from gb_ai_server.domain import PortAllocator
from gb_ai_server.infrastructure import ClineModelRegistrar, Environment
from gb_ai_server.infrastructure.di.container import Container
from gb_ai_server.infrastructure.logging import TerminalLogger
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
        type=Path,
        default=Path(os.getenv("MODELS_DIR", "/tmp/llama_models")),
        help="Directory for model files",
    )
    parser.add_argument(
        "--hf-token",
        type=str,
        default=None,
        help="HuggingFace token for gated repositories",
    )
    parser.add_argument(
        "--register-models",
        action="store_true",
        help="Register models with Cline (standalone, no bootstrap)",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    Environment.load_env_file(Path(".env"))
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.register_models:
        return _register_only(args)

    root = BootstrapCompositionRoot(Container())
    return root.run(args)


def _register_only(args: argparse.Namespace) -> int:
    container = Container()
    logger = container.logger
    env_root = Path(".").resolve()

    models_config = env_root / "scripts" / "models.conf.sh"
    if not models_config.exists():
        logger.error("No models.conf.sh found")
        return 1

    models = load_models(models_config)
    if not models:
        logger.warn("No models configured")
        return 0

    # Map model index to container name based on docker-compose services
    container_names = _get_container_names(len(models))

    model_tuples = [
        (m.display_name, m.filename, port, container_name)
        for m, port, container_name in zip(
            models,
            PortAllocator.ports_for_models(len(models)),
            container_names,
        )
    ]

    registrar = ClineModelRegistrar(logger)
    service = container.model_registrar(registrar)

    from gb_ai_server.application.dtos.requests.register_models_request import RegisterModelsRequest
    request = RegisterModelsRequest(models=model_tuples)
    response = service.execute(request)

    if response.success:
        first = model_tuples[0]
        logger.ok(f"Registered {first[0]} with Cline (http://localhost:{first[2]})")
        return 0

    logger.warn("Failed to register models with Cline")
    return 1


def _get_container_names(model_count: int) -> list[str]:
    """Get container names for each model based on docker-compose service definitions."""
    # Default container names matching docker-compose.yml
    default_containers = ["llama-coder", "llama-qwen3", "llama-devs"]
    return default_containers[:model_count]


if __name__ == "__main__":
    sys.exit(main())
