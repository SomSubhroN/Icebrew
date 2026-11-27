# tests/ai/test_registry.py

import pytest

from icebrew.ai.catalog.schema import (
    ModelMetadata,
    ModelSource,
)
from icebrew.ai.catalog.registry import ModelRegistry


@pytest.fixture
def models():
    return [
        ModelMetadata(
            id="alpha",
            name="Alpha",
            provider="Provider A",
            tasks=("text-generation",),
            formats=("gguf",),
            source=ModelSource("example/alpha"),
            license="MIT",
            backends=("llama_cpp",),
            tags=("small", "local"),
        ),
        ModelMetadata(
            id="beta",
            name="Beta",
            provider="Provider B",
            tasks=("embeddings",),
            formats=("onnx",),
            source=ModelSource("example/beta"),
            license="Apache-2.0",
            backends=("onnx",),
            tags=("embedding",),
        ),
        ModelMetadata(
            id="gamma",
            name="Gamma",
            provider="Provider A",
            tasks=("text-generation", "summarization"),
            formats=("gguf",),
            source=ModelSource("example/gamma"),
            license="MIT",
            backends=("llama_cpp", "ollama"),
            tags=("large", "local"),
        ),
    ]


@pytest.fixture
def registry(models):
    return ModelRegistry(models)


def test_registry_initialization(registry):
    assert len(registry) == 3


def test_register_model(registry):
    model = ModelMetadata(
        id="delta",
        name="Delta",
        provider="Provider D",
        tasks=("classification",),
        formats=("transformers",),
        source=ModelSource("example/delta"),
        license="MIT",
        backends=("transformers",),
    )

    registry.register(model)

    assert len(registry) == 4
    assert registry.exists("delta")


def test_duplicate_registration_rejected(registry):
    with pytest.raises(ValueError):
        registry.register(registry.get("alpha"))


def test_invalid_registration_rejected():
    registry = ModelRegistry()

    with pytest.raises(TypeError):
        registry.register("not_a_model")


def test_get_model(registry):
    model = registry.get("alpha")

    assert model.name == "Alpha"


def test_get_unknown_model_rejected(registry):
    with pytest.raises(KeyError, match="not found"):
        registry.get("unknown")


def test_exists(registry):
    assert registry.exists("alpha")
    assert not registry.exists("unknown")


def test_contains(registry):
    assert "alpha" in registry
    assert "unknown" not in registry


def test_remove_model(registry):
    removed = registry.remove("alpha")

    assert removed.id == "alpha"
    assert len(registry) == 2
    assert not registry.exists("alpha")


def test_remove_unknown_model_rejected(registry):
    with pytest.raises(KeyError):
        registry.remove("unknown")


def test_list_models_sorted(registry):
    result = registry.list_models()

    assert [model.id for model in result] == [
        "alpha",
        "beta",
        "gamma",
    ]


def test_filter_by_task(registry):
    result = registry.list_models(task="text-generation")

    assert {model.id for model in result} == {
        "alpha",
        "gamma",
    }


def test_filter_by_backend(registry):
    result = registry.list_models(backend="ollama")

    assert [model.id for model in result] == ["gamma"]


def test_filter_by_format(registry):
    result = registry.list_models(model_format="onnx")

    assert [model.id for model in result] == ["beta"]


def test_filter_by_provider_case_insensitive(registry):
    result = registry.list_models(provider="provider a")

    assert {model.id for model in result} == {
        "alpha",
        "gamma",
    }


def test_filter_by_tag(registry):
    result = registry.list_models(tag="local")

    assert {model.id for model in result} == {
        "alpha",
        "gamma",
    }


def test_combined_filters(registry):
    result = registry.list_models(
        task="text-generation",
        backend="llama_cpp",
        provider="Provider A",
        tag="local",
    )

    assert {model.id for model in result} == {
        "alpha",
        "gamma",
    }


def test_empty_filter_result(registry):
    assert registry.list_models(task="unknown-task") == []


def test_registry_to_dict(registry):
    data = registry.to_dict()

    assert data["registry_version"] == 1
    assert len(data["models"]) == 3


def test_registry_from_dict(registry):
    data = registry.to_dict()

    reconstructed = ModelRegistry.from_dict(data)

    assert len(reconstructed) == 3
    assert reconstructed.get("alpha") == registry.get("alpha")


def test_invalid_registry_dict_rejected():
    with pytest.raises(ValueError):
        ModelRegistry.from_dict({"models": "invalid"})


def test_save_and_load_registry(registry, tmp_path):
    file_path = tmp_path / "catalog.json"

    registry.save(file_path)

    loaded = ModelRegistry.load(file_path)

    assert len(loaded) == 3
    assert loaded.get("gamma") == registry.get("gamma")


def test_save_creates_parent_directories(registry, tmp_path):
    file_path = tmp_path / "nested" / "deep" / "catalog.json"

    registry.save(file_path)

    assert file_path.exists()


def test_load_missing_file_rejected(tmp_path):
    file_path = tmp_path / "missing.json"

    with pytest.raises(FileNotFoundError):
        ModelRegistry.load(file_path)


def test_load_invalid_json_rejected(tmp_path):
    file_path = tmp_path / "catalog.json"
    file_path.write_text("{invalid", encoding="utf-8")

    with pytest.raises(ValueError, match="Invalid registry JSON"):
        ModelRegistry.load(file_path)


def test_save_to_directory_rejected(registry, tmp_path):
    with pytest.raises(IsADirectoryError):
        registry.save(tmp_path)


def test_load_directory_rejected(tmp_path):
    with pytest.raises(IsADirectoryError):
        ModelRegistry.load(tmp_path)