from __future__ import annotations

import hashlib
import io
from pathlib import Path

import pytest

from icebrew.ai.downloads.manager import (
    DownloadCancelled,
    DownloadExistsError,
    DownloadIntegrityError,
    DownloadManager,
)


class FakeResponse:
    def __init__(
        self,
        data: bytes,
        *,
        status: int = 200,
        headers: dict | None = None,
    ):
        self._buffer = io.BytesIO(data)
        self.status = status
        self.headers = headers or {}

    def read(self, size=-1):
        return self._buffer.read(size)

    def getcode(self):
        return self.status

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return None


@pytest.fixture
def manager():
    return DownloadManager(chunk_size=4)


@pytest.fixture
def payload():
    return b"icebrew-model-file-content"


@pytest.fixture
def sha256(payload):
    return hashlib.sha256(payload).hexdigest()


def mock_urlopen(monkeypatch, response):
    def fake_urlopen(request, timeout=None):
        return response

    monkeypatch.setattr(
        "urllib.request.urlopen",
        fake_urlopen,
    )


def test_successful_download(
    manager,
    monkeypatch,
    tmp_path,
    payload,
    sha256,
):
    destination = tmp_path / "model.bin"

    mock_urlopen(
        monkeypatch,
        FakeResponse(
            payload,
            headers={"Content-Length": str(len(payload))},
        ),
    )

    result = manager.download_file(
        "https://example.com/model.bin",
        destination,
        expected_sha256=sha256,
        expected_size=len(payload),
    )

    assert destination.exists()
    assert destination.read_bytes() == payload
    assert result.size_bytes == len(payload)
    assert result.sha256 == sha256
    assert result.already_exists is False
    assert not destination.with_name("model.bin.part").exists()


def test_progress_callback(
    manager,
    monkeypatch,
    tmp_path,
    payload,
):
    destination = tmp_path / "model.bin"
    events = []

    mock_urlopen(
        monkeypatch,
        FakeResponse(
            payload,
            headers={"Content-Length": str(len(payload))},
        ),
    )

    manager.download_file(
        "https://example.com/model.bin",
        destination,
        progress_callback=lambda url, downloaded, total: events.append(
            (url, downloaded, total)
        ),
    )

    assert events
    assert events[-1][1] == len(payload)


def test_existing_verified_file_is_skipped(
    manager,
    monkeypatch,
    tmp_path,
    payload,
    sha256,
):
    destination = tmp_path / "model.bin"
    destination.write_bytes(payload)

    def fail_urlopen(*args, **kwargs):
        pytest.fail("Network request should not have been made.")

    monkeypatch.setattr(
        "urllib.request.urlopen",
        fail_urlopen,
    )

    result = manager.download_file(
        "https://example.com/model.bin",
        destination,
        expected_sha256=sha256,
        expected_size=len(payload),
    )

    assert result.already_exists is True
    assert result.size_bytes == len(payload)


def test_existing_invalid_file_requires_overwrite(
    manager,
    tmp_path,
    payload,
    sha256,
):
    destination = tmp_path / "model.bin"
    destination.write_bytes(b"wrong content")

    with pytest.raises(DownloadExistsError):
        manager.download_file(
            "https://example.com/model.bin",
            destination,
            expected_sha256=sha256,
            expected_size=len(payload),
        )


def test_sha256_mismatch(
    manager,
    monkeypatch,
    tmp_path,
    payload,
):
    destination = tmp_path / "model.bin"

    mock_urlopen(
        monkeypatch,
        FakeResponse(payload),
    )

    wrong_hash = hashlib.sha256(b"wrong").hexdigest()

    with pytest.raises(DownloadIntegrityError):
        manager.download_file(
            "https://example.com/model.bin",
            destination,
            expected_sha256=wrong_hash,
        )

    assert not destination.exists()
    assert not destination.with_name("model.bin.part").exists()


def test_size_mismatch(
    manager,
    monkeypatch,
    tmp_path,
    payload,
):
    destination = tmp_path / "model.bin"

    mock_urlopen(
        monkeypatch,
        FakeResponse(payload),
    )

    with pytest.raises(DownloadIntegrityError):
        manager.download_file(
            "https://example.com/model.bin",
            destination,
            expected_size=len(payload) + 1,
        )

    assert not destination.exists()


def test_cancelled_download_preserves_partial_file(
    manager,
    monkeypatch,
    tmp_path,
    payload,
):
    destination = tmp_path / "model.bin"

    mock_urlopen(
        monkeypatch,
        FakeResponse(payload),
    )

    calls = 0

    def cancel():
        nonlocal calls
        calls += 1
        return calls >= 2

    with pytest.raises(DownloadCancelled):
        manager.download_file(
            "https://example.com/model.bin",
            destination,
            cancel_callback=cancel,
        )

    partial = destination.with_name("model.bin.part")

    assert partial.exists()
    assert not destination.exists()


def test_overwrite_existing_file(
    manager,
    monkeypatch,
    tmp_path,
    payload,
):
    destination = tmp_path / "model.bin"
    destination.write_bytes(b"old data")

    mock_urlopen(
        monkeypatch,
        FakeResponse(payload),
    )

    result = manager.download_file(
        "https://example.com/model.bin",
        destination,
        overwrite=True,
    )

    assert destination.read_bytes() == payload
    assert result.already_exists is False


def test_invalid_sha256_is_rejected(
    manager,
    tmp_path,
):
    with pytest.raises(ValueError):
        manager.download_file(
            "https://example.com/model.bin",
            tmp_path / "model.bin",
            expected_sha256="not-a-hash",
        )


def test_invalid_size_is_rejected(
    manager,
    tmp_path,
):
    with pytest.raises(ValueError):
        manager.download_file(
            "https://example.com/model.bin",
            tmp_path / "model.bin",
            expected_size=-1,
        )


def test_empty_url_is_rejected(
    manager,
    tmp_path,
):
    with pytest.raises(ValueError):
        manager.download_file(
            "",
            tmp_path / "model.bin",
        )


def test_partial_file_is_restarted_if_server_ignores_range(
    manager,
    monkeypatch,
    tmp_path,
    payload,
):
    destination = tmp_path / "model.bin"
    partial = destination.with_name("model.bin.part")
    partial.write_bytes(b"old-partial-data")

    mock_urlopen(
        monkeypatch,
        FakeResponse(
            payload,
            status=200,
            headers={"Content-Length": str(len(payload))},
        ),
    )

    result = manager.download_file(
        "https://example.com/model.bin",
        destination,
        resume=True,
    )

    assert destination.read_bytes() == payload
    assert result.resumed is False
    assert not partial.exists()


def test_resume_from_valid_partial_response(
    manager,
    monkeypatch,
    tmp_path,
    payload,
):
    destination = tmp_path / "model.bin"
    partial = destination.with_name("model.bin.part")

    prefix = payload[:8]
    remainder = payload[8:]

    partial.write_bytes(prefix)

    mock_urlopen(
        monkeypatch,
        FakeResponse(
            remainder,
            status=206,
            headers={
                "Content-Length": str(len(remainder)),
                "Content-Range": (
                    f"bytes {len(prefix)}-{len(payload)-1}/{len(payload)}"
                ),
            },
        ),
    )

    result = manager.download_file(
        "https://example.com/model.bin",
        destination,
        resume=True,
    )

    assert destination.read_bytes() == payload
    assert result.resumed is True