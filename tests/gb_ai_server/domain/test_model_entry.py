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

    def test_parses_five_part_format(self) -> None:
        # Both n_gpu_layers and ctx_size fields (4th and 5th parts) are accepted
        # for backward compatibility but NOT stored — calculated at runtime.
        entry = ModelEntry.from_string("qwen:7b|qwen.gguf|https://example.com/q|999|8192")
        assert entry.display_name == "qwen:7b"
        assert entry.filename == "qwen.gguf"
        assert entry.url == "https://example.com/q"
        assert not hasattr(entry, "n_gpu_layers")
    def test_raises_on_too_many_parts(self) -> None:
        with pytest.raises(ValueError, match="Invalid model entry format"):
            ModelEntry.from_string("a|b|c|d|e|f")

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
        assert not hasattr(entry, "n_gpu_layers")

    def test_from_five_tuple_ignores_extra(self) -> None:
        # n_gpu_layers and ctx_size (4th and 5th elements) are accepted
        # for backward compatibility but NOT stored — calculated at runtime.
        entry = ModelEntry.from_tuple(("m", "f.gguf", "https://example.com/f", 50, 4096))
        assert entry.display_name == "m"
        assert not hasattr(entry, "n_gpu_layers")

class TestModelEntryNoCtxSizeField:
    """ModelEntry must not hold a ctx_size field — context window comes from HF lib."""

    def test_has_no_ctx_size_attribute(self) -> None:
        entry = ModelEntry("a", "b.gguf", "https://example.com/b.gguf")
        assert not hasattr(entry, "ctx_size"), (
            "ModelEntry must not store ctx_size — use fetch_safe_ctx_size() instead"
        )

    def test_env_var_has_no_effect_on_model_entry(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("CTX_SIZE", "99999")
        entry = ModelEntry("a", "b.gguf", "https://example.com/b.gguf")
        assert not hasattr(entry, "ctx_size")

    def test_five_part_string_does_not_expose_ctx(self) -> None:
        entry = ModelEntry.from_string("qwen:7b|qwen.gguf|https://example.com/q|999|4096")
        assert not hasattr(entry, "ctx_size")

    def test_five_tuple_does_not_expose_ctx(self) -> None:
        entry = ModelEntry.from_tuple(("m", "f.gguf", "https://example.com/f", 50, 4096))
        assert not hasattr(entry, "ctx_size")


class TestModelEntryStr:
    def test_serialization(self) -> None:
        entry = ModelEntry("a", "b.gguf", "https://example.com/b.gguf")
        assert str(entry) == "a|b.gguf|https://example.com/b.gguf"
