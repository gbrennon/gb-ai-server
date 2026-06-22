"""Service implementation for verifying prerequisites."""

from pathlib import Path
import shutil
from typing import TYPE_CHECKING

from ..ports.outbound.logger import Logger
from ..ports.outbound.runtime_detector import RuntimeDetector
from ..ports.outbound.compose_tool_detector import ComposeToolDetector
from ..dtos.requests.verify_prerequisites_request import VerifyPrerequisitesRequest
from ..dtos.responses.verify_prerequisites_response import VerifyPrerequisitesResponse

if TYPE_CHECKING:
    from ..ports.outbound import ContainerRuntime, ComposeTool


class PrerequisiteVerifierService:
    """Verify system prerequisites for bootstrap."""

    def __init__(
        self,
        logger: Logger,
        runtime_detector: RuntimeDetector,
        compose_detector: ComposeToolDetector,
    ) -> None:
        self.logger = logger
        self._runtime_detector = runtime_detector
        self._compose_detector = compose_detector
        self._container_runtime: ContainerRuntime | None = None
        self._compose_tool: ComposeTool | None = None

    @property
    def container_runtime(self) -> ContainerRuntime | None:
        return self._container_runtime

    @property
    def compose_tool(self) -> ComposeTool | None:
        return self._compose_tool

    def execute(self, request: VerifyPrerequisitesRequest) -> VerifyPrerequisitesResponse:
        self.logger.section("Verifying Prerequisites")
        all_passed = True

        if not self._verify_container_runtime():
            all_passed = False
        if not self._verify_compose_tool():
            all_passed = False
        if not self._verify_command("curl"):
            all_passed = False
        if not self._verify_compose(Path(request.compose_file)):
            all_passed = False

        return VerifyPrerequisitesResponse(all_passed)

    def _verify_container_runtime(self) -> bool:
        try:
            self._container_runtime = self._runtime_detector.detect()
            self.logger.debug(f"Detected: {self._container_runtime.pretty_name}")
            self.logger.ok("Container Runtime verified")
            return True
        except RuntimeError as e:
            self.logger.error(str(e))
            return False

    def _verify_compose_tool(self) -> bool:
        try:
            self._compose_tool = self._compose_detector.detect()
            self.logger.debug(f"Using: {self._compose_tool.pretty_name}")
            self.logger.ok("Compose Tool verified")
            return True
        except RuntimeError as e:
            self.logger.error(str(e))
            return False

    def _verify_command(self, command: str) -> bool:
        if shutil.which(command):
            self.logger.ok(f"{command} command verified")
            return True
        self.logger.error(f"Command not found: {command}")
        return False

    def _verify_compose(self, compose_file: Path) -> bool:
        if not self._compose_tool:
            self.logger.warn("Compose tool not detected")
            return False
        if not compose_file.exists():
            self.logger.error(f"Compose file not found: {compose_file}")
            return False
        result = self._compose_tool.validate(compose_file)
        if not result.success:
            self.logger.error("Compose validation failed")
            if result.stderr:
                self.logger.debug(result.stderr)
            return False
        self.logger.ok("Compose Configuration verified")
        return True
