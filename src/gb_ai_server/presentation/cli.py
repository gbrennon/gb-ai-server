"""CLI entry point for the llama.cpp bootstrap."""

import os
import argparse
import sys
from pathlib import Path

from gb_ai_server.domain import PortAllocator
from gb_ai_server.infrastructure import ClineModelRegistrar, Environment
from gb_ai_server.infrastructure.di.container import (
    InfrastructureRegistry,
    VerifierFactory,
    ComposeServiceFactory,
    ModelServiceFactory,
)
from gb_ai_server.presentation.composer import BootstrapCompositionRoot
from gb_ai_server.presentation.parser import load_models
from gb_ai_server.application.utils import print_section
from gb_ai_server.presentation.presenter import (
    ModelSelectionPresenter,
)


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
    parser.add_argument(
        "--model",
        "-m",
        type=str,
        default=None,
        help="Model to host (display name from models.conf.sh)",
    )
    parser.add_argument(
        "--list-models",
        action="store_true",
        help="List available models and exit",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    Environment.load_env_file(Path(".env"))
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.list_models:
        return _list_models(args)

    if args.register_models:
        return _register_only(args)

    infra = InfrastructureRegistry()
    root = BootstrapCompositionRoot(
        infrastructure=infra,
        verifiers=VerifierFactory(infra),
        compose=ComposeServiceFactory(infra),
        models=ModelServiceFactory(infra),
    )
    return root.run(args)



def _list_models(args: argparse.Namespace) -> int:
    infra = InfrastructureRegistry()
    logger = infra.logger
    env_root = Path(".").resolve()

    models_config = env_root / "scripts" / "models.conf.sh"
    if not models_config.exists():
        logger.error("No models.conf.sh found")
        return 1

    models = load_models(models_config)
    if not models:
        logger.warn("No models configured")
        return 0

    print_section("Available Models")
    for m in models:
        logger.info(f"  {m.display_name:30s} {m.filename}")
    print()
    logger.info("Use: uv run gb-ai-server --model <name>")
    return 0


def _register_only(args: argparse.Namespace) -> int:
    infra = InfrastructureRegistry()
    logger = infra.logger
    model_sel = ModelSelectionPresenter(logger)
    env_root = Path(".").resolve()

    models_config = env_root / "scripts" / "models.conf.sh"
    if not models_config.exists():
        logger.error("No models.conf.sh found")
        return 1

    all_models = load_models(models_config)
    if not all_models:
        logger.warn("No models configured")
        return 0

    if args.model:
        selected = [m for m in all_models if m.display_name == args.model]
        if not selected:
            logger.error(f"Model '{args.model}' not found")
            return 1
        models = selected
    else:
        models = [all_models[0]]

    available = []
    for m in models:
        model_path = args.models_dir / m.filename
        if model_path.exists():
            available.append(m)
        else:
            model_sel.model_not_available(m.display_name, m.filename)

    if not available:
        logger.warn("No available models to register")
        return 0

    model_tuples = [
        (m.display_name, m.filename, PortAllocator.port_for_model(0), "llama-coder")
        for m in available
    ]

    registrar = ClineModelRegistrar(logger)
    models_factory = ModelServiceFactory(infra)
    service = models_factory.model_registrar(registrar)

    from gb_ai_server.application.dtos.requests.register_models_request import RegisterModelsRequest
    request = RegisterModelsRequest(models=model_tuples)
    response = service.execute(request)

    if response.success:
        for m in available:
            logger.ok(f"Registered {m.display_name} with Cline (http://localhost:{PortAllocator.port_for_model(0)})")
        return 0

    logger.warn("Failed to register models with Cline")
    return 1


if __name__ == "__main__":
    sys.exit(main())
