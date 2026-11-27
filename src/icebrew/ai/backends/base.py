# src/icebrew/ai/backends/base.py

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any


class ModelBackend(ABC):
    """Abstract contract for Icebrew inference backends."""

    @property
    @abstractmethod
    def identifier(self) -> str:
        """Unique backend identifier."""
        raise NotImplementedError

    @property
    @abstractmethod
    def supported_formats(self) -> tuple[str, ...]:
        """Model formats supported by this backend."""
        raise NotImplementedError

    @property
    @abstractmethod
    def supported_tasks(self) -> tuple[str, ...]:
        """Inference tasks supported by this backend."""
        raise NotImplementedError

    @abstractmethod
    def is_available(self) -> bool:
        """Return whether the backend is usable in the current environment."""
        raise NotImplementedError

    @abstractmethod
    def health_check(self) -> dict[str, Any]:
        """Return a structured backend health report."""
        raise NotImplementedError

    @abstractmethod
    def load(
        self,
        model_path: str | Path,
        **kwargs: Any,
    ) -> Any:
        """Load a model using this backend."""
        raise NotImplementedError

    @abstractmethod
    def generate(
        self,
        prompt: str,
        **kwargs: Any,
    ) -> Any:
        """Generate output from a prompt."""
        raise NotImplementedError

    @abstractmethod
    def unload(self) -> None:
        """Release loaded model resources."""
        raise NotImplementedError