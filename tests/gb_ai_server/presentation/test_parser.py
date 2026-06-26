"""Tests for presentation layer models parser."""

from pathlib import Path

import pytest

from gb_ai_server.presentation.parser import (
    _is_array_end,
    _parse_entry,
    _strip_array_declaration,
    _strip_array_end,
    load_models,
)


class TestStripArrayDeclaration:
    def test_strips_when_matches(self) -> None:
        assert _strip_array_declaration('MODELS=("entry")') == '"entry")'

    def test_returns_unchanged_when_no_match(self) -> None:
        assert _strip_array_declaration("echo hello") == "echo hello"

    def test_handles_empty_string(self) -> None:
        assert _strip_array_declaration("") == ""


class TestIsArrayEnd:
    def test_true_when_ends_with_paren(self) -> None:
        assert _is_array_end(")") is True

    def test_true_with_content(self) -> None:
        assert _is_array_end('"entry")') is True

    def test_false_when_does_not_end(self) -> None:
        assert _is_array_end('"entry"') is False

    def test_false_on_empty(self) -> None:
        assert _is_array_end("") is False


class TestStripArrayEnd:
    def test_strips_when_ends_with_paren(self) -> None:
        assert _strip_array_end('"entry")') == '"entry"'

    def test_returns_unchanged_when_no_paren(self) -> None:
        assert _strip_array_end('"entry"') == '"entry"'

    def test_handles_empty(self) -> None:
        assert _strip_array_end("") == ""


class TestParseEntry:
    def test_parses_valid_entry(self) -> None:
        entry = _parse_entry('"qwen:7b|qwen.gguf|https://example.com/q"')
        assert entry is not None
        assert entry.display_name == "qwen:7b"
        assert entry.filename == "qwen.gguf"

    def test_returns_none_for_empty(self) -> None:
        assert _parse_entry("") is None

    def test_returns_none_for_comment(self) -> None:
        assert _parse_entry("# this is a comment") is None

    def test_returns_none_for_whitespace(self) -> None:
        assert _parse_entry("   ") is None

    def test_parses_without_quotes(self) -> None:
        entry = _parse_entry("m|f.gguf|https://example.com/f")
        assert entry is not None
        assert entry.display_name == "m"


class TestLoadModels:
    def test_parses_single_entry(self, tmp_path: Path) -> None:
        conf = tmp_path / "models.conf.sh"
        conf.write_text('MODELS=(\n  "qwen:7b|qwen.gguf|https://example.com/q"\n)\n')
        models = load_models(conf)
        assert len(models) == 1
        assert models[0].display_name == "qwen:7b"

    def test_parses_multiple_entries(self, tmp_path: Path) -> None:
        conf = tmp_path / "models.conf.sh"
        conf.write_text(
            'MODELS=(\n'
            '  "qwen:7b|qwen.gguf|https://example.com/q"\n'
            '  "mistral|m.gguf|https://example.com/m"\n'
            ')\n'
        )
        models = load_models(conf)
        assert len(models) == 2
        assert models[0].display_name == "qwen:7b"
        assert models[1].display_name == "mistral"

    def test_skips_comments(self, tmp_path: Path) -> None:
        conf = tmp_path / "models.conf.sh"
        conf.write_text(
            'MODELS=(\n'
            '  # this is a comment\n'
            '  "qwen:7b|qwen.gguf|https://example.com/q"\n'
            ')\n'
        )
        models = load_models(conf)
        assert len(models) == 1

    def test_returns_empty_when_no_entries(self, tmp_path: Path) -> None:
        conf = tmp_path / "models.conf.sh"
        conf.write_text("MODELS=(\n)\n")
        models = load_models(conf)
        assert models == []

    def test_raises_on_missing_file(self, tmp_path: Path) -> None:
        missing = tmp_path / "nonexistent.sh"
        with pytest.raises(ValueError, match="Models config not found"):
            load_models(missing)

    def test_ignores_content_before_array(self, tmp_path: Path) -> None:
        conf = tmp_path / "models.conf.sh"
        conf.write_text(
            '#!/bin/bash\n'
            'export FOO=bar\n'
            'MODELS=(\n'
            '  "m|f.gguf|https://example.com/f"\n'
            ')\n'
        )
        models = load_models(conf)
        assert len(models) == 1
