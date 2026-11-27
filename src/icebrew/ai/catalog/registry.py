# src/icebrew/ai/catalog/registry.py

from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

from icebrew.ai.catalog.schema import ModelMetadata


class ModelRegistry:
    """Validated in-memory registry for AI model metadata."""

    def __init__(
        self,
        models: Iterable[ModelMetadata] | None = None,
    ) -> None:
        self._models: dict[str, ModelMetadata] = {}

        if models is not None:
            for model in models:
                self.register(model)

    def register(self, model: ModelMetadata) -> None:
        """Register a model. Duplicate IDs are rejected."""
        if not isinstance(model, ModelMetadata):
            raise TypeError("Only ModelMetadata instances can be registered.")

        if model.id in self._models:
            raise ValueError(f"Model '{model.id}' is already registered.")

        self._models[model.id] = model

    def get(self, model_id: str) -> ModelMetadata:
        """Retrieve a model by ID."""
        try:
            return self._models[model_id]
        except KeyError:
            raise KeyError(f"Model '{model_id}' was not found.") from None

    def exists(self, model_id: str) -> bool:
        """Check whether a model exists in the registry."""
        return model_id in self._models

    def remove(self, model_id: str) -> ModelMetadata:
        """Remove and return a model."""
        try:
            return self._models.pop(model_id)
        except KeyError:
            raise KeyError(f"Model '{model_id}' was not found.") from None

    def list_models(
        self,
        *,
        task: str | None = None,
        backend: str | None = None,
        model_format: str | None = None,
        provider: str | None = None,
        tag: str | None = None,
    ) -> list[ModelMetadata]:
        """List registered models with optional filters."""
        models = list(self._models.values())

        if task is not None:
            models = [m for m in models if task in m.tasks]

        if backend is not None:
            models = [m for m in models if backend in m.backends]

        if model_format is not None:
            models = [m for m in models if model_format in m.formats]

        if provider is not None:
            models = [m for m in models if m.provider.casefold() == provider.casefold()]

        if tag is not None:
            models = [m for m in models if tag in m.tags]

        return sorted(models, key=lambda m: m.id.casefold())

    def __len__(self) -> int:
        return len(self._models)

    def __contains__(self, model_id: str) -> bool:
        return model_id in self._models

    def to_dict(self) -> dict:
        """Serialize registry to a dictionary."""
        return {
            "registry_version": 1,
            "models": [
                model.to_dict()
                for model in self.list_models()
            ],
        }

    @classmethod
    def from_dict(cls, data: dict) -> ModelRegistry:
        """Reconstruct a registry from a dictionary."""
        if not isinstance(data, dict):
            raise TypeError("Registry data must be a dictionary.")

        models_data = data.get("models")

        if not isinstance(models_data, list):
            raise ValueError("Registry data must contain a models list.")

        models = [
            ModelMetadata.from_dict(item)
            for item in models_data
        ]

        return cls(models)

    def save(self, file_path: str | Path) -> None:
        """Save registry to JSON."""
        path = Path(file_path)

        if path.exists() and path.is_dir():
            raise IsADirectoryError(f"Cannot save registry to directory: {path}")

        path.parent.mkdir(parents=True, exist_ok=True)

        payload = self.to_dict()

        path.write_text(
            json.dumps(payload, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    @classmethod
    def load(cls, file_path: str | Path) -> ModelRegistry:
        """Load registry from JSON."""
        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(f"Registry file not found: {path}")

        if not path.is_file():
            raise IsADirectoryError(f"Registry path is not a file: {path}")

        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise ValueError(
                f"Invalid registry JSON in '{path}': {exc}"
            ) from exc

        return cls.from_dict(data)