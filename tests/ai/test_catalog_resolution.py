"""Tests for model catalog and generic source resolution."""

import pytest

from icebrew.ai.catalog import (
    CatalogError,
    ModelCatalog,
    ModelFile,
    ModelMetadata,
    ModelRequirements,
    ModelSource,
    SourceResolutionError,
    SourceResolver,
)


@pytest.fixture
def model():
    return ModelMetadata(
        id="test-model",
        name="Test Model",
        provider="TestProvider",
        tasks=("text-generation",),
        formats=("gguf",),
        source=ModelSource(
            repository="test/repository",
            revision="main",
        ),
        license="MIT",
        backends=("llama.cpp",),
        files=(
            ModelFile(
                filename="model.gguf",
                sha256=None,
                size_bytes=None,
            ),
        ),
        requirements=ModelRequirements(),
        description="A test model",
        tags=("test", "small"),
    )


@pytest.fixture
def second_model():
    return ModelMetadata(
        id="second-model",
        name="Second Model",
        provider="AnotherProvider",
        tasks=("embeddings",),
        formats=("onnx",),
        source=ModelSource(
            repository="direct/onnx",
            url="https://example.com/model.onnx",
        ),
        license="MIT",
        backends=("onnxruntime",),
        files=(
            ModelFile(
                filename="model.onnx",
                sha256=None,
                size_bytes=None,
            ),
        ),
        requirements=ModelRequirements(),
        description="Another test model",
        tags=("embedding",),
    )


# ---------------------------------------------------------------------
# Catalog
# ---------------------------------------------------------------------

def test_catalog_register_and_get(model):
    catalog = ModelCatalog()
    catalog.register(model)

    assert catalog.get(model.id) == model
    assert catalog.exists(model.id)
    assert model.id in catalog


def test_catalog_duplicate_registration(model):
    catalog = ModelCatalog([model])

    with pytest.raises(CatalogError):
        catalog.register(model)


def test_catalog_unknown_model():
    catalog = ModelCatalog()

    with pytest.raises(CatalogError):
        catalog.get("missing")


def test_catalog_remove(model):
    catalog = ModelCatalog([model])

    removed = catalog.remove(model.id)

    assert removed == model
    assert not catalog.exists(model.id)


def test_catalog_filter_by_task(model, second_model):
    catalog = ModelCatalog([model, second_model])

    result = catalog.list_models(task="text-generation")

    assert [item.id for item in result] == [model.id]


def test_catalog_filter_by_backend(model, second_model):
    catalog = ModelCatalog([model, second_model])

    result = catalog.list_models(backend="llama.cpp")

    assert [item.id for item in result] == [model.id]


def test_catalog_filter_by_format(model, second_model):
    catalog = ModelCatalog([model, second_model])

    result = catalog.list_models(model_format="onnx")

    assert [item.id for item in result] == [second_model.id]


def test_catalog_filter_by_provider_case_insensitive(
    model,
    second_model,
):
    catalog = ModelCatalog([model, second_model])

    result = catalog.list_models(provider="testprovider")

    assert [item.id for item in result] == [model.id]


def test_catalog_filter_by_tag(model, second_model):
    catalog = ModelCatalog([model, second_model])

    result = catalog.list_models(tag="SMALL")

    assert [item.id for item in result] == [model.id]


def test_catalog_search(model, second_model):
    catalog = ModelCatalog([model, second_model])

    result = catalog.list_models(query="TestProvider")

    assert [item.id for item in result] == [model.id]


def test_catalog_sorted(model, second_model):
    catalog = ModelCatalog([second_model, model])

    result = catalog.list_models()

    assert [item.id for item in result] == sorted(
        [model.id, second_model.id],
        key=str.casefold,
    )


def test_catalog_serialization(model, second_model):
    catalog = ModelCatalog([model, second_model])

    restored = ModelCatalog.from_dict(catalog.to_dict())

    assert len(restored) == 2
    assert restored.get(model.id) == model
    assert restored.get(second_model.id) == second_model


def test_catalog_from_invalid_data():
    with pytest.raises(TypeError):
        ModelCatalog.from_dict([])


# ---------------------------------------------------------------------
# Source resolution
# ---------------------------------------------------------------------

def test_resolve_single_file_direct_url(second_model):
    resolver = SourceResolver()

    url = resolver.resolve(
        second_model,
        "model.onnx",
    )

    assert url == "https://example.com/model.onnx"


