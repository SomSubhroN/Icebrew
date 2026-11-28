from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from icebrew.ai.catalog.schema import (
    ModelFile,
    ModelMetadata,
    ModelSource,
)
from icebrew.ai.models import ModelManager, ModelStorage


class FakeDownloadManager:
    """A deterministic fake downloader for model lifecycle tests."""

    def download_model(
        self,
        model,
        destination_dir,
        *,
        url_resolver,
        overwrite=False,
        resume=True,
        progress_callback=None,
        cancel_callback=None,
    ):
        destination_dir = Path(destination_dir)
        results = []

        for model_file in model.files:
            if cancel_callback and cancel_callback():
                raise RuntimeError("Cancelled")

            url = url_resolver(model, model_file)

            file_path = destination_dir / model_file.filename
            file_path.write_bytes(b"test-model-data")

            file_content = file_path.read_bytes()

            results.append(
                type(
                    "FakeDownloadResult",
                    (),
                    {
                        "url": url,
                        "destination": file_path,
                        "size_bytes": len(file_content),
                        "sha256": hashlib.sha256(
                            file_content
                        ).hexdigest(),
                        "resumed": False,
                        "already_exists": False,
                    },
                )()
            )

        return results


@pytest.fixture
def model():
    data = b"test-model-data"

    return ModelMetadata(
        id="test-model",
        name="Test Model",
        provider="test",
        tasks=["text-generation"],
        formats=["gguf"],
        source=ModelSource(
            repository="test/repository",
        ),
        license="test-license",
        backends=["llama.cpp"],
        files=[
            ModelFile(
                filename="model.gguf",
                sha256=hashlib.sha256(data).hexdigest(),
                size_bytes=len(data),
            )
        ],
    )


@pytest.fixture
def manager(tmp_path):
    return ModelManager(
        storage=ModelStorage(tmp_path / "icebrew"),
        download_manager=FakeDownloadManager(),
    )


def resolver(model, model_file):
    return f"https://example.com/{model_file.filename}"


# ---------------------------------------------------------
# Storage
# ---------------------------------------------------------


def test_storage_initializes(manager):
    assert manager.storage.models_dir.exists()
    assert manager.storage.manifests_dir.exists()


def test_model_id_validation():
    assert (
        ModelStorage.validate_model_id("test-model")
        == "test-model"
    )

    with pytest.raises(ValueError):
        ModelStorage.validate_model_id("../outside")

    with pytest.raises(ValueError):
        ModelStorage.validate_model_id("model/other")

    with pytest.raises(ValueError):
        ModelStorage.validate_model_id("")

    with pytest.raises(ValueError):
        ModelStorage.validate_model_id(".")

    with pytest.raises(ValueError):
        ModelStorage.validate_model_id("..")


# ---------------------------------------------------------
# Installation
# ---------------------------------------------------------


def test_install_model(manager, model):
    results = manager.install(
        model,
        url_resolver=resolver,
    )

    destination = manager.storage.model_path(model.id)

    assert destination.exists()
    assert destination.is_dir()
    assert (destination / "model.gguf").exists()
    assert (destination / "manifest.json").exists()
    assert len(results) == 1


def test_install_model_file_contents(manager, model):
    manager.install(
        model,
        url_resolver=resolver,
    )

    file_path = (
        manager.storage.model_path(model.id)
        / "model.gguf"
    )

    assert file_path.read_bytes() == b"test-model-data"


def test_get_manifest(manager, model):
    manager.install(
        model,
        url_resolver=resolver,
    )

    manifest = manager.get_manifest(model.id)

    assert manifest is not None
    assert manifest.model_id == model.id
    assert manifest.model_name == model.name
    assert manifest.model_metadata["id"] == model.id


def test_list_installed(manager, model):
    manager.install(
        model,
        url_resolver=resolver,
    )

    results = manager.list_installed()

    assert len(results) == 1
    assert results[0]["model_id"] == model.id
    assert results[0]["status"] == "installed"


