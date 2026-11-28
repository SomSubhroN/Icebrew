
"""Hugging Face Hub model provider."""

from __future__ import annotations

from urllib.parse import urlparse

from icebrew.ai.catalog.schema import ModelMetadata
from icebrew.ai.providers.base import ProviderError, SourceProvider
from icebrew.ai.providers.discovery import DiscoveredModel


class HuggingFaceProvider(SourceProvider):
    """Resolve, inspect, and discover model repositories on Hugging Face."""

    def __init__(self, *, token: str | None = None):
        self.token = token

    @property
    def identifier(self) -> str:
        return "huggingface"

    def _get_api(self):
        """Create the Hugging Face API client."""
        try:
            from huggingface_hub import HfApi
        except ImportError as exc:
            raise ProviderError(
                "Hugging Face integration requires the optional "
                "dependency 'huggingface_hub'. Install it with "
                "`pip install icebrew[huggingface]`."
            ) from exc

        return HfApi(token=self.token)

    @staticmethod
    def _repository(model: ModelMetadata) -> str:
        """Extract and validate the repository identifier."""
        repository = getattr(model.source, "repository", None)

        if not isinstance(repository, str) or not repository.strip():
            raise ProviderError(
                f"Model '{model.id}' has no valid repository identifier."
            )

        return repository.strip()

    @staticmethod
    def _revision(model: ModelMetadata) -> str:
        """Return the requested revision or the default branch."""
        revision = getattr(model.source, "revision", None)
        return revision or "main"

    def repository_info(self, model: ModelMetadata):
        """Retrieve repository metadata from the Hub."""
        api = self._get_api()
        repository = self._repository(model)
        revision = self._revision(model)

        try:
            return api.model_info(
                repo_id=repository,
                revision=revision,
                files_metadata=True,
            )
        except Exception as exc:
            raise ProviderError(
                f"Unable to retrieve Hugging Face repository "
                f"'{repository}' at revision '{revision}': {exc}"
            ) from exc

    def list_files(self, model: ModelMetadata) -> list[str]:
        """Return the repository's file names."""
        info = self.repository_info(model)
        siblings = getattr(info, "siblings", None)

        if siblings is None:
            raise ProviderError(
                "Hugging Face repository response contained "
                "no file listing."
            )

        files = []

        for sibling in siblings:
            filename = getattr(sibling, "rfilename", None)

            if isinstance(filename, str) and filename:
                files.append(filename)

        return sorted(set(files))

    def resolve(self, model: ModelMetadata, filename: str) -> str:
        """Resolve a declared file into a Hugging Face download URL."""
        self._validate_declared_file(model, filename)

        repository = self._repository(model)
        revision = self._revision(model)

        try:
            from huggingface_hub import hf_hub_url
        except ImportError as exc:
            raise ProviderError(
                "Hugging Face integration requires the optional "
                "dependency 'huggingface_hub'. Install it with "
                "`pip install icebrew[huggingface]`."
            ) from exc

        try:
            url = hf_hub_url(
                repo_id=repository,
                filename=filename,
                revision=revision,
            )
        except Exception as exc:
            raise ProviderError(
                f"Unable to resolve '{filename}' from "
                f"'{repository}' at revision '{revision}': {exc}"
            ) from exc

        self._validate_url(url)
        return url

    def create_url_resolver(self, model: ModelMetadata):
        """Create a filename-to-URL callback."""

        def resolve_filename(filename: str) -> str:
            return self.resolve(model, filename)

        return resolve_filename

    def discover(
        self,
        *,
        query: str | None = None,
        task: str | None = None,
        library: str | None = None,
        limit: int = 20,
        sort: str = "downloads",
        direction: int = -1,
    ) -> list[DiscoveredModel]:
        """Search Hugging Face model repositories.

        Returns normalized discovery metadata without downloading
        model weights or registering repositories automatically.
        """

        if isinstance(limit, bool) or not isinstance(limit, int):
            raise ValueError("limit must be an integer")

        if limit < 1:
            raise ValueError("limit must be at least 1")

        allowed_sorts = {
            "downloads",
            "likes",
            "lastModified",
        }

        if sort not in allowed_sorts:
            raise ValueError(
                f"Unsupported sort value: {sort}. "
                f"Choose from {sorted(allowed_sorts)}."
            )

        if isinstance(direction, bool) or direction not in {-1, 1}:
            raise ValueError("direction must be -1 or 1")

        if query is not None and not isinstance(query, str):
            raise ValueError("query must be a string or None")

        if task is not None and not isinstance(task, str):
            raise ValueError("task must be a string or None")

        if library is not None and not isinstance(library, str):
            raise ValueError("library must be a string or None")

        api = self._get_api()

        kwargs = {
            "search": query,
            "filter": task,
            "sort": sort,
            "direction": direction,
            "limit": limit,
        }

        try:
            results = api.list_models(**kwargs)
        except Exception as exc:
            raise ProviderError(
                f"Hugging Face model discovery failed: {exc}"
            ) from exc

        discovered: list[DiscoveredModel] = []

        for item in results:
            repository = getattr(item, "id", None)

            if not isinstance(repository, str) or not repository:
                continue

            library_name = getattr(item, "library_name", None)

            # Library filtering is performed locally to avoid
            # relying on provider-specific API arguments.
            if library and (
                not isinstance(library_name, str)
                or library_name.casefold() != library.casefold()
            ):
                continue

            tags = getattr(item, "tags", None) or ()

            discovered.append(
                DiscoveredModel(
                    repository=repository,
                    pipeline_tag=getattr(item, "pipeline_tag", None),
                    library_name=library_name,
                    downloads=getattr(item, "downloads", None),
                    likes=getattr(item, "likes", None),
                    tags=tuple(
                        tag for tag in tags
                        if isinstance(tag, str)
                    ),
                    description=None,
                )
            )

        return discovered

    @staticmethod
    def _validate_declared_file(
        model: ModelMetadata,
        filename: str,
    ) -> None:
        """Ensure the requested file belongs to the model metadata."""
        if not isinstance(filename, str) or not filename:
            raise ProviderError(
                "Filename must be a non-empty string."
            )

        declared = {
            file.filename for file in model.files
        }

        if filename not in declared:
            raise ProviderError(
                f"File '{filename}' is not declared in model "
                f"metadata for '{model.id}'."
            )

        if (
            filename in {".", ".."}
            or "\\" in filename
            or "\x00" in filename
        ):
            raise ProviderError(
                f"Unsafe model filename: {filename}"
            )

    @staticmethod
    def _validate_url(url: str) -> None:
        """Validate a resolved HTTP(S) URL."""
        parsed = urlparse(url)

        if parsed.scheme not in {"http", "https"}:
            raise ProviderError(
                "Hugging Face resolved an unsupported URL scheme."
            )

        if not parsed.netloc:
            raise ProviderError(
                "Hugging Face resolved an invalid URL."
            )
