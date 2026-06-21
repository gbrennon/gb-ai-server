#!/usr/bin/env python3
"""
llama.cpp Bootstrap CLI.

Hexagonal architecture: domain → application → infrastructure.
Clean dependency injection, testable, no tight coupling.
"""

import argparse
import os
import sys
from pathlib import Path
import traceback

from gb_ai_server import (
    Logger,
    Environment,
    ModelEntry,
    PortAllocator,
    RuntimeDetector,
    ComposeToolDetector,
    PrerequisiteVerifier,
    ServiceOrchestrator,
    ModelCopier,
    HealthVerifier,
    ModelDownloader,
    HuggingFaceModelDownloader,
)
from gb_ai_server.application import ModelDownloadService


def load_models(models_conf_path: Path) -> list[ModelEntry]:
    """
    Load models from configuration file.

    Parses bash-format models.conf.sh file.

    Args:
        models_conf_path: Path to models.conf.sh.

    Returns:
        List of ModelEntry instances.

    Raises:
        ValueError: If config file invalid.
    """
    if not models_conf_path.exists():
        raise ValueError(f"Models config not found: {models_conf_path}")

    models: list[ModelEntry] = []

    with open(models_conf_path) as f:
        in_array = False
        for line in f:
            line = line.strip()

            # Start of MODELS array
            if line.startswith("MODELS=("):
                in_array = True
                line = line[8:]  # Remove "MODELS=("

            if not in_array:
                continue

            # End of array
            if line.endswith(")"):
                line = line[:-1]  # Remove closing paren
                in_array = False

            # Parse entry
            line = line.strip()
            if line and not line.startswith("#"):
                # Remove surrounding quotes
                line = line.strip('"\'')
                if line:
                    models.append(ModelEntry.from_string(line))

    return models


def main(argv: list[str] | None = None) -> int:
    """
    Main bootstrap workflow.

    Args:
        argv: Command-line arguments.

    Returns:
        Exit code (0 = success).
    """
    parser = argparse.ArgumentParser(
        prog="bootstrap",
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
        default=Path("/tmp/llama_models"),
        help="Directory for model files",
    )
    parser.add_argument(
        "--hf-token",
        type=str,
        default=None,
        help="HuggingFace token for gated repositories",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging",
    )

    args = parser.parse_args(argv)

    # Setup environment
    env = Environment.from_env()
    if args.debug:
        env.debug = True

    # Set HF_TOKEN from arg if provided
    if args.hf_token:
        os.environ["HF_TOKEN"] = args.hf_token

    logger = Logger()

    try:
        # Load configuration
        models = load_models(env.models_config_path)
        if not models:
            logger.error("No models configured")
            return 1

        # Verify prerequisites
        verifier = PrerequisiteVerifier(logger)
        if not verifier.verify_all(env.compose_file):
            logger.error("Prerequisites not met")
            return 1

        if not verifier.compose_tool or not verifier.container_runtime:
            logger.error("Failed to detect compose tool or runtime")
            return 1

        # Download models
        if not args.skip_download:
            # Infrastructure: concrete implementation
            hf_downloader = HuggingFaceModelDownloader(logger)
            # Application: orchestration service using domain protocol
            download_service = ModelDownloadService(logger, hf_downloader)

            results = download_service.download_models(
                models,
                args.models_dir,
                skip_existing=True,
                token=args.hf_token,
            )
            if not any(results.values()):
                logger.warn("All model downloads failed")
                return 1
        else:
            logger.info("Skipping model download (--skip-download)")

        # Start services
        orchestrator = ServiceOrchestrator(
            logger,
            verifier.compose_tool,
        )
        if not orchestrator.start_services(env.compose_file, "llama-coder"):
            logger.error("Failed to start services")
            return 1

        # Copy models to container
        copier = ModelCopier(logger, verifier.container_runtime)
        results = copier.copy_models(
            models,
            args.models_dir,
            "llama-coder",
        )
        if not any(results.values()):
            logger.warn("Failed to copy models to container")

        # Restart to load models
        if not orchestrator.restart_services(env.compose_file, "llama-coder"):
            logger.error("Failed to restart service")
            return 1

        # Verify health
        if not args.skip_health:
            verifier_svc = HealthVerifier(logger)
            ports = PortAllocator.ports_for_models(len(models))
            if not verifier_svc.verify_health(ports, timeout_seconds=60):
                logger.error("Health check failed")
                return 1

        # Success
        logger.section("Bootstrap Complete")
        logger.ok("llama.cpp is running")
        print()
        logger.info("Endpoints:")
        print("  API: http://localhost:8081")
        print("  Health: http://localhost:8081/health")
        print()
        logger.info("View logs: podman logs -f llama-coder")

        return 0

    except Exception as e:
        logger.error(f"Bootstrap failed: {e}")
        if env.debug:

            traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
