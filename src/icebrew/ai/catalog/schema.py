# src/icebrew/ai/catalog/schema.py

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class ModelFile:
    filename: str
    sha256: str | None = None
    size_bytes: int | None = None

    def __post_init__(self) -> None:
        if not self.filename or not self.filename.strip():
            raise ValueError("Model file filename cannot be empty.")

        if self.sha256 is not None:
            checksum = self.sha256.strip().lower()

            if len(checksum) != 64 or any(
                character not in "0123456789abcdef"
                for character in checksum
            ):
                raise ValueError(
                    "SHA-256 checksum must contain exactly 64 hexadecimal characters."
                )

            object.__setattr__(self, "sha256", checksum)

        if self.size_bytes is not None:
            if isinstance(self.size_bytes, bool) or not isinstance(
                self.size_bytes, int
            ):
                raise TypeError("size_bytes must be an integer.")

            if self.size_bytes < 0:
                raise ValueError("size_bytes cannot be negative.")

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ModelFile:
        if not isinstance(data, dict):
            raise TypeError("Model file metadata must be a dictionary.")

        return cls(
            filename=data["filename"],
            sha256=data.get("sha256"),
            size_bytes=data.get("size_bytes"),
        )


@dataclass(frozen=True)
class ModelSource:
    repository: str
    revision: str | None = None
    url: str | None = None

    def __post_init__(self) -> None:
        if not self.repository or not self.repository.strip():
            raise ValueError("Model repository cannot be empty.")

        if self.revision is not None and not self.revision.strip():
            raise ValueError("Revision cannot be an empty string.")

        if self.url is not None and not self.url.strip():
            raise ValueError("URL cannot be an empty string.")

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ModelSource:
        if not isinstance(data, dict):
            raise TypeError("Model source must be a dictionary.")

        return cls(
            repository=data["repository"],
            revision=data.get("revision"),
            url=data.get("url"),
        )


@dataclass(frozen=True)
class ModelRequirements:
    estimated_ram_gb: float | None = None
    gpu_optional: bool = True
    minimum_ram_gb: float | None = None
    notes: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        for name in ("estimated_ram_gb", "minimum_ram_gb"):
            value = getattr(self, name)

            if value is not None:
                if isinstance(value, bool) or not isinstance(value, (int, float)):
                    raise TypeError(f"{name} must be numeric.")

                if value <= 0:
                    raise ValueError(f"{name} must be greater than zero.")

        if not isinstance(self.gpu_optional, bool):
            raise TypeError("gpu_optional must be a boolean.")

        object.__setattr__(self, "notes", tuple(self.notes))

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ModelRequirements:
        if not isinstance(data, dict):
            raise TypeError("Requirements must be a dictionary.")

        return cls(
            estimated_ram_gb=data.get("estimated_ram_gb"),
            gpu_optional=data.get("gpu_optional", True),
            minimum_ram_gb=data.get("minimum_ram_gb"),
            notes=tuple(data.get("notes", ())),
        )


@dataclass(frozen=True)
class ModelMetadata:
    id: str
    name: str
    provider: str
    tasks: tuple[str, ...]
    formats: tuple[str, ...]
    source: ModelSource
    license: str
    backends: tuple[str, ...]
    files: tuple[ModelFile, ...] = ()
    requirements: ModelRequirements = field(
        default_factory=ModelRequirements
    )
    description: str | None = None
    tags: tuple[str, ...] = ()
    metadata_version: int = 1

    def __post_init__(self) -> None:
        for field_name in ("id", "name", "provider", "license"):
            value = getattr(self, field_name)

            if not isinstance(value, str):
                raise TypeError(f"{field_name} must be a string.")

            if not value.strip():
                raise ValueError(f"{field_name} cannot be empty.")

        for field_name in ("tasks", "formats", "backends"):
            values = tuple(getattr(self, field_name))

            if not values:
                raise ValueError(f"{field_name} cannot be empty.")

            if any(
                not isinstance(value, str) or not value.strip()
                for value in values
            ):
                raise ValueError(
                    f"Every entry in {field_name} must be a non-empty string."
                )

            if len(set(values)) != len(values):
                raise ValueError(f"{field_name} cannot contain duplicates.")

            object.__setattr__(self, field_name, values)

        object.__setattr__(self, "files", tuple(self.files))
        object.__setattr__(self, "tags", tuple(self.tags))

        if self.description is not None and not isinstance(
            self.description, str
        ):
            raise TypeError("description must be a string or None.")

        if (
            isinstance(self.metadata_version, bool)
            or not isinstance(self.metadata_version, int)
        ):
            raise TypeError("metadata_version must be an integer.")

        if self.metadata_version < 1:
            raise ValueError("metadata_version must be at least 1.")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ModelMetadata:
        if not isinstance(data, dict):
            raise TypeError("Model metadata must be a dictionary.")

        return cls(
            id=data["id"],
            name=data["name"],
            provider=data["provider"],
            tasks=tuple(data["tasks"]),
            formats=tuple(data["formats"]),
            source=ModelSource.from_dict(data["source"]),
            license=data["license"],
            backends=tuple(data["backends"]),
            files=tuple(
                ModelFile.from_dict(item)
                for item in data.get("files", ())
            ),
            requirements=ModelRequirements.from_dict(
                data.get("requirements", {})
            ),
            description=data.get("description"),
            tags=tuple(data.get("tags", ())),
            metadata_version=data.get("metadata_version", 1),
        )