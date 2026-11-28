"""Curated model catalog."""

from __future__ import annotations

from collections.abc import Iterable

from icebrew.ai.catalog.schema import ModelMetadata


class CatalogError(ValueError):
    """Raised when catalog operations fail."""


class ModelCatalog:
    """Validated in-memory catalog of model metadata."""

    def __init__(self, models: Iterable[ModelMetadata] = ()) -> None:
        self._models: dict[str, ModelMetadata] = {}

        for model in models:
            self.register(model)

    def register(self, model: ModelMetadata) -> None:
        if not isinstance(model, ModelMetadata):
            raise TypeError("model must be a ModelMetadata instance")

        if model.id in self._models:
            raise CatalogError(f"Model already exists in catalog: {model.id}")

        self._models[model.id] = model

    def get(self, model_id: str) -> ModelMetadata:
        try:
            return self._models[model_id]
        except KeyError as exc:
            raise CatalogError(f"Unknown catalog model: {model_id}") from exc

    def exists(self, model_id: str) -> bool:
        return model_id in self._models

    def remove(self, model_id: str) -> ModelMetadata:
        try:
            return self._models.pop(model_id)
        except KeyError as exc:
            raise CatalogError(f"Unknown catalog model: {model_id}") from exc

    def list_models(
        self,
        *,
        task: str | None = None,
        backend: str | None = None,
        model_format: str | None = None,
        provider: str | None = None,
        tag: str | None = None,
        query: str | None = None,
    ) -> list[ModelMetadata]:
        results = list(self._models.values())

        if task is not None:
            results = [
                model for model in results
                if task in model.tasks
            ]

        if backend is not None:
            results = [
                model for model in results
                if backend in model.backends
            ]

        if model_format is not None:
            results = [
                model for model in results
                if model_format in model.formats
            ]

        if provider is not None:
            results = [
                model for model in results
                if model.provider.casefold() == provider.casefold()
            ]

        if tag is not None:
            results = [
                model for model in results
                if tag.casefold() in {
                    item.casefold() for item in model.tags
                }
            ]

        if query is not None:
            needle = query.casefold().strip()

            if needle:
                results = [
                    model for model in results
                    if needle in model.id.casefold()
                    or needle in model.name.casefold()
                    or needle in model.description.casefold()
                    or needle in model.provider.casefold()
                    or any(
                        needle in item.casefold()
                        for item in model.tags
                    )
                ]

        return sorted(results, key=lambda model: model.id.casefold())

    def to_dict(self) -> dict[str, dict]:
        return {
            model_id: model.to_dict()
            for model_id, model in sorted(self._models.items())
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ModelCatalog":
        if not isinstance(data, dict):
            raise TypeError("Catalog data must be a dictionary")

        models = [
            ModelMetadata.from_dict(model_data)
            for model_data in data.values()
        ]

        return cls(models)

    def __len__(self) -> int:
        return len(self._models)

    def __contains__(self, model_id: str) -> bool:
        return model_id in self._models