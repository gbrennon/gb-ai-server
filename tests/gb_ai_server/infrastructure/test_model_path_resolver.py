"""Tests for ModelPathResolver using real filesystem fixtures.

Behavior confirmed via REPL (2026-06-27):
  ├─ Empty dirs → ValueError
  ├─ primary() → first dir in list
  ├─ all_dirs() → copy of full list
  ├─ resolve(filename) → searches in order, returns Path or None
  ├─ Empty files (0 bytes) → treated as not found
  └─ First match wins when file exists in multiple dirs
"""

from pathlib import Path

import pytest

from gb_ai_server.infrastructure.paths import ModelPathResolver


# ---------------------------------------------------------------------------
# Fixtures — simulate real-world model storage layout
# ---------------------------------------------------------------------------

@pytest.fixture
def primary_dir(tmp_path: Path) -> Path:
    """Simulate the writable download cache (e.g., ``./models``)."""
    d = tmp_path / "download_cache"
    d.mkdir(parents=True)
    return d


@pytest.fixture
def secondary_dir(tmp_path: Path) -> Path:
    """Simulate a read-only USB drive with pre-loaded models."""
    d = tmp_path / "usb_drive"
    d.mkdir(parents=True)
    return d


@pytest.fixture
def tertiary_dir(tmp_path: Path) -> Path:
    """Simulate a network mount (NAS) with additional models."""
    d = tmp_path / "nas_mount"
    d.mkdir(parents=True)
    return d


@pytest.fixture
def resolver_single(primary_dir: Path) -> ModelPathResolver:
    """Resolver with only the primary writable directory."""
    return ModelPathResolver([primary_dir])


@pytest.fixture
def resolver_with_fallback(
    primary_dir: Path, secondary_dir: Path
) -> ModelPathResolver:
    """Resolver with primary + USB fallback."""
    return ModelPathResolver([primary_dir, secondary_dir])


@pytest.fixture
def resolver_three_tier(
    primary_dir: Path, secondary_dir: Path, tertiary_dir: Path
) -> ModelPathResolver:
    """Resolver with three tiers: cache → USB → NAS."""
    return ModelPathResolver([primary_dir, secondary_dir, tertiary_dir])


@pytest.fixture
def populated_primary(primary_dir: Path) -> Path:
    """Primary dir with a downloaded model file."""
    model = primary_dir / "qwen.gguf"
    model.write_text("gguf-data")
    return primary_dir


@pytest.fixture
def populated_secondary(secondary_dir: Path) -> Path:
    """Secondary dir with a USB-only model file."""
    model = secondary_dir / "gemma.gguf"
    model.write_text("gguf-data")
    return secondary_dir


@pytest.fixture
def populated_tertiary(tertiary_dir: Path) -> Path:
    """Tertiary dir with a NAS-only model file."""
    model = tertiary_dir / "llama.gguf"
    model.write_text("gguf-data")
    return tertiary_dir


# ---------------------------------------------------------------------------
# Constructor
# ---------------------------------------------------------------------------

class TestConstructor:
    def test_requires_at_least_one_dir(self) -> None:
        with pytest.raises(ValueError, match="At least one model directory"):
            ModelPathResolver([])

    def test_accepts_single_dir(self, primary_dir: Path) -> None:
        r = ModelPathResolver([primary_dir])
        assert r.primary() == primary_dir
        assert r.all_dirs() == [primary_dir]

    def test_accepts_multiple_dirs(
        self, primary_dir: Path, secondary_dir: Path
    ) -> None:
        r = ModelPathResolver([primary_dir, secondary_dir])
        assert r.all_dirs() == [primary_dir, secondary_dir]


# ---------------------------------------------------------------------------
# primary() / all_dirs()
# ---------------------------------------------------------------------------

