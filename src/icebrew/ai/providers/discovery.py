"""Hugging Face model discovery utilities."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class DiscoveredModel:
    """Normalized information about a discovered repository."""

    repository: str
    pipeline_tag: str | None = None
    library_name: str | None = None
    downloads: int | None = None
    likes: int | None = None
    tags: tuple[str, ...] = ()
    description: str | None = None

    def to_dict(self) -> dict:
        return {
            "repository": self.repository,
            "pipeline_tag": self.pipeline_tag,
            "library_name": self.library_name,
            "downloads": self.downloads,
            "likes": self.likes,
            "tags": list(self.tags),
            "description": self.description,
        }