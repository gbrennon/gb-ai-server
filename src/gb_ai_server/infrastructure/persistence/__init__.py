"""Persistence adapters for model file storage and tool registration."""

from .model_downloader import HuggingFaceModelDownloader
from .cline_model_registrar import ClineModelRegistrar

__all__: list[str] = [
    "HuggingFaceModelDownloader",
    "ClineModelRegistrar",
]
