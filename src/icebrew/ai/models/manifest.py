from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


MANIFEST_VERSION = 1


@dataclass(frozen=True)
class InstalledManifest:
    model_id: str
    model_name: str
    installed_at: str
    model_metadata: dict[str, Any]
    manifest_version: int = MANIFEST_VERSION

    @classmethod
    def create(cls, model) -> "InstalledManifest":
        return cls(
            model_id=model.id,
            model_name=model.name,
            installed_at=datetime.now(timezone.utc).isoformat(),
            model_metadata=model.to_dict(),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "manifest_version": self.manifest_version,
            "model_id": self.model_id,
            "model_name": self.model_name,
            "installed_at": self.installed_at,
            "model_metadata": self.model_metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "InstalledManifest":
        if not isinstance(data, dict):
            raise ValueError("Manifest must be a JSON object.")

        version = data.get("manifest_version")

        if version != MANIFEST_VERSION:
            raise ValueError(
                f"Unsupported manifest version: {version}"
            )

        required = (
            "model_id",
            "model_name",
            "installed_at",
            "model_metadata",
        )

        for field in required:
            if field not in data:
                raise ValueError(f"Manifest missing field: {field}")

        if not isinstance(data["model_metadata"], dict):
            raise ValueError("model_metadata must be an object.")

        return cls(
            model_id=data["model_id"],
            model_name=data["model_name"],
            installed_at=data["installed_at"],
            model_metadata=data["model_metadata"],
            manifest_version=version,
        )

    def save(self, path: str | Path) -> None:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)

        temporary = path.with_name(path.name + ".tmp")

        temporary.write_text(
            json.dumps(self.to_dict(), indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

        temporary.replace(path)

    @classmethod
    def load(cls, path: str | Path) -> "InstalledManifest":
        path = Path(path)

        data = json.loads(path.read_text(encoding="utf-8"))

        return cls.from_dict(data)