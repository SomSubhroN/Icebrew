from __future__ import annotations

import hashlib
import os
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from icebrew.ai.catalog.schema import ModelFile, ModelMetadata


ProgressCallback = Callable[[str, int, int | None], None]
CancelCallback = Callable[[], bool]
URLResolver = Callable[[ModelMetadata, ModelFile], str]


class DownloadError(RuntimeError):
    """Base exception for model download failures."""


class DownloadCancelled(DownloadError):
    """Raised when a download is cancelled by the caller."""


class DownloadIntegrityError(DownloadError):
    """Raised when a downloaded file fails integrity verification."""


class DownloadExistsError(DownloadError):
    """Raised when a destination already exists and overwrite is disabled."""


@dataclass(frozen=True)
class DownloadResult:
    url: str
    destination: Path
    size_bytes: int
    sha256: str
    resumed: bool
    already_exists: bool = False


class DownloadManager:
    """Explicit, integrity-checked model download manager."""

    def __init__(
        self,
        *,
        chunk_size: int = 1024 * 1024,
        timeout: float = 30.0,
        user_agent: str = "Icebrew/0.1",
    ) -> None:
        if isinstance(chunk_size, bool) or not isinstance(chunk_size, int):
            raise TypeError("chunk_size must be an integer.")
        if chunk_size <= 0:
            raise ValueError("chunk_size must be greater than zero.")
        if timeout <= 0:
            raise ValueError("timeout must be greater than zero.")

        self.chunk_size = chunk_size
        self.timeout = timeout
        self.user_agent = user_agent

    @staticmethod
    def _hash_file(path: Path) -> str:
        digest = hashlib.sha256()

        with path.open("rb") as handle:
            while chunk := handle.read(1024 * 1024):
                digest.update(chunk)

        return digest.hexdigest()

    @staticmethod
    def _validate_existing(
        path: Path,
        *,
        expected_sha256: str | None,
        expected_size: int | None,
    ) -> bool:
        if not path.exists():
            return False

        if not path.is_file():
            raise DownloadExistsError(
                f"Destination exists and is not a file: {path}"
            )

        size = path.stat().st_size

        if expected_size is not None and size != expected_size:
            return False

        if expected_sha256 is not None:
            actual_hash = DownloadManager._hash_file(path)
            if actual_hash.lower() != expected_sha256.lower():
                return False

        return True

    def download_file(
        self,
        url: str,
        destination: str | Path,
        *,
        expected_sha256: str | None = None,
        expected_size: int | None = None,
        overwrite: bool = False,
        resume: bool = True,
        progress_callback: ProgressCallback | None = None,
        cancel_callback: CancelCallback | None = None,
    ) -> DownloadResult:
        """Download a single file with verification and atomic finalization."""

        if not isinstance(url, str) or not url.strip():
            raise ValueError("A non-empty download URL is required.")

        if expected_size is not None:
            if isinstance(expected_size, bool) or not isinstance(
                expected_size, int
            ):
                raise TypeError("expected_size must be an integer.")
            if expected_size < 0:
                raise ValueError("expected_size cannot be negative.")

        if expected_sha256 is not None:
            expected_sha256 = expected_sha256.strip().lower()

            if len(expected_sha256) != 64:
                raise ValueError("SHA-256 must contain exactly 64 characters.")

            try:
                int(expected_sha256, 16)
            except ValueError as exc:
                raise ValueError("SHA-256 must be hexadecimal.") from exc

        destination = Path(destination).expanduser()
        destination.parent.mkdir(parents=True, exist_ok=True)

        partial = destination.with_name(destination.name + ".part")

        if destination.exists():
            if self._validate_existing(
                destination,
                expected_sha256=expected_sha256,
                expected_size=expected_size,
            ):
                if not overwrite:
                    return DownloadResult(
                        url=url,
                        destination=destination,
                        size_bytes=destination.stat().st_size,
                        sha256=self._hash_file(destination),
                        resumed=False,
                        already_exists=True,
                    )

            elif not overwrite:
                raise DownloadExistsError(
                    f"Existing destination does not match expected integrity: "
                    f"{destination}. Use overwrite=True to replace it."
                )

        existing_partial = (
            partial.stat().st_size
            if resume and partial.exists()
            else 0
        )

        request_headers = {
            "User-Agent": self.user_agent,
        }

        if existing_partial:
            request_headers["Range"] = f"bytes={existing_partial}-"

        request = urllib.request.Request(
            url,
            headers=request_headers,
        )

        resumed = False
        bytes_written = 0
        total_size: int | None = expected_size

        try:
            with urllib.request.urlopen(
                request,
                timeout=self.timeout,
            ) as response:

                status = getattr(response, "status", response.getcode())

                # Resume only when the server returns a valid partial response.
                if existing_partial and status == 206:
                    content_range = response.headers.get("Content-Range", "")

                    if content_range.startswith(
                        f"bytes {existing_partial}-"
                    ):
                        write_mode = "ab"
                        resumed = True
                        bytes_written = existing_partial

                        content_length = response.headers.get(
                            "Content-Length"
                        )

                        if content_length is not None:
                            try:
                                total_size = (
                                    existing_partial
                                    + int(content_length)
                                )
                            except ValueError:
                                total_size = expected_size

                    else:
                        write_mode = "wb"
                        bytes_written = 0
                        resumed = False

                else:
                    # Server ignored the Range request. Start over.
                    write_mode = "wb"
                    bytes_written = 0
                    resumed = False

                if total_size is None:
                    content_length = response.headers.get(
                        "Content-Length"
                    )

                    if content_length is not None:
                        try:
                            total_size = int(content_length)
                        except ValueError:
                            total_size = None

                with partial.open(write_mode) as output:
                    while True:
                        if cancel_callback and cancel_callback():
                            raise DownloadCancelled(
                                f"Download cancelled: {url}"
                            )

                        chunk = response.read(self.chunk_size)

                        if not chunk:
                            break

                        output.write(chunk)
                        bytes_written += len(chunk)

                        if progress_callback:
                            progress_callback(
                                url,
                                bytes_written,
                                total_size,
                            )

                    output.flush()
                    os.fsync(output.fileno())

        except DownloadCancelled:
            # Preserve partial data for a future resume.
            raise

        except urllib.error.HTTPError as exc:
            raise DownloadError(
                f"HTTP error {exc.code} while downloading {url}: "
                f"{exc.reason}"
            ) from exc

        except urllib.error.URLError as exc:
            raise DownloadError(
                f"Network error while downloading {url}: {exc.reason}"
            ) from exc

        except TimeoutError as exc:
            raise DownloadError(
                f"Download timed out: {url}"
            ) from exc

        except OSError as exc:
            raise DownloadError(
                f"File error while downloading {url}: {exc}"
            ) from exc

        if not partial.exists():
            raise DownloadError(
                f"Download did not produce a file: {url}"
            )

        actual_size = partial.stat().st_size

        if expected_size is not None and actual_size != expected_size:
            partial.unlink(missing_ok=True)

            raise DownloadIntegrityError(
                f"Size mismatch for {url}: expected {expected_size} bytes, "
                f"received {actual_size} bytes."
            )

        if total_size is not None and actual_size != total_size:
            # The server-reported size is not always reliable.
            # Expected metadata size, when available, takes precedence.
            if expected_size is None:
                total_size = actual_size

        actual_hash = self._hash_file(partial)

        if expected_sha256 is not None:
            if actual_hash.lower() != expected_sha256.lower():
                partial.unlink(missing_ok=True)

                raise DownloadIntegrityError(
                    f"SHA-256 mismatch for {url}."
                )

        # If overwrite was requested, replace the existing destination.
        # os.replace provides atomic replacement on the same filesystem.
        os.replace(partial, destination)

        return DownloadResult(
            url=url,
            destination=destination,
            size_bytes=actual_size,
            sha256=actual_hash,
            resumed=resumed,
        )

    def download_model(
        self,
        model: ModelMetadata,
        destination_dir: str | Path,
        *,
        url_resolver: URLResolver,
        overwrite: bool = False,
        resume: bool = True,
        progress_callback: ProgressCallback | None = None,
        cancel_callback: CancelCallback | None = None,
    ) -> list[DownloadResult]:
        """Download all declared model files using an explicit URL resolver."""

        destination_dir = Path(destination_dir).expanduser()
        destination_dir.mkdir(parents=True, exist_ok=True)

        results: list[DownloadResult] = []

        for model_file in model.files:
            if cancel_callback and cancel_callback():
                raise DownloadCancelled(
                    f"Model download cancelled: {model.id}"
                )

            url = url_resolver(model, model_file)

            destination = destination_dir / model_file.filename

            result = self.download_file(
                url,
                destination,
                expected_sha256=model_file.sha256,
                expected_size=model_file.size_bytes,
                overwrite=overwrite,
                resume=resume,
                progress_callback=progress_callback,
                cancel_callback=cancel_callback,
            )

            results.append(result)

        return results