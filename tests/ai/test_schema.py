# tests/ai/test_schema.py

import pytest

from icebrew.ai.catalog.schema import (
    ModelFile,
    ModelMetadata,
    ModelRequirements,
    ModelSource,
)


@pytest.fixture
def sample_model():
    return ModelMetadata(
        id="qwen-test",
        name="Qwen Test",
        provider="Qwen",
        tasks=("text-generation",),
        formats=("gguf",),
        source=ModelSource(
            repository="example/repository",
            revision="main",
        ),
        license="Apache-2.0",
        backends=("llama_cpp",),
        files=(
            ModelFile(
                filename="model.gguf",
                sha256="a" * 64,
                size_bytes=1024,
            ),
        ),
        requirements=ModelRequirements(
            estimated_ram_gb=4.0,
            gpu_optional=True,
        ),
        tags=("small", "local"),
    )


def test_model_metadata_creation(sample_model):
    assert sample_model.id == "qwen-test"
    assert sample_model.tasks == ("text-generation",)
    assert sample_model.backends == ("llama_cpp",)


def test_model_metadata_serialization(sample_model):
    data = sample_model.to_dict()

    assert data["id"] == "qwen-test"
    assert data["source"]["repository"] == "example/repository"
    assert data["files"][0]["filename"] == "model.gguf"
    assert data["requirements"]["estimated_ram_gb"] == 4.0


def test_model_metadata_round_trip(sample_model):
    restored = ModelMetadata.from_dict(sample_model.to_dict())

    assert restored == sample_model


def test_empty_model_id_rejected():
    with pytest.raises(ValueError):
        ModelMetadata(
            id="",
            name="Test",
            provider="Test",
            tasks=("text-generation",),
            formats=("gguf",),
            source=ModelSource("example/repository"),
            license="MIT",
            backends=("llama_cpp",),
        )


def test_empty_tasks_rejected():
    with pytest.raises(ValueError):
        ModelMetadata(
            id="test",
            name="Test",
            provider="Test",
            tasks=(),
            formats=("gguf",),
            source=ModelSource("example/repository"),
            license="MIT",
            backends=("llama_cpp",),
        )


def test_duplicate_tasks_rejected():
    with pytest.raises(ValueError):
        ModelMetadata(
            id="test",
            name="Test",
            provider="Test",
            tasks=("generation", "generation"),
            formats=("gguf",),
            source=ModelSource("example/repository"),
            license="MIT",
            backends=("llama_cpp",),
        )


def test_invalid_sha256_rejected():
    with pytest.raises(ValueError):
        ModelFile(
            filename="model.gguf",
            sha256="invalid",
        )


def test_sha256_normalized():
    file = ModelFile(
        filename="model.gguf",
        sha256="A" * 64,
    )

    assert file.sha256 == "a" * 64


def test_negative_file_size_rejected():
    with pytest.raises(ValueError):
        ModelFile(
            filename="model.gguf",
            size_bytes=-1,
        )


def test_empty_repository_rejected():
    with pytest.raises(ValueError):
        ModelSource(repository="")


def test_invalid_ram_rejected():
    with pytest.raises(ValueError):
        ModelRequirements(estimated_ram_gb=0)


def test_boolean_ram_rejected():
    with pytest.raises(TypeError):
        ModelRequirements(estimated_ram_gb=True)


def test_invalid_metadata_version_rejected():
    with pytest.raises(ValueError):
        ModelMetadata(
            id="test",
            name="Test",
            provider="Test",
            tasks=("generation",),
            formats=("gguf",),
            source=ModelSource("example/repository"),
            license="MIT",
            backends=("llama_cpp",),
            metadata_version=0,
        )


def test_from_dict_reconstruction(sample_model):
    reconstructed = ModelMetadata.from_dict(sample_model.to_dict())

    assert reconstructed.name == sample_model.name
    assert reconstructed.files == sample_model.files
    assert reconstructed.requirements == sample_model.requirements


def test_metadata_is_immutable(sample_model):
    with pytest.raises(AttributeError):
        sample_model.name = "Modified"