from __future__ import annotations

import os
import platform
from pathlib import Path


class ModelStorage:
    """Manage Icebrew's local model-storage paths."""

    def __init__(self, root: str | Path | None = None):
        if root is None:
            root = self.default_root()

        self.root = Path(root).expanduser().resolve()
        self.models_dir = self.root / "models"
        self.manifests_dir = self.root / "manifests"

    @staticmethod
    def default_root() -> Path:
        env_root = os.environ.get("ICEBREW_HOME")

        if env_root:
            return Path(env_root).expanduser()

        system = platform.system()

        if system == "Windows":
            base = os.environ.get("APPDATA")
            if base:
                return Path(base) / "Icebrew"
            return Path.home() / "AppData" / "Roaming" / "Icebrew"

        if system == "Darwin":
            return (
                Path.home()
                / "Library"
                / "Application Support"
                / "Icebrew"
            )

        base = os.environ.get("XDG_DATA_HOME")

        if base:
            return Path(base) / "icebrew"

        return Path.home() / ".local" / "share" / "icebrew"

    def initialize(self) -> None:
        self.models_dir.mkdir(parents=True, exist_ok=True)
        self.manifests_dir.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def validate_model_id(model_id: str) -> str:
        if not isinstance(model_id, str) or not model_id.strip():
            raise ValueError("Model ID must be a non-empty string.")

        model_id = model_id.strip()

        if model_id in {".", ".."}:
            raise ValueError("Invalid model ID.")

        if any(
            character not in
            "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._-"
            for character in model_id
        ):
            raise ValueError(
                "Model ID may only contain letters, numbers, dots, "
                "underscores and hyphens."
            )

        return model_id

    def model_path(self, model_id: str) -> Path:
        model_id = self.validate_model_id(model_id)
        return self.models_dir / model_id

    def manifest_path(self, model_id: str) -> Path:
        model_id = self.validate_model_id(model_id)
        return self.manifests_dir / f"{model_id}.json"

    def is_within_storage(self, path: str | Path) -> bool:
        path = Path(path).resolve()

        try:
            path.relative_to(self.root)
            return True
        except ValueError:
            return False