def test_resolve_url_template(model):
    templated_model = ModelMetadata(
        id=model.id,
        name=model.name,
        provider=model.provider,
        tasks=model.tasks,
        formats=model.formats,
        source=ModelSource(
            repository="direct/template",
            url="https://example.com/models/{filename}",
        ),
        license=model.license,
        backends=model.backends,
        files=model.files,
        requirements=model.requirements,
        description=model.description,
        tags=model.tags,
    )

    resolver = SourceResolver()

    url = resolver.resolve(
        templated_model,
        "model.gguf",
    )

    assert url == "https://example.com/models/model.gguf"


def test_resolve_url_template_encodes_filename(model):
    file_model = ModelMetadata(
        id=model.id,
        name=model.name,
        provider=model.provider,
        tasks=model.tasks,
        formats=model.formats,
        source=ModelSource(
            repository="direct/template",
            url="https://example.com/{filename}",
        ),
        license=model.license,
        backends=model.backends,
        files=(
            ModelFile(
                filename="model file.gguf",
                sha256=None,
                size_bytes=None,
            ),
        ),
        requirements=model.requirements,
        description=model.description,
        tags=model.tags,
    )

    resolver = SourceResolver()

    url = resolver.resolve(
        file_model,
        "model file.gguf",
    )

    assert url == "https://example.com/model%20file.gguf"


def test_resolve_requires_registered_provider_for_repository(
    model,
):
    resolver = SourceResolver()

    with pytest.raises(SourceResolutionError):
        resolver.resolve(model, "model.gguf")


def test_registered_provider(model):
    resolver = SourceResolver()

    resolver.register(
        "test",
        lambda model, filename:
            f"https://provider.example/{model.id}/{filename}",
    )

    url = resolver.resolve(
        model,
        "model.gguf",
        provider="TEST",
    )

    assert url == (
        "https://provider.example/test-model/model.gguf"
    )


def test_duplicate_provider_registration(model):
    resolver = SourceResolver()

    handler = lambda model, filename: (
        f"https://example.com/{filename}"
    )

    resolver.register("test", handler)

    with pytest.raises(SourceResolutionError):
        resolver.register("test", handler)


def test_replace_provider_registration(model):
    resolver = SourceResolver()

    resolver.register(
        "test",
        lambda model, filename:
            f"https://old.example/{filename}",
    )

    resolver.register(
        "test",
        lambda model, filename:
            f"https://new.example/{filename}",
        replace=True,
    )

    assert resolver.resolve(
        model,
        "model.gguf",
        provider="test",
    ).startswith("https://new.example/")


def test_unregister_provider(model):
    resolver = SourceResolver()

    handler = lambda model, filename: (
        f"https://example.com/{filename}"
    )

    resolver.register("test", handler)

    removed = resolver.unregister("test")

    assert removed is handler
    assert "test" not in resolver.providers()


def test_unknown_provider(model):
    resolver = SourceResolver()

    with pytest.raises(SourceResolutionError):
        resolver.resolve(
            model,
            "model.gguf",
            provider="missing",
        )


def test_filename_must_be_declared(model):
    resolver = SourceResolver()

    with pytest.raises(SourceResolutionError):
        resolver.resolve(model, "unknown.gguf")


@pytest.mark.parametrize(
    "filename",
    [
        "../model.gguf",
        "folder/model.gguf",
        "folder\\model.gguf",
        ".",
        "..",
    ],
)
def test_unsafe_filename(model, filename):
    resolver = SourceResolver()

    with pytest.raises(SourceResolutionError):
        resolver.resolve(model, filename)


def test_invalid_handler_url(model):
    resolver = SourceResolver()

    resolver.register(
        "test",
        lambda model, filename: "ftp://example.com/model",
    )

    with pytest.raises(SourceResolutionError):
        resolver.resolve(
            model,
            "model.gguf",
            provider="test",
        )


def test_create_url_resolver(model):
    resolver = SourceResolver()

    resolver.register(
        "test",
        lambda model, filename:
            f"https://example.com/{model.id}/{filename}",
    )

    callback = resolver.create_url_resolver(
        model,
        provider="test",
    )

    assert callback("model.gguf") == (
        "https://example.com/test-model/model.gguf"
    )


def test_provider_listing(model):
    resolver = SourceResolver()

    resolver.register(
        "z-provider",
        lambda model, filename:
            f"https://example.com/{filename}",
    )

    resolver.register(
        "a-provider",
        lambda model, filename:
            f"https://example.com/{filename}",
    )

    assert resolver.providers() == [
        "a-provider",
        "z-provider",
    ]