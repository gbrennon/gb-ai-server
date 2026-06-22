"""Service implementation for copying models to containers."""

from pathlib import Path

from ..ports.outbound.logger import Logger
from ..ports.outbound import ContainerRuntime
from ..dtos.requests.copy_models_request import CopyModelsRequest
from ..dtos.responses.copy_models_response import CopyModelsResponse


class ModelCopierService:
    """Copy model files into running containers."""

    def __init__(self, logger: Logger, container_runtime: ContainerRuntime) -> None:
        self.logger = logger
        self.runtime = container_runtime

    def execute(self, request: CopyModelsRequest) -> CopyModelsResponse:
        if not self.runtime.is_running(request.container_name):
            self.logger.warn(
                f"Container {request.container_name} not running, skipping copy"
            )
            return CopyModelsResponse(
                {display_name: False for display_name, _, _ in request.entries}
            )

        self.logger.section("Copying Models to Container")
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
            result = self.runtime.copy_to(
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