# ---------------------------------------------------------
# Verification
# ---------------------------------------------------------


def test_verify_model(manager, model):
    manager.install(
        model,
        url_resolver=resolver,
    )

    result = manager.verify(model.id)

    assert result["verified"] is True
    assert result["status"] == "installed"
    assert result["files"][0]["status"] == "ok"


def test_verify_missing_model(manager):
    result = manager.verify("missing-model")

    assert result["status"] == "missing"
    assert result["verified"] is False


def test_verify_missing_file(manager, model):
    manager.install(
        model,
        url_resolver=resolver,
    )

    file_path = (
        manager.storage.model_path(model.id)
        / "model.gguf"
    )

    file_path.unlink()

    result = manager.verify(model.id)

    assert result["verified"] is False
    assert result["files"][0]["status"] == "missing"


def test_verify_hash_mismatch(manager, model):
    manager.install(
        model,
        url_resolver=resolver,
    )

    file_path = (
        manager.storage.model_path(model.id)
        / "model.gguf"
    )

    original = b"test-model-data"
    corrupted = b"X" + original[1:]

    assert len(corrupted) == len(original)

    file_path.write_bytes(corrupted)

    result = manager.verify(model.id)

    assert result["verified"] is False
    assert result["files"][0]["status"] == "hash_mismatch"

def test_verify_size_mismatch(manager, model):
    manager.install(
        model,
        url_resolver=resolver,
    )

    file_path = (
        manager.storage.model_path(model.id)
        / "model.gguf"
    )

    file_path.write_bytes(b"short")

    result = manager.verify(model.id)

    assert result["verified"] is False
    assert result["files"][0]["status"] == "size_mismatch"


# ---------------------------------------------------------
# Removal
# ---------------------------------------------------------


def test_remove_requires_confirmation(manager, model):
    manager.install(
        model,
        url_resolver=resolver,
    )

    with pytest.raises(PermissionError):
        manager.remove(model.id)


def test_remove_model(manager, model):
    manager.install(
        model,
        url_resolver=resolver,
    )

    result = manager.remove(
        model.id,
        confirm=True,
    )

    assert result is True
    assert not manager.storage.model_path(model.id).exists()


def test_remove_missing_model(manager):
    result = manager.remove(
        "missing-model",
        confirm=True,
    )

    assert result is False


# ---------------------------------------------------------
# Existing installations
# ---------------------------------------------------------


def test_install_existing_model_requires_overwrite(
    manager,
    model,
):
    manager.install(
        model,
        url_resolver=resolver,
    )

    with pytest.raises(FileExistsError):
        manager.install(
            model,
            url_resolver=resolver,
        )


# ---------------------------------------------------------
# Incomplete and corrupted installations
# ---------------------------------------------------------


def test_incomplete_installation_is_detected(manager):
    directory = manager.storage.model_path("broken-model")
    directory.mkdir()

    results = manager.list_installed()

    entry = next(
        item
        for item in results
        if item["model_id"] == "broken-model"
    )

    assert entry["status"] == "incomplete"


def test_incomplete_model_verification(manager):
    directory = manager.storage.model_path("broken-model")
    directory.mkdir()

    result = manager.verify("broken-model")

    assert result["status"] == "incomplete"
    assert result["verified"] is False


# ---------------------------------------------------------
# Unsafe filenames
# ---------------------------------------------------------


def test_install_unsafe_filename(manager):
    unsafe_model = ModelMetadata(
        id="unsafe-model",
        name="Unsafe",
        provider="test",
        tasks=["text-generation"],
        formats=["gguf"],
        source=ModelSource(
            repository="test/repository",
        ),
        license="test-license",
        backends=["llama.cpp"],
        files=[
            ModelFile(
                filename="../outside.gguf",
            ),
        ],
    )

    with pytest.raises(ValueError):
        manager.install(
            unsafe_model,
            url_resolver=resolver,
        )