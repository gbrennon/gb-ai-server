"""Outbound ports - interfaces implemented by infrastructure adapters."""

from .model_downloader import ModelDownloader
from .container_runtime import ContainerRuntime
from .compose_tool import ComposeTool
from .logger import Logger
from .runtime_detector import RuntimeDetector
from .compose_tool_detector import ComposeToolDetector
from .http_client import HttpClient

__all__: list[str] = [
    "ModelDownloader",
    "ContainerRuntime",
    "ComposeTool",
    "Logger",
    "RuntimeDetector",
    "ComposeToolDetector",
    "HttpClient",
]
