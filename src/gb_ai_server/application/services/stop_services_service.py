"""Service implementation for stopping services."""

from pathlib import Path

from ..ports.outbound.logger import Logger
from ..ports.outbound import ComposeLifecycle
from ..dtos.requests.stop_services_request import StopServicesRequest
from ..dtos.responses.stop_services_response import StopServicesResponse
from ..utils import print_section


class StopServicesService:
    """Stop services using compose tool."""

    def __init__(self, logger: Logger, compose_lifecycle: ComposeLifecycle | None = None) -> None:
        self.logger = logger
        self.compose_lifecycle = compose_lifecycle

    def execute(self, request: StopServicesRequest) -> StopServicesResponse:
        if not self.compose_lifecycle:
            self.logger.error("Compose lifecycle operator is not available. Cannot stop services.")
            return StopServicesResponse(False)

        print_section("Stopping Services")
        result = self.compose_lifecycle.down(Path(request.compose_file))
        if result.success:
            self.logger.ok("Services stopped")
            return StopServicesResponse(True)
        else:
            self.logger.warn("Failed to stop services gracefully")
            return StopServicesResponse(False)