class TestAccessors:
    def test_primary_returns_first_dir(
        self, primary_dir: Path, secondary_dir: Path
    ) -> None:
        r = ModelPathResolver([primary_dir, secondary_dir])
        assert r.primary() == primary_dir

    def test_all_dirs_returns_copy(
        self, primary_dir: Path, secondary_dir: Path
    ) -> None:
        r = ModelPathResolver([primary_dir, secondary_dir])
        dirs = r.all_dirs()
        dirs.append(Path("/injected"))
        # original should be unchanged
        assert r.all_dirs() == [primary_dir, secondary_dir]


# ---------------------------------------------------------------------------
# resolve() — basic scenarios
# ---------------------------------------------------------------------------

class TestResolveBasic:
    def test_returns_none_for_nonexistent_file(
        self, resolver_single: ModelPathResolver
    ) -> None:
        assert resolver_single.resolve("nonexistent.gguf") is None

    def test_finds_file_in_primary(
        self, populated_primary: Path, resolver_single: ModelPathResolver
    ) -> None:
        path = resolver_single.resolve("qwen.gguf")
        assert path == populated_primary / "qwen.gguf"
        assert path.exists()

    def test_skips_empty_file(
        self, primary_dir: Path, resolver_single: ModelPathResolver
    ) -> None:
        empty = primary_dir / "empty.gguf"
        empty.touch()
        assert resolver_single.resolve("empty.gguf") is None


# ---------------------------------------------------------------------------
# resolve() — multi-directory fallback
# ---------------------------------------------------------------------------

class TestResolveFallback:
    def test_finds_file_in_secondary_when_not_in_primary(
        self,
        populated_secondary: Path,
        resolver_with_fallback: ModelPathResolver,
    ) -> None:
        path = resolver_with_fallback.resolve("gemma.gguf")
        assert path == populated_secondary / "gemma.gguf"
        assert path.exists()

    def test_prefers_primary_over_secondary(
        self,
        primary_dir: Path,
        secondary_dir: Path,
        resolver_with_fallback: ModelPathResolver,
    ) -> None:
        """Same filename in both dirs — primary should win."""
        (primary_dir / "shared.gguf").write_text("primary-version")
        (secondary_dir / "shared.gguf").write_text("secondary-version")

        path = resolver_with_fallback.resolve("shared.gguf")
        assert path == primary_dir / "shared.gguf"
        assert path.read_text() == "primary-version"

    def test_three_tier_finds_in_tertiary(
        self,
        populated_tertiary: Path,
        resolver_three_tier: ModelPathResolver,
    ) -> None:
        path = resolver_three_tier.resolve("llama.gguf")
        assert path == populated_tertiary / "llama.gguf"

    def test_three_tier_all_missing(
        self, resolver_three_tier: ModelPathResolver
    ) -> None:
        assert resolver_three_tier.resolve("ghost.gguf") is None


# ---------------------------------------------------------------------------
# resolve() — empty / edge cases
# ---------------------------------------------------------------------------

class TestResolveEdgeCases:
    def test_empty_file_in_primary_does_not_block_secondary(
        self,
        primary_dir: Path,
        secondary_dir: Path,
    ) -> None:
        """0-byte file in primary should be skipped, secondary checked."""
        (primary_dir / "model.gguf").touch()
        (secondary_dir / "model.gguf").write_text("real-data")
        r = ModelPathResolver([primary_dir, secondary_dir])
        path = r.resolve("model.gguf")
        assert path == secondary_dir / "model.gguf"

    def test_empty_file_everywhere_returns_none(
        self,
        primary_dir: Path,
        secondary_dir: Path,
    ) -> None:
        (primary_dir / "empty.gguf").touch()
        (secondary_dir / "empty.gguf").touch()
        r = ModelPathResolver([primary_dir, secondary_dir])
        assert r.resolve("empty.gguf") is None

    def test_filename_with_spaces(
        self, primary_dir: Path, resolver_single: ModelPathResolver
    ) -> None:
        model = primary_dir / "my model.gguf"
        model.write_text("data")
        path = resolver_single.resolve("my model.gguf")
        assert path == model
