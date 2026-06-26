"""Compose tool detection result."""

from dataclasses import dataclass

from .compose_tool import ComposeTool
from .compose_lifecycle import ComposeLifecycle
from .compose_query import ComposeQuery


@dataclass
class ComposeDetection:
    """Result of compose tool detection."""

    tool: ComposeTool
    lifecycle: ComposeLifecycle
    query: ComposeQuery
