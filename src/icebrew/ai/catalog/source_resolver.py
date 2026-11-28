"""Generic model source URL resolution."""

from __future__ import annotations

from collections.abc import Callable
from urllib.parse import quote

from icebrew.ai.catalog.schema import ModelMetadata


class SourceResolutionError(ValueError):
    """Raised when a model source cannot be resolved."""


SourceHandler = Callable[[ModelMetadata, str], str]


class SourceResolver:
    """Resolve model files to URLs using registered source handlers."""

    def __init__(self) -> None:
        self._handlers: dict[str, SourceHandler] = {}

    def register(
        self,
        provider: str,
        handler: SourceHandler,
        *,
        replace: bool = False,
    ) -> None:
        if not isinstance(provider, str) or not provider.strip():
            raise ValueError("provider must be a non-empty string")

        if not callable(handler):
            raise TypeError("handler must be callable")

        key = provider.strip().casefold()

        if key in self._handlers and not replace:
            raise SourceResolutionError(
                f"Source provider already registered: {provider}"
            )

        self._handlers[key] = handler

    def unregister(self, provider: str) -> SourceHandler:
        key = provider.strip().casefold()

        try:
            return self._handlers.pop(key)
        except KeyError as exc:
            raise SourceResolutionError(
                f"Unknown source provider: {provider}"
            ) from exc

    def providers(self) -> list[str]:
        return sorted(self._handlers)

    def resolve(
        self,
        model: ModelMetadata,
        filename: str,
        *,
        provider: str | None = None,
    ) -> str:
        self._validate_filename(model, filename)

        if provider is not None:
            key = provider.strip().casefold()

            if key not in self._handlers:
                raise SourceResolutionError(
                    f"Unknown source provider: {provider}"
                )

            url = self._handlers[key](model, filename)
            return self._validate_url(url)

        # Generic explicit URL source.
        source_url = getattr(model.source, "url", None)

        if source_url:
            if "{filename}" in source_url:
                url = source_url.replace(
                    "{filename}",
                    quote(filename, safe=""),
                )
            elif len(model.files) == 1:
                url = source_url
            else:
                raise SourceResolutionError(
                    "A direct URL source with multiple files must use "
                    "a {filename} URL template or a registered provider."
                )

            return self._validate_url(url)

        # Generic repository sources require a registered provider.
        repository = getattr(model.source, "repository", None)

        if repository:
            raise SourceResolutionError(
                f"Model source references repository '{repository}', "
                "but no provider has been specified or registered for "
                "this source."
            )

        raise SourceResolutionError(
            f"Model '{model.id}' has no resolvable source."
        )

    def create_url_resolver(
        self,
        model: ModelMetadata,
        *,
        provider: str | None = None,
    ) -> Callable[[str], str]:
        """Create the filename-to-URL callback used by downloads."""

        def resolve_filename(filename: str) -> str:
            return self.resolve(
                model,
                filename,
                provider=provider,
            )

        return resolve_filename

    @staticmethod
    def _validate_filename(
        model: ModelMetadata,
        filename: str,
    ) -> None:
        if not isinstance(filename, str) or not filename:
            raise SourceResolutionError(
                "Filename must be a non-empty string."
            )

        declared_files = {
            item.filename for item in model.files
        }

        if filename not in declared_files:
            raise SourceResolutionError(
                f"File '{filename}' is not declared for model "
                f"'{model.id}'."
            )

        if (
            filename in {".", ".."}
            or "/" in filename
            or "\\" in filename
            or "\x00" in filename
        ):
            raise SourceResolutionError(
                f"Unsafe filename: {filename}"
            )

    @staticmethod
    def _validate_url(url: str) -> str:
        if not isinstance(url, str) or not url.strip():
            raise SourceResolutionError(
                "Source handler returned an empty URL."
            )

        if not url.startswith(("https://", "http://")):
            raise SourceResolutionError(
                "Resolved source URL must use HTTP or HTTPS."
            )

        return url