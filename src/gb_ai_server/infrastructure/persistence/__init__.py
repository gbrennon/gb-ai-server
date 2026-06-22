"""Persistence adapters for model file storage."""

from .model_downloader import HuggingFaceModelDownloader

__all__: list[str] = [
    "HuggingFaceModelDownloader",
]
