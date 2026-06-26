"""Service implementation for restarting services."""

from pathlib import Path

from ..ports.outbound.logger import Logger
from ..ports.outbound import ComposeLifecycle
from ..dtos.requests.restart_services_request import RestartServicesRequest
from ..dtos.responses.restart_services_response import RestartServicesResponse
from ..utils import print_section


class RestartServicesService:
    """Restart services using compose tool."""

    def __init__(self, logger: Logger, compose_lifecycle: ComposeLifecycle | None = None) -> None:
        self.logger = logger
        self.compose_lifecycle = compose_lifecycle

    def execute(self, request: RestartServicesRequest) -> RestartServicesResponse:
        if not self.compose_lifecycle:
            self.logger.error("Compose lifecycle operator is not available. Cannot restart services.")
            return RestartServicesResponse(False)

        print_section("Restarting Services")
        result = self.compose_lifecycle.restart(
            Path(request.compose_file),
            *request.services,
        )
        if result.success:
            self.logger.ok("Services restarted")
            return RestartServicesResponse(True)
        else:
            self.logger.error("Failed to restart services")
            if result.stderr:
                self.logger.debug(result.stderr)
            return RestartServicesResponse(False)
