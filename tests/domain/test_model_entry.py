"""Tests for ModelEntry domain object."""

import pytest
from gb_ai_server.domain import ModelEntry


class TestModelEntryFromString:
    def test_valid_entry(self) -> None:
        entry = ModelEntry.from_string("qwen2.5-coder:7b|qwen-7b.gguf|https://huggingface.co/Qwen/Qwen2.5-Coder-7B/resolve/main/qwen-7b.gguf")
        assert entry.display_name == "qwen2.5-coder:7b"
        assert entry.filename == "qwen-7b.gguf"
        assert "huggingface.co" in entry.url

    def test_triple_pipe_format(self) -> None:
        entry = ModelEntry.from_string("  name  |  file.gguf  |  https://example.com/model  ")
        assert entry.display_name == "name"
        assert entry.filename == "file.gguf"
        assert entry.url == "https://example.com/model"

    def test_raises_on_not_enough_parts(self) -> None:
        with pytest.raises(ValueError, match="Invalid model entry format"):
            ModelEntry.from_string("only|two")

    def test_raises_on_too_many_parts(self) -> None:
        with pytest.raises(ValueError, match="Invalid model entry format"):
            ModelEntry.from_string("a|b|c|d")

    def test_raises_on_empty_parts(self) -> None:
        with pytest.raises(ValueError, match="empty fields"):
            ModelEntry.from_string("||url")

    def test_raises_on_empty_display_name(self) -> None:
        with pytest.raises(ValueError, match="empty fields"):
            ModelEntry.from_string("|file.gguf|url")

    def test_raises_on_empty_string(self) -> None:
        with pytest.raises(ValueError, match="Invalid model entry format"):
            ModelEntry.from_string("")


class TestModelEntryFromTuple:
    def test_from_tuple(self) -> None:
        entry = ModelEntry.from_tuple(("my-model", "model.gguf", "https://example.com/m.gguf"))
        assert entry.display_name == "my-model"
        assert entry.filename == "model.gguf"
        assert entry.url == "https://example.com/m.gguf"


class TestModelEntryStr:
    def test_serialization(self) -> None:
        entry = ModelEntry("a", "b.gguf", "https://example.com/b.gguf")
        assert str(entry) == "a|b.gguf|https://example.com/b.gguf"
