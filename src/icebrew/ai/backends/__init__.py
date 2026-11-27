# src/icebrew/ai/backends/__init__.py

from icebrew.ai.backends.base import ModelBackend
from icebrew.ai.backends.manager import BackendManager

__all__ = [
    "ModelBackend",
    "BackendManager",
]