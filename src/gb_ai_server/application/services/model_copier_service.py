"""Service implementation for copying models to containers."""

from pathlib import Path

from ..ports.outbound.logger import Logger
from ..ports.outbound import ContainerInspector, ContainerOperator
from ..dtos.requests.copy_models_request import CopyModelsRequest
from ..dtos.responses.copy_models_response import CopyModelsResponse
from ..utils import print_section


class ModelCopierService:
    """Copy model files into running containers."""

    def __init__(
        self,
        logger: Logger,
        inspector: ContainerInspector | None = None,
        operator: ContainerOperator | None = None,
    ) -> None:
        self.logger = logger
        self._inspector = inspector
        self._operator = operator

    def execute(self, request: CopyModelsRequest) -> CopyModelsResponse:
        if not self._inspector or not self._operator:
            self.logger.error("Container runtime inspector or operator is not available. Cannot copy models.")
            return CopyModelsResponse(
                {display_name: False for display_name, _, _ in request.entries}
            )

        if not self._inspector.is_running(request.container_name):
            self.logger.warn(
                f"Container {request.container_name} not running, skipping copy"
            )
            return CopyModelsResponse(
                {display_name: False for display_name, _, _ in request.entries}
            )

        print_section("Copying Models to Container")
        results: dict[str, bool] = {}
        source_dir = Path(request.source_dir)

        for display_name, filename, _ in request.entries:
            source = source_dir / filename
            if not source.exists():
                self.logger.warn(
                    f"{display_name} not found at {source}, skipping"
                )
                results[display_name] = False
                continue

            self.logger.info(
                f"Copying {display_name} to {request.container_name}..."
            )
            result = self._operator.copy_to(
                source,
                request.container_name,
                f"{request.dest_dir}/{filename}",
            )
            if result.success:
                self.logger.ok(f"Copied {display_name}")
                results[display_name] = True
            else:
                self.logger.warn(f"Failed to copy {display_name}")
                if result.stderr:
                    self.logger.debug(result.stderr)
                results[display_name] = False

        return CopyModelsResponse(results)
