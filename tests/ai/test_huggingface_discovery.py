"""Offline tests for Hugging Face discovery."""

from types import SimpleNamespace

import pytest

from icebrew.ai.providers import (
    DiscoveredModel,
    HuggingFaceProvider,
    ProviderError,
)


@pytest.fixture
def provider():
    return HuggingFaceProvider()


@pytest.fixture
def fake_models():
    return [
        SimpleNamespace(
            id="org/model-a",
            pipeline_tag="text-generation",
            library_name="transformers",
            downloads=1000,
            likes=50,
            tags=["llm", "text-generation"],
        ),
        SimpleNamespace(
            id="org/model-b",
            pipeline_tag="sentence-similarity",
            library_name="sentence-transformers",
            downloads=500,
            likes=20,
            tags=["embedding"],
        ),
        SimpleNamespace(
            id="org/model-c",
            pipeline_tag="text-generation",
            library_name="transformers",
            downloads=200,
            likes=10,
            tags=["llm"],
        ),
    ]


def test_discovery_normalization(provider, fake_models, monkeypatch):
    class FakeAPI:
        def list_models(self, **kwargs):
            return fake_models

    monkeypatch.setattr(
        provider,
        "_get_api",
        lambda: FakeAPI(),
    )

    results = provider.discover()

    assert len(results) == 3
    assert isinstance(results[0], DiscoveredModel)
    assert results[0].repository == "org/model-a"
    assert results[0].downloads == 1000
    assert results[0].likes == 50


def test_discovery_query_arguments(provider, fake_models, monkeypatch):
    captured = {}

    class FakeAPI:
        def list_models(self, **kwargs):
            captured.update(kwargs)
            return fake_models

    monkeypatch.setattr(
        provider,
        "_get_api",
        lambda: FakeAPI(),
    )

    provider.discover(
        query="small language model",
        task="text-generation",
        limit=5,
        sort="likes",
        direction=-1,
    )

    assert captured["search"] == "small language model"
    assert captured["filter"] == "text-generation"
    assert captured["limit"] == 5
    assert captured["sort"] == "likes"
    assert captured["direction"] == -1


def test_discovery_library_filter(
    provider,
    fake_models,
    monkeypatch,
):
    class FakeAPI:
        def list_models(self, **kwargs):
            return fake_models

    monkeypatch.setattr(
        provider,
        "_get_api",
        lambda: FakeAPI(),
    )

    results = provider.discover(
        library="transformers",
    )

    assert [item.repository for item in results] == [
        "org/model-a",
        "org/model-c",
    ]


def test_discovery_library_filter_case_insensitive(
    provider,
    fake_models,
    monkeypatch,
):
    class FakeAPI:
        def list_models(self, **kwargs):
            return fake_models

    monkeypatch.setattr(
        provider,
        "_get_api",
        lambda: FakeAPI(),
    )

    results = provider.discover(
        library="TRANSFORMERS",
    )

    assert len(results) == 2


def test_discovery_empty_result(provider, monkeypatch):
    class FakeAPI:
        def list_models(self, **kwargs):
            return []

    monkeypatch.setattr(
        provider,
        "_get_api",
        lambda: FakeAPI(),
    )

    assert provider.discover() == []


def test_discovery_missing_ids(provider, monkeypatch):
    class FakeAPI:
        def list_models(self, **kwargs):
            return [
                SimpleNamespace(id=None),
                SimpleNamespace(id="valid/model"),
            ]

    monkeypatch.setattr(
        provider,
        "_get_api",
        lambda: FakeAPI(),
    )

    results = provider.discover()

    assert [item.repository for item in results] == [
        "valid/model",
    ]


def test_discovery_missing_tags(provider, monkeypatch):
    class FakeAPI:
        def list_models(self, **kwargs):
            return [
                SimpleNamespace(
                    id="test/model",
                    tags=None,
                ),
            ]

    monkeypatch.setattr(
        provider,
        "_get_api",
        lambda: FakeAPI(),
    )

    results = provider.discover()

    assert results[0].tags == ()


def test_discovery_api_error(provider, monkeypatch):
    class FakeAPI:
        def list_models(self, **kwargs):
            raise RuntimeError("network error")

    monkeypatch.setattr(
        provider,
        "_get_api",
        lambda: FakeAPI(),
    )

    with pytest.raises(ProviderError, match="discovery failed"):
        provider.discover()


@pytest.mark.parametrize(
    "limit",
    [
        0,
        -1,
        True,
        1.5,
        "10",
    ],
)
def test_invalid_limit(provider, limit):
    with pytest.raises(ValueError):
        provider.discover(limit=limit)


@pytest.mark.parametrize(
    "sort",
    [
        "invalid",
        "",
    ],
)
def test_invalid_sort(provider, sort):
    with pytest.raises(ValueError):
        provider.discover(sort=sort)


@pytest.mark.parametrize(
    "direction",
    [
        0,
        2,
        -2,
        True,
    ],
)
def test_invalid_direction(provider, direction):
    with pytest.raises(ValueError):
        provider.discover(direction=direction)


def test_discovered_model_to_dict():
    model = DiscoveredModel(
        repository="org/model",
        pipeline_tag="text-generation",
        library_name="transformers",
        downloads=100,
        likes=10,
        tags=("llm", "test"),
        description=None,
    )

    result = model.to_dict()

    assert result["repository"] == "org/model"
    assert result["pipeline_tag"] == "text-generation"
    assert result["tags"] == ["llm", "test"]