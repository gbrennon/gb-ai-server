"""Tests for presentation layer CLI entry point."""

from pathlib import Path
from unittest.mock import patch

from gb_ai_server.presentation.cli import build_parser, main


class TestBuildParser:
    def test_returns_parser_with_prog(self) -> None:
        parser = build_parser()
        assert parser.prog == "bootstrap"

    def test_defaults_are_correct(self) -> None:
        parser = build_parser()
        args = parser.parse_args([])
        assert args.dry_run is False
        assert args.skip_download is False
        assert args.skip_health is False
        assert args.models_dir == Path("/tmp/llama_models")
        assert args.hf_token is None
        assert args.debug is False

    def test_parses_all_flags(self) -> None:
        parser = build_parser()
        args = parser.parse_args(
            [
                "--dry-run",
                "--skip-download",
                "--skip-health",
                "--models-dir",
                "/custom/path",
                "--hf-token",
                "hf_abc123",
                "--debug",
            ]
        )
        assert args.dry_run is True
        assert args.skip_download is True
        assert args.skip_health is True
        assert args.models_dir == Path("/custom/path")
        assert args.hf_token == "hf_abc123"
        assert args.debug is True


class TestMain:
    def test_delegates_to_composition_root(self) -> None:
        with patch(
            "gb_ai_server.presentation.cli.BootstrapCompositionRoot"
        ) as MockRoot:
            instance = MockRoot.return_value
            instance.run.return_value = 0

            result = main(["--skip-download", "--skip-health"])

            assert result == 0
            MockRoot.assert_called_once()
            instance.run.assert_called_once()

    def test_returns_non_zero_when_root_fails(self) -> None:
        with patch(
            "gb_ai_server.presentation.cli.BootstrapCompositionRoot"
        ) as MockRoot:
            instance = MockRoot.return_value
            instance.run.return_value = 1

            result = main(["--skip-download", "--skip-health"])

            assert result == 1
