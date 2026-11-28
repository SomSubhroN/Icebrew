# src/icebrew/ai/catalog/__init__.py

from icebrew.ai.catalog.schema import (
    ModelFile,
    ModelMetadata,
    ModelRequirements,
    ModelSource,
)
from icebrew.ai.catalog.registry import ModelRegistry
"""AI model catalog interfaces."""

from icebrew.ai.catalog.schema import (
    ModelFile,
    ModelMetadata,
    ModelRequirements,
    ModelSource,
)
from icebrew.ai.catalog.registry import ModelRegistry
from icebrew.ai.catalog.catalog import ModelCatalog, CatalogError
from icebrew.ai.catalog.source_resolver import (
    SourceResolver,
    SourceResolutionError,
)


__all__ = [
    "ModelFile",
    "ModelMetadata",
    "ModelRequirements",
    "ModelSource",
    "ModelRegistry",
    "ModelFile",
    "ModelMetadata",
    "ModelRequirements",
    "ModelSource",
    "ModelRegistry",
    "ModelCatalog",
    "CatalogError",
    "SourceResolver",
    "SourceResolutionError",
]