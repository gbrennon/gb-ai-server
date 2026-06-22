"""CLI entry point for the llama.cpp bootstrap."""

import argparse
import sys
from pathlib import Path

from gb_ai_server.infrastructure.di.container import Container
from gb_ai_server.presentation.composer import BootstrapCompositionRoot


def build_parser() -> argparse.ArgumentParser:
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
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    root = BootstrapCompositionRoot(Container())
    return root.run(args)


if __name__ == "__main__":
    sys.exit(main())
