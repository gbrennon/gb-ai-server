"""Integration tests for model downloader (fixture files, no real downloads)."""

from pathlib import Path
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

import pytest

from gb_ai_server.infrastructure.persistence.model_downloader import (
    HuggingFaceModelDownloader,
)
from tests.conftest import make_logger_mock


class _TestFileHandler(BaseHTTPRequestHandler):
    """Serves a static file for download tests."""

    def do_GET(self) -> None:
        self.send_response(200)
        self.send_header("Content-Type", "application/octet-stream")
        self.send_header("Content-Length", "13")
        self.end_headers()
        self.wfile.write(b"hello, fixture")

    def log_message(self, fmt: str, *args: object) -> None:
        pass


@pytest.fixture(scope="module")
def download_server() -> int:
    """Start a local HTTP server that serves a small file."""
    server = HTTPServer(("127.0.0.1", 0), _TestFileHandler)
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield port
    server.shutdown()


class TestHuggingFaceModelDownloader:
    def test_exists_returns_false_for_missing_file(self, tmp_path: Path) -> None:
        logger = make_logger_mock()
        downloader = HuggingFaceModelDownloader(logger)
        assert downloader.exists("nonexistent.gguf", tmp_path) is False

    def test_exists_returns_true_for_existing_file(self, tmp_path: Path) -> None:
        logger = make_logger_mock()
        downloader = HuggingFaceModelDownloader(logger)
        model_file = tmp_path / "model.gguf"
        model_file.write_text("fixture-data")
        assert downloader.exists("model.gguf", tmp_path) is True

    def test_exists_returns_false_for_empty_file(self, tmp_path: Path) -> None:
        logger = make_logger_mock()
        downloader = HuggingFaceModelDownloader(logger)
        model_file = tmp_path / "empty.gguf"
        model_file.write_text("")
        assert downloader.exists("empty.gguf", tmp_path) is False

    def test_parse_hf_url_valid(self) -> None:
        logger = make_logger_mock()
        downloader = HuggingFaceModelDownloader(logger)
        repo_id, file_path = downloader._parse_hf_url(
            "https://huggingface.co/Qwen/Qwen2.5-Coder-7B/resolve/main/qwen-7b.gguf"
        )
        assert repo_id == "Qwen/Qwen2.5-Coder-7B"
        assert file_path == "qwen-7b.gguf"

    def test_parse_hf_url_with_tag(self) -> None:
        logger = make_logger_mock()
        downloader = HuggingFaceModelDownloader(logger)
        repo_id, file_path = downloader._parse_hf_url(
            "https://huggingface.co/mistralai/Mistral-7B-v0.1/resolve/v1.0/model.gguf"
        )
        assert repo_id == "mistralai/Mistral-7B-v0.1"
        assert file_path == "model.gguf"

    def test_parse_hf_url_invalid(self) -> None:
        logger = make_logger_mock()
        downloader = HuggingFaceModelDownloader(logger)
        repo_id, file_path = downloader._parse_hf_url("https://example.com/model.gguf")
        assert repo_id is None
        assert file_path is None

    def test_parse_hf_url_empty(self) -> None:
        logger = make_logger_mock()
        downloader = HuggingFaceModelDownloader(logger)
        repo_id, file_path = downloader._parse_hf_url("")
        assert repo_id is None
        assert file_path is None

    def test_skip_existing_download(self, tmp_path: Path) -> None:
        logger = make_logger_mock()
        downloader = HuggingFaceModelDownloader(logger)
        model_file = tmp_path / "existing.gguf"
        model_file.write_text("data")
        result = downloader.download(
            "existing",
            "existing.gguf",
            "https://example.com/existing.gguf",
            tmp_path,
        )
        assert result is True

    def test_download_returns_false_for_invalid_url(self, tmp_path: Path) -> None:
        logger = make_logger_mock()
        downloader = HuggingFaceModelDownloader(logger)
        result = downloader.download(
            "test", "test.gguf", "https://example.com/model.gguf", tmp_path
        )
        assert result is False

    def test_download_with_curl_creates_file(self, tmp_path: Path, download_server: int) -> None:
        logger = make_logger_mock()
        downloader = HuggingFaceModelDownloader(logger)
        dest = tmp_path / "downloaded.txt"
        result = downloader._download_with_curl(
            "test-file",
            f"http://127.0.0.1:{download_server}/download",
            dest,
        )
        assert result is True
        assert dest.exists()
        assert dest.stat().st_size > 0

    def test_download_with_curl_fails_on_bad_url(self, tmp_path: Path) -> None:
        logger = make_logger_mock()
        downloader = HuggingFaceModelDownloader(logger)
        dest = tmp_path / "nonexistent.txt"
        result = downloader._download_with_curl(
            "bad-url",
            "http://127.0.0.1:1/nonexistent",
            dest,
        )
        assert result is False

    def test_download_creates_destination_dir(self, tmp_path: Path) -> None:
        logger = make_logger_mock()
        downloader = HuggingFaceModelDownloader(logger)
        nested = tmp_path / "deep" / "dir"
        assert not nested.exists()
        downloader.download(
            "test",
            "test.gguf",
            "https://huggingface.co/Qwen/Qwen2.5-Coder-7B/resolve/main/qwen-7b.gguf",
            nested,
        )
        assert nested.exists()

    def test_download_returns_false_on_empty_url(self, tmp_path: Path) -> None:
        logger = make_logger_mock()
        downloader = HuggingFaceModelDownloader(logger)
        result = downloader.download("bad", "bad.gguf", "", tmp_path)
        assert result is False
