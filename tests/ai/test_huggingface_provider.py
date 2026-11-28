"""Offline tests for the Hugging Face provider."""

from types import SimpleNamespace

import pytest

from icebrew.ai.catalog.schema import (
    ModelFile,
    ModelMetadata,
    ModelRequirements,
    ModelSource,
)
from icebrew.ai.providers import (
    HuggingFaceProvider,
    ProviderError,
)


@pytest.fixture
def model():
    return ModelMetadata(
        id="hf-test",
        name="HF Test",
        provider="Hugging Face",
        tasks=("text-generation",),
        formats=("gguf",),
        source=ModelSource(
            repository="example/test-model",
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
            ModelFile(
                filename="config.json",
                sha256=None,
                size_bytes=None,
            ),
        ),
        requirements=ModelRequirements(),
        description="Test model",
        tags=("test",),
    )


def test_identifier():
    provider = HuggingFaceProvider()

    assert provider.identifier == "huggingface"


def test_validate_repository(model):
    provider = HuggingFaceProvider()

    assert provider._repository(model) == "example/test-model"


def test_validate_revision(model):
    provider = HuggingFaceProvider()

    assert provider._revision(model) == "main"


def test_validate_default_revision(model):
    model_without_revision = ModelMetadata(
        id=model.id,
        name=model.name,
        provider=model.provider,
        tasks=model.tasks,
        formats=model.formats,
        source=ModelSource(
            repository="example/test-model",
            revision=None,
        ),
        license=model.license,
        backends=model.backends,
        files=model.files,
        requirements=model.requirements,
        description=model.description,
        tags=model.tags,
    )

    provider = HuggingFaceProvider()

    assert provider._revision(model_without_revision) == "main"


def test_validate_declared_file(model):
    provider = HuggingFaceProvider()

    provider._validate_declared_file(
        model,
        "model.gguf",
    )


def test_undeclared_file(model):
    provider = HuggingFaceProvider()

    with pytest.raises(ProviderError):
        provider.resolve(model, "unknown.gguf")


def test_unsafe_filename(model):
    provider = HuggingFaceProvider()

    with pytest.raises(ProviderError):
        provider._validate_declared_file(
            model,
            "../model.gguf",
        )


def test_nested_declared_filename(model):
    nested_model = ModelMetadata(
        id=model.id,
        name=model.name,
        provider=model.provider,
        tasks=model.tasks,
        formats=model.formats,
        source=model.source,
        license=model.license,
        backends=model.backends,
        files=(
            ModelFile(
                filename="weights/model.gguf",
                sha256=None,
                size_bytes=None,
            ),
        ),
        requirements=model.requirements,
        description=model.description,
        tags=model.tags,
    )

    provider = HuggingFaceProvider()

    provider._validate_declared_file(
        nested_model,
        "weights/model.gguf",
    )


def test_validate_url():
    HuggingFaceProvider._validate_url(
        "https://huggingface.co/example/model/resolve/main/model.gguf"
    )


@pytest.mark.parametrize(
    "url",
    [
        "ftp://example.com/model",
        "not-a-url",
        "https:///invalid",
    ],
)
def test_invalid_url(url):
    with pytest.raises(ProviderError):
        HuggingFaceProvider._validate_url(url)


def test_repository_info_mock(model, monkeypatch):
    provider = HuggingFaceProvider()

    expected = SimpleNamespace(
        siblings=[
            SimpleNamespace(rfilename="model.gguf"),
            SimpleNamespace(rfilename="config.json"),
        ]
    )

    class FakeAPI:
        def model_info(
            self,
            repo_id,
            revision,
            files_metadata,
        ):
            assert repo_id == "example/test-model"
            assert revision == "main"
            assert files_metadata is True

            return expected

    monkeypatch.setattr(
        provider,
        "_get_api",
        lambda: FakeAPI(),
    )

    assert provider.repository_info(model) is expected


def test_list_files_mock(model, monkeypatch):
    provider = HuggingFaceProvider()

    class FakeAPI:
        def model_info(
            self,
            repo_id,
            revision,
            files_metadata,
        ):
            return SimpleNamespace(
                siblings=[
                    SimpleNamespace(rfilename="z.gguf"),
                    SimpleNamespace(rfilename="config.json"),
                    SimpleNamespace(rfilename="a.gguf"),
                    SimpleNamespace(rfilename="config.json"),
                ]
            )

    monkeypatch.setattr(
        provider,
        "_get_api",
        lambda: FakeAPI(),
    )

    result = provider.list_files(model)

    assert result == [
        "a.gguf",
        "config.json",
        "z.gguf",
    ]


def test_repository_info_error(model, monkeypatch):
    provider = HuggingFaceProvider()

    class FakeAPI:
        def model_info(self, **kwargs):
            raise RuntimeError("connection failed")

    monkeypatch.setattr(
        provider,
        "_get_api",
        lambda: FakeAPI(),
    )

    with pytest.raises(ProviderError, match="Unable to retrieve"):
        provider.repository_info(model)


def test_missing_siblings(model, monkeypatch):
    provider = HuggingFaceProvider()

    class FakeAPI:
        def model_info(self, **kwargs):
            return SimpleNamespace()

    monkeypatch.setattr(
        provider,
        "_get_api",
        lambda: FakeAPI(),
    )

    with pytest.raises(ProviderError):
        provider.list_files(model)


def test_create_url_resolver(model, monkeypatch):
    provider = HuggingFaceProvider()

    monkeypatch.setattr(
        provider,
        "resolve",
        lambda model, filename:
            f"https://example.com/{filename}",
    )

    resolver = provider.create_url_resolver(model)

    assert resolver("model.gguf") == (
        "https://example.com/model.gguf"
    )


def test_token_is_preserved():
    provider = HuggingFaceProvider(token="test-token")

    assert provider.token == "test-token"