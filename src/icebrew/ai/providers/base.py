"""Generic AI source provider abstraction."""

from __future__ import annotations

from abc import ABC, abstractmethod

from icebrew.ai.catalog.schema import ModelMetadata


class ProviderError(RuntimeError):
    """Base exception for provider-related failures."""


class SourceProvider(ABC):
    """Base interface for AI model source providers."""

    @property
    @abstractmethod
    def identifier(self) -> str:
        """Return the provider identifier."""

    @abstractmethod
    def resolve(self, model: ModelMetadata, filename: str) -> str:
        """Resolve a declared model file into a downloadable URL."""

    @abstractmethod
    def list_files(self, model: ModelMetadata) -> list[str]:
        """List files available in the source repository."""