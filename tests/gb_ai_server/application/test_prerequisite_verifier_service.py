"""Tests for PrerequisiteVerifierService (mocked outbound ports)."""

from pathlib import Path
from unittest.mock import patch


from gb_ai_server.application.services import PrerequisiteVerifierService
from gb_ai_server.application.dtos.requests import VerifyPrerequisitesRequest
from tests.gb_ai_server.conftest import (
    make_logger_mock,
    make_compose_tool_mock,
    make_lifecycle_mock,
    make_query_mock,
    make_runtime_detector_mock,
    make_compose_detector_mock,
    make_runtime_mock,
    make_inspector_mock,
    make_operator_mock,
)


class TestPrerequisiteVerifierService:
    def test_all_prerequisites_pass(self, tmp_path: Path) -> None:
        logger = make_logger_mock()
        tool = make_compose_tool_mock()
        lifecycle = make_lifecycle_mock()
        query = make_query_mock(validate_ok=True)
        runtime = make_runtime_mock()
        inspector = make_inspector_mock()
        operator = make_operator_mock()
        service = PrerequisiteVerifierService(
            logger=logger,
            runtime_detector=make_runtime_detector_mock(runtime, inspector, operator),
            compose_detector=make_compose_detector_mock(tool, lifecycle, query),
        )

        compose_file = tmp_path / "docker-compose.yml"
        compose_file.write_text("services:\n  test:\n    image: alpine\n")

        with patch("shutil.which", return_value="/usr/bin/curl"):
            response = service.execute(
                VerifyPrerequisitesRequest(str(compose_file))
            )

        assert response.success is True
        assert response.container_runtime is not None
        assert response.inspector is not None
        assert response.operator is not None
        assert response.compose_tool is not None
        assert response.compose_lifecycle is not None
        assert response.compose_query is not None

    def test_fails_when_runtime_not_detected(self) -> None:
        logger = make_logger_mock()
        detector = make_runtime_detector_mock()
        detector.detect.side_effect = RuntimeError("No container runtime found")

        service = PrerequisiteVerifierService(
            logger=logger,
            runtime_detector=detector,
            compose_detector=make_compose_detector_mock(),
        )

        with patch("shutil.which", return_value="/usr/bin/curl"):
            response = service.execute(
                VerifyPrerequisitesRequest("compose.yml")
            )

        assert response.success is False
        logger.error.assert_any_call("No container runtime found")

    def test_fails_when_compose_not_detected(self) -> None:
        logger = make_logger_mock()
        detector = make_compose_detector_mock()
        detector.detect.side_effect = RuntimeError("No compose tool found")

        service = PrerequisiteVerifierService(
            logger=logger,
            runtime_detector=make_runtime_detector_mock(),
            compose_detector=detector,
        )

        with patch("shutil.which", return_value="/usr/bin/curl"):
            response = service.execute(
                VerifyPrerequisitesRequest("compose.yml")
            )

        assert response.success is False

    def test_fails_when_curl_missing(self) -> None:
        logger = make_logger_mock()
        service = PrerequisiteVerifierService(
            logger=logger,
            runtime_detector=make_runtime_detector_mock(),
            compose_detector=make_compose_detector_mock(),
        )

        with patch("shutil.which", return_value=None):
            response = service.execute(
                VerifyPrerequisitesRequest("compose.yml")
            )

        assert response.success is False

    def test_fails_when_compose_file_missing(self) -> None:
        logger = make_logger_mock()
        query = make_query_mock(validate_ok=True)
        service = PrerequisiteVerifierService(
            logger=logger,
            runtime_detector=make_runtime_detector_mock(),
            compose_detector=make_compose_detector_mock(query_mock=query),
        )

        with patch("shutil.which", return_value="/usr/bin/curl"):
            response = service.execute(
                VerifyPrerequisitesRequest("/nonexistent/compose.yml")
            )

        assert response.success is False

    def test_fails_when_compose_validation_fails(self, tmp_path: Path) -> None:
        logger = make_logger_mock()
        query = make_query_mock(validate_ok=False)
        service = PrerequisiteVerifierService(
            logger=logger,
            runtime_detector=make_runtime_detector_mock(),
            compose_detector=make_compose_detector_mock(query_mock=query),
        )

        compose_file = tmp_path / "docker-compose.yml"
        compose_file.write_text("invalid: yaml: :")

        with patch("shutil.which", return_value="/usr/bin/curl"):
            response = service.execute(
                VerifyPrerequisitesRequest(str(compose_file))
            )

        assert response.success is False
