"""Tests for ModelDownloaderService (mocked outbound ports)."""

from gb_ai_server.application.services import ModelDownloaderService
from gb_ai_server.application.dtos.requests import DownloadModelsRequest
from tests.gb_ai_server.conftest import make_logger_mock, make_model_downloader_mock


class TestModelDownloaderService:
    def test_downloads_all_entries(self) -> None:
        logger = make_logger_mock()
        downloader = make_model_downloader_mock(success=True)
        service = ModelDownloaderService(logger, downloader)

        request = DownloadModelsRequest(
            entries=[("model-a", "a.gguf", "https://example.com/a.gguf")],
            destination_dir="/tmp/models",
        )
        response = service.execute(request)

        assert response.results == {"model-a": True}
        downloader.download.assert_called_once()

    def test_downloads_multiple_models(self) -> None:
        logger = make_logger_mock()
        downloader = make_model_downloader_mock(success=True)
        service = ModelDownloaderService(logger, downloader)

        entries = [
            ("model-a", "a.gguf", "https://example.com/a.gguf"),
            ("model-b", "b.gguf", "https://example.com/b.gguf"),
        ]
        request = DownloadModelsRequest(entries=entries, destination_dir="/tmp/models")
        response = service.execute(request)

        assert response.results == {"model-a": True, "model-b": True}
        assert downloader.download.call_count == 2

    def test_reports_failures(self) -> None:
        logger = make_logger_mock()

        def failing_download(*args: object, **kwargs: object) -> bool:
            return False

        downloader = make_model_downloader_mock(success=False)
        service = ModelDownloaderService(logger, downloader)

        request = DownloadModelsRequest(
            entries=[("model-a", "a.gguf", "https://example.com/a.gguf")],
            destination_dir="/tmp/models",
        )
        response = service.execute(request)

        assert response.results == {"model-a": False}

    def test_creates_destination_dir(self, tmp_path: object) -> None:
        logger = make_logger_mock()
        downloader = make_model_downloader_mock(success=True)
        service = ModelDownloaderService(logger, downloader)

        dest = str(tmp_path / "models")
        request = DownloadModelsRequest(
            entries=[("m", "m.gguf", "https://example.com/m.gguf")],
            destination_dir=dest,
        )
        service.execute(request)

        downloader.download.assert_called_with(
            "m",
            "m.gguf",
            "https://example.com/m.gguf",
            tmp_path / "models",
            token=None,
        )
