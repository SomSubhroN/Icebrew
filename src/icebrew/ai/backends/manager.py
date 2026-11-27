# src/icebrew/ai/backends/manager.py

from __future__ import annotations

from typing import Iterable

from icebrew.ai.backends.base import ModelBackend
from icebrew.ai.catalog.schema import ModelMetadata


class BackendManager:
    """Manage registered AI inference backends."""

    def __init__(
        self,
        backends: Iterable[ModelBackend] | None = None,
    ) -> None:
        self._backends: dict[str, ModelBackend] = {}

        if backends is not None:
            for backend in backends:
                self.register(backend)

    def register(self, backend: ModelBackend) -> None:
        """Register a backend instance."""
        if not isinstance(backend, ModelBackend):
            raise TypeError("Backend must inherit from ModelBackend.")

        identifier = backend.identifier

        if not isinstance(identifier, str) or not identifier.strip():
            raise ValueError("Backend identifier cannot be empty.")

        if identifier in self._backends:
            raise ValueError(
                f"Backend '{identifier}' is already registered."
            )

        self._backends[identifier] = backend

    def get(self, identifier: str) -> ModelBackend:
        """Retrieve a backend by identifier."""
        try:
            return self._backends[identifier]
        except KeyError:
            raise KeyError(
                f"Backend '{identifier}' is not registered."
            ) from None

    def exists(self, identifier: str) -> bool:
        return identifier in self._backends

    def remove(self, identifier: str) -> ModelBackend:
        """Remove and return a registered backend."""
        try:
            return self._backends.pop(identifier)
        except KeyError:
            raise KeyError(
                f"Backend '{identifier}' is not registered."
            ) from None

    def list_backends(
        self,
        *,
        available_only: bool = False,
    ) -> list[ModelBackend]:
        """Return registered backends."""
        backends = list(self._backends.values())

        if available_only:
            backends = [
                backend
                for backend in backends
                if backend.is_available()
            ]

        return sorted(
            backends,
            key=lambda backend: backend.identifier.casefold(),
        )

    def compatible_backends(
        self,
        model: ModelMetadata,
        *,
        available_only: bool = False,
    ) -> list[ModelBackend]:
        """Find registered backends compatible with a model."""
        compatible = []

        for backend in self._backends.values():
            if backend.identifier not in model.backends:
                continue

            if not set(model.formats).intersection(
                backend.supported_formats
            ):
                continue

            if not set(model.tasks).intersection(
                backend.supported_tasks
            ):
                continue

            if available_only and not backend.is_available():
                continue

            compatible.append(backend)

        return sorted(
            compatible,
            key=lambda backend: backend.identifier.casefold(),
        )

    def resolve(
        self,
        model: ModelMetadata,
        *,
        preferred: str | None = None,
        require_available: bool = True,
    ) -> ModelBackend:
        """Resolve a compatible backend for a model."""

        if preferred is not None:
            backend = self.get(preferred)

            if backend.identifier not in model.backends:
                raise ValueError(
                    f"Backend '{preferred}' is not listed as supported "
                    f"for model '{model.id}'."
                )

            if not set(model.formats).intersection(
                backend.supported_formats
            ):
                raise ValueError(
                    f"Backend '{preferred}' does not support any "
                    f"format declared by model '{model.id}'."
                )

            if not set(model.tasks).intersection(
                backend.supported_tasks
            ):
                raise ValueError(
                    f"Backend '{preferred}' does not support any "
                    f"task declared by model '{model.id}'."
                )

            if require_available and not backend.is_available():
                raise RuntimeError(
                    f"Backend '{preferred}' is not available."
                )

            return backend

        compatible = self.compatible_backends(
            model,
            available_only=require_available,
        )

        if not compatible:
            if require_available:
                raise RuntimeError(
                    f"No available compatible backend was found "
                    f"for model '{model.id}'."
                )

            raise LookupError(
                f"No registered compatible backend was found "
                f"for model '{model.id}'."
            )

        return compatible[0]

    def __len__(self) -> int:
        return len(self._backends)

    def __contains__(self, identifier: str) -> bool:
        return identifier in self._backends