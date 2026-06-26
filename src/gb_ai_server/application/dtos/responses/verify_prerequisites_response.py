"""Response DTO for prerequisite verification."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ...ports.outbound import (
        ContainerRuntime,
        ContainerInspector,
        ContainerOperator,
        ComposeTool,
        ComposeLifecycle,
        ComposeQuery,
    )


class VerifyPrerequisitesResponse:
    """Result of prerequisite verification."""

    def __init__(
        self,
        success: bool,
        container_runtime: ContainerRuntime | None = None,
        inspector: ContainerInspector | None = None,
        operator: ContainerOperator | None = None,
        compose_tool: ComposeTool | None = None,
        compose_lifecycle: ComposeLifecycle | None = None,
        compose_query: ComposeQuery | None = None,
    ) -> None:
        self.success = success
        self.container_runtime = container_runtime
        self.inspector = inspector
        self.operator = operator
        self.compose_tool = compose_tool
        self.compose_lifecycle = compose_lifecycle
        self.compose_query = compose_query
