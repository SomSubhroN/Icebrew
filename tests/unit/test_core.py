
import pytest # type: ignore

from icebrew.core.exceptions import (
    DataError,
    IcebrewError,
    ModelDownloadError,
    ModelNotFoundError,
)


def test_icebrew_error_stores_message_and_code() -> None:
    error = IcebrewError("Something went wrong", code="TEST_ERROR")

    assert error.message == "Something went wrong"
    assert error.code == "TEST_ERROR"
    assert str(error) == "Something went wrong"


def test_data_error_inherits_from_icebrew_error() -> None:
    error = DataError("Unable to read dataset")

    assert isinstance(error, IcebrewError)
    assert error.code == "DATA_ERROR"


def test_model_not_found_error() -> None:
    error = ModelNotFoundError("Model unavailable")

    assert isinstance(error, IcebrewError)
    assert error.code == "MODEL_NOT_FOUND"


def test_model_download_error() -> None:
    error = ModelDownloadError("Download failed")

    assert isinstance(error, IcebrewError)
    assert error.code == "MODEL_DOWNLOAD_ERROR"


def test_icebrew_error_can_be_caught() -> None:
    with pytest.raises(IcebrewError):
        raise DataError("Dataset failure")
