# tests/ai/test_backends.py

from pathlib import Path

import pytest

from icebrew.ai.backends.base import ModelBackend
from icebrew.ai.backends.manager import BackendManager
from icebrew.ai.catalog.schema import ModelMetadata, ModelSource


class MockBackend(ModelBackend):

    def __init__(
        self,
        identifier="mock",
        formats=("gguf",),
        tasks=("text-generation",),
        available=True,
    ):
        self._identifier = identifier
        self._formats = formats
        self._tasks = tasks
        self._available = available
        self.loaded_path = None

    @property
    def identifier(self):
        return self._identifier

    @property
    def supported_formats(self):
        return self._formats

    @property
    def supported_tasks(self):
        return self._tasks

    def is_available(self):
        return self._available

    def health_check(self):
        return {
            "backend": self.identifier,
            "available": self.is_available(),
        }

    def load(self, model_path, **kwargs):
        self.loaded_path = Path(model_path)
        return self.loaded_path

    def generate(self, prompt, **kwargs):
        return f"Generated: {prompt}"

    def unload(self):
        self.loaded_path = None


class IncompleteBackend:
    pass


@pytest.fixture
def model():
    return ModelMetadata(
        id="test-model",
        name="Test Model",
        provider="Test",
        tasks=("text-generation",),
        formats=("gguf",),
        source=ModelSource("example/test-model"),
        license="MIT",
        backends=("mock", "mock-alt"),
    )


@pytest.fixture
def manager():
    return BackendManager(
        [
            MockBackend("mock"),
            MockBackend("mock-alt"),
        ]
    )


def test_backend_contract():
    backend = MockBackend()

    assert backend.identifier == "mock"
    assert backend.supported_formats == ("gguf",)
    assert backend.supported_tasks == ("text-generation",)
    assert backend.is_available()


def test_backend_health_check():
    backend = MockBackend()

    report = backend.health_check()

    assert report["backend"] == "mock"
    assert report["available"] is True


def test_backend_load():
    backend = MockBackend()

    result = backend.load("model.gguf")

    assert result == Path("model.gguf")
    assert backend.loaded_path == Path("model.gguf")


def test_backend_generate():
    backend = MockBackend()

    assert backend.generate("hello") == "Generated: hello"


def test_backend_unload():
    backend = MockBackend()

    backend.load("model.gguf")
    backend.unload()

    assert backend.loaded_path is None


def test_manager_initialization(manager):
    assert len(manager) == 2


def test_register_backend():
    manager = BackendManager()
    backend = MockBackend("test")

    manager.register(backend)

    assert manager.get("test") is backend


def test_register_duplicate_backend_rejected(manager):
    with pytest.raises(ValueError):
        manager.register(MockBackend("mock"))


def test_register_invalid_backend_rejected():
    manager = BackendManager()

    with pytest.raises(TypeError):
        manager.register(IncompleteBackend())


def test_get_backend(manager):
    assert manager.get("mock").identifier == "mock"


def test_get_unknown_backend_rejected(manager):
    with pytest.raises(KeyError):
        manager.get("unknown")


def test_exists(manager):
    assert manager.exists("mock")
    assert not manager.exists("unknown")


def test_contains(manager):
    assert "mock" in manager
    assert "unknown" not in manager


def test_remove_backend(manager):
    removed = manager.remove("mock")

    assert removed.identifier == "mock"
    assert not manager.exists("mock")


def test_remove_unknown_backend_rejected(manager):
    with pytest.raises(KeyError):
        manager.remove("unknown")


def test_list_backends_sorted(manager):
    backends = manager.list_backends()

    assert [backend.identifier for backend in backends] == [
        "mock",
        "mock-alt",
    ]


def test_list_available_backends():
    manager = BackendManager(
        [
            MockBackend("available", available=True),
            MockBackend("unavailable", available=False),
        ]
    )

    backends = manager.list_backends(available_only=True)

    assert [backend.identifier for backend in backends] == [
        "available",
    ]


def test_compatible_backends(manager, model):
    result = manager.compatible_backends(model)

    assert {backend.identifier for backend in result} == {
        "mock",
        "mock-alt",
    }


def test_compatible_backends_available_only(model):
    manager = BackendManager(
        [
            MockBackend("mock", available=True),
            MockBackend("mock-alt", available=False),
        ]
    )

    result = manager.compatible_backends(
        model,
        available_only=True,
    )

    assert [backend.identifier for backend in result] == [
        "mock",
    ]


def test_resolve_backend(manager, model):
    backend = manager.resolve(model)

    assert backend.identifier == "mock"


def test_resolve_preferred_backend(manager, model):
    backend = manager.resolve(
        model,
        preferred="mock-alt",
    )

    assert backend.identifier == "mock-alt"


def test_resolve_unregistered_preferred_backend(manager, model):
    with pytest.raises(KeyError):
        manager.resolve(
            model,
            preferred="unknown",
        )


def test_resolve_incompatible_backend():
    manager = BackendManager(
        [
            MockBackend(
                "mock",
                formats=("onnx",),
            )
        ]
    )

    model = ModelMetadata(
        id="test",
        name="Test",
        provider="Test",
        tasks=("text-generation",),
        formats=("gguf",),
        source=ModelSource("example/test"),
        license="MIT",
        backends=("mock",),
    )

    with pytest.raises(ValueError, match="format"):
        manager.resolve(model, preferred="mock")


def test_resolve_incompatible_task():
    manager = BackendManager(
        [
            MockBackend(
                "mock",
                tasks=("embeddings",),
            )
        ]
    )

    model = ModelMetadata(
        id="test",
        name="Test",
        provider="Test",
        tasks=("text-generation",),
        formats=("gguf",),
        source=ModelSource("example/test"),
        license="MIT",
        backends=("mock",),
    )

    with pytest.raises(ValueError, match="task"):
        manager.resolve(model, preferred="mock")


def test_resolve_unavailable_backend():
    manager = BackendManager(
        [
            MockBackend(
                "mock",
                available=False,
            )
        ]
    )

    with pytest.raises(RuntimeError, match="not available"):
        manager.resolve(
            ModelMetadata(
                id="test",
                name="Test",
                provider="Test",
                tasks=("text-generation",),
                formats=("gguf",),
                source=ModelSource("example/test"),
                license="MIT",
                backends=("mock",),
            ),
            preferred="mock",
        )


def test_resolve_without_available_requirement():
    manager = BackendManager(
        [
            MockBackend(
                "mock",
                available=False,
            )
        ]
    )

    model = ModelMetadata(
        id="test",
        name="Test",
        provider="Test",
        tasks=("text-generation",),
        formats=("gguf",),
        source=ModelSource("example/test"),
        license="MIT",
        backends=("mock",),
    )

    backend = manager.resolve(
        model,
        require_available=False,
    )

    assert backend.identifier == "mock"


def test_resolve_no_compatible_backend(model):
    manager = BackendManager(
        [
            MockBackend(
                "other",
                formats=("onnx",),
                tasks=("embeddings",),
            )
        ]
    )

    with pytest.raises(LookupError):
        manager.resolve(
            model,
            require_available=False,
        )


def test_resolve_no_available_compatible_backend(model):
    manager = BackendManager(
        [
            MockBackend(
                "mock",
                available=False,
            )
        ]
    )

    with pytest.raises(RuntimeError):
        manager.resolve(model)


def test_backend_identifier_validation():
    with pytest.raises(ValueError):
        BackendManager(
            [
                MockBackend(identifier=""),
            ]
        )