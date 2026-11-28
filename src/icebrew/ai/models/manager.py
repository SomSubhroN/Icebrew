from __future__ import annotations

import hashlib
import json
import os
import shutil
import tempfile
from pathlib import Path

from icebrew.ai.catalog.schema import ModelMetadata
from icebrew.ai.downloads.manager import (
    DownloadManager,
    DownloadResult,
)
from icebrew.ai.models.manifest import InstalledManifest
from icebrew.ai.models.storage import ModelStorage


class ModelManager:
    """Manage the installation lifecycle of local Icebrew models."""

    MANIFEST_FILENAME = "manifest.json"

    def __init__(
        self,
        storage: ModelStorage | None = None,
        download_manager: DownloadManager | None = None,
    ):
        self.storage = storage or ModelStorage()
        self.download_manager = download_manager or DownloadManager()
        self.storage.initialize()

    def install(
        self,
        model: ModelMetadata,
        *,
        url_resolver,
        overwrite: bool = False,
        resume: bool = True,
        progress_callback=None,
        cancel_callback=None,
    ) -> list[DownloadResult]:
        model_id = self.storage.validate_model_id(model.id)
        destination = self.storage.model_path(model_id)

        if destination.exists() and not overwrite:
            raise FileExistsError(
                f"Model is already installed or partially present: {model_id}"
            )

        # Validate filenames before downloads. Only flat filenames are permitted.
        for model_file in model.files:
            filename = model_file.filename

            if not filename or Path(filename).name != filename:
                raise ValueError(
                    f"Unsafe model filename: {filename!r}"
                )

            if filename in {".", "..", self.MANIFEST_FILENAME}:
                raise ValueError(
                    f"Reserved or unsafe model filename: {filename!r}"
                )

        staging = Path(
            tempfile.mkdtemp(
                prefix=f".{model_id}.install-",
                dir=self.storage.models_dir,
            )
        )

        backup = destination.with_name(f".{model_id}.backup")

        try:
            results = self.download_manager.download_model(
                model,
                staging,
                url_resolver=url_resolver,
                overwrite=False,
                resume=resume,
                progress_callback=progress_callback,
                cancel_callback=cancel_callback,
            )

            manifest = InstalledManifest.create(model)
            manifest.save(staging / self.MANIFEST_FILENAME)

            # Ensure existing installation is not destroyed prematurely.
            if destination.exists():
                if not overwrite:
                    raise FileExistsError(
                        f"Model already exists: {model_id}"
                    )

                if backup.exists():
                    raise FileExistsError(
                        f"Backup path already exists: {backup}"
                    )

                destination.rename(backup)

            try:
                staging.rename(destination)
            except Exception:
                if backup.exists() and not destination.exists():
                    backup.rename(destination)
                raise

            # Installation succeeded. Remove the previous installation.
            if backup.exists():
                shutil.rmtree(backup)

            return results

        except Exception:
            # Remove only this operation's staging directory.
            if staging.exists():
                shutil.rmtree(staging, ignore_errors=True)

            raise

    def get_manifest(
        self,
        model_id: str,
    ) -> InstalledManifest | None:
        path = self.storage.model_path(model_id)

        if not path.is_dir():
            return None

        manifest_path = path / self.MANIFEST_FILENAME

        if not manifest_path.is_file():
            return None

        return InstalledManifest.load(manifest_path)

    def list_installed(self) -> list[dict]:
        results = []

        for directory in self.storage.models_dir.iterdir():
            if not directory.is_dir():
                continue

            manifest_path = directory / self.MANIFEST_FILENAME

            if not manifest_path.is_file():
                results.append(
                    {
                        "model_id": directory.name,
                        "status": "incomplete",
                        "path": str(directory),
                    }
                )
                continue

            try:
                manifest = InstalledManifest.load(manifest_path)

                results.append(
                    {
                        "model_id": manifest.model_id,
                        "name": manifest.model_name,
                        "status": "installed",
                        "installed_at": manifest.installed_at,
                        "path": str(directory),
                    }
                )

            except (ValueError, json.JSONDecodeError, OSError):
                results.append(
                    {
                        "model_id": directory.name,
                        "status": "corrupted",
                        "path": str(directory),
                    }
                )

        return sorted(results, key=lambda item: item["model_id"])

    def verify(self, model_id: str) -> dict:
        directory = self.storage.model_path(model_id)

        if not directory.is_dir():
            return {
                "model_id": model_id,
                "status": "missing",
                "verified": False,
                "files": [],
            }

        manifest_path = directory / self.MANIFEST_FILENAME

        if not manifest_path.is_file():
            return {
                "model_id": model_id,
                "status": "incomplete",
                "verified": False,
                "files": [],
            }

        try:
            manifest = InstalledManifest.load(manifest_path)
            metadata = ModelMetadata.from_dict(
                manifest.model_metadata
            )

        except (ValueError, TypeError, KeyError, OSError):
            return {
                "model_id": model_id,
                "status": "corrupted",
                "verified": False,
                "files": [],
            }

        checks = []

        for model_file in metadata.files:
            file_path = directory / model_file.filename

            if not file_path.is_file():
                checks.append(
                    {
                        "filename": model_file.filename,
                        "status": "missing",
                    }
                )
                continue

            size = file_path.stat().st_size

            if (
                model_file.size_bytes is not None
                and size != model_file.size_bytes
            ):
                checks.append(
                    {
                        "filename": model_file.filename,
                        "status": "size_mismatch",
                        "expected": model_file.size_bytes,
                        "actual": size,
                    }
                )
                continue

            if model_file.sha256:
                digest = hashlib.sha256()

                with file_path.open("rb") as handle:
                    while chunk := handle.read(1024 * 1024):
                        digest.update(chunk)

                actual_hash = digest.hexdigest()

                if actual_hash.lower() != model_file.sha256.lower():
                    checks.append(
                        {
                            "filename": model_file.filename,
                            "status": "hash_mismatch",
                        }
                    )
                    continue

            checks.append(
                {
                    "filename": model_file.filename,
                    "status": "ok",
                }
            )

        verified = all(
            item["status"] == "ok"
            for item in checks
        )

        return {
            "model_id": model_id,
            "status": "installed" if verified else "corrupted",
            "verified": verified,
            "files": checks,
        }

    def remove(
        self,
        model_id: str,
        *,
        confirm: bool = False,
    ) -> bool:
        if confirm is not True:
            raise PermissionError(
                "Model removal requires explicit confirm=True."
            )

        model_id = self.storage.validate_model_id(model_id)
        target = self.storage.model_path(model_id)

        if not target.exists():
            return False

        resolved = target.resolve()

        if not self.storage.is_within_storage(resolved):
            raise PermissionError(
                "Refusing to remove a path outside Icebrew storage."
            )

        if resolved == self.storage.models_dir.resolve():
            raise PermissionError(
                "Refusing to remove the model-storage directory itself."
            )

        if not resolved.is_dir():
            raise ValueError(
                "Expected an installed model directory."
            )

        shutil.rmtree(resolved)

        return True