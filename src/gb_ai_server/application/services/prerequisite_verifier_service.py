"""Service implementation for verifying prerequisites."""

from pathlib import Path
import shutil

from ..ports.outbound.logger import Logger
from ..ports.outbound.runtime_detector import RuntimeDetector
from ..ports.outbound.compose_tool_detector import ComposeToolDetector
from ..dtos.requests.verify_prerequisites_request import VerifyPrerequisitesRequest
from ..dtos.responses.verify_prerequisites_response import VerifyPrerequisitesResponse
from ..utils import print_section


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

    def execute(self, request: VerifyPrerequisitesRequest) -> VerifyPrerequisitesResponse:
        print_section("Verifying Prerequisites")

        # 1. Detect Container Runtime
        runtime = None
        inspector = None
        operator = None
        try:
            detection = self._runtime_detector.detect()
            runtime = detection.runtime
            inspector = detection.inspector
            operator = detection.operator
            self.logger.debug(f"Detected: {runtime.pretty_name}")
            self.logger.ok("Container Runtime verified")
            runtime_ok = True
        except RuntimeError as e:
            self.logger.error(str(e))
            runtime_ok = False

        # 2. Detect Compose Tool
        compose_tool = None
        compose_lifecycle = None
        compose_query = None
        try:
            detection = self._compose_detector.detect()
            compose_tool = detection.tool
            compose_lifecycle = detection.lifecycle
            compose_query = detection.query
            self.logger.debug(f"Using: {compose_tool.pretty_name}")
            self.logger.ok("Compose Tool verified")
            compose_ok = True
        except RuntimeError as e:
            self.logger.error(str(e))
            compose_ok = False

        # 3. Verify curl command
        curl_ok = self._verify_command("curl")

        # 4. Validate compose file
        compose_file_ok = False
        if compose_query:
            compose_file = Path(request.compose_file)
            if not compose_file.exists():
                self.logger.error(f"Compose file not found: {compose_file}")
            else:
                result = compose_query.validate(compose_file)
                if not result.success:
                    self.logger.error("Compose validation failed")
                    if result.stderr:
                        self.logger.debug(result.stderr)
                else:
                    self.logger.ok("Compose Configuration verified")
                    compose_file_ok = True
        else:
            self.logger.warn("Compose tool validation skipped due to detection failure")

        all_passed = runtime_ok and compose_ok and curl_ok and compose_file_ok

        return VerifyPrerequisitesResponse(
            success=all_passed,
            container_runtime=runtime,
            inspector=inspector,
            operator=operator,
            compose_tool=compose_tool,
            compose_lifecycle=compose_lifecycle,
            compose_query=compose_query,
        )

    def _verify_command(self, command: str) -> bool:
        if shutil.which(command):
            self.logger.ok(f"{command} command verified")
            return True
        self.logger.error(f"Command not found: '{command}'. Please install it and ensure it is in your PATH.")
        return False
