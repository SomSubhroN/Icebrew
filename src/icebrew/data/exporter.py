"""Data export utilities for Icebrew."""

from pathlib import Path
import os
import tempfile

import pandas as pd

from icebrew.core.exceptions import DataError


SUPPORTED_FORMATS = {"csv", "json", "jsonl", "xlsx", "parquet"}


def export_data(
    df: pd.DataFrame,
    file_path: str | Path,
    *,
    format: str | None = None,
    overwrite: bool = False,
    index: bool = False,
    encoding: str = "utf-8",
    sheet_name: str = "Sheet1",
) -> Path:
    """Export a DataFrame safely to a supported format."""

    if not isinstance(df, pd.DataFrame):
        raise TypeError("Expected a pandas DataFrame.")

    file_path = Path(file_path)

    if file_path.exists() and file_path.is_dir():
        raise DataError(f"Output path is a directory: {file_path}")

    if not file_path.parent.exists():
        raise DataError(f"Parent directory does not exist: {file_path.parent}")

    if not file_path.parent.is_dir():
        raise DataError(f"Invalid parent directory: {file_path.parent}")

    export_format = (format or file_path.suffix.lstrip(".")).lower()

    if export_format not in SUPPORTED_FORMATS:
        raise DataError(
            f"Unsupported export format: {export_format}. "
            f"Supported formats: {', '.join(sorted(SUPPORTED_FORMATS))}"
        )

    if not file_path.suffix:
        raise DataError("Output file must have an extension.")

    if not overwrite and file_path.exists():
        raise DataError(f"File already exists: {file_path}")

    if not isinstance(overwrite, bool):
        raise TypeError("overwrite must be a boolean.")

    if not isinstance(index, bool):
        raise TypeError("index must be a boolean.")

    if not isinstance(encoding, str) or not encoding:
        raise ValueError("Encoding must be a non-empty string.")

    if not isinstance(sheet_name, str) or not sheet_name:
        raise ValueError("Sheet name must be a non-empty string.")

    if export_format == "xlsx":
        if len(sheet_name) > 31:
            raise ValueError("Excel sheet names cannot exceed 31 characters.")
        if any(char in sheet_name for char in "[]:*?/\\"):
            raise ValueError("Excel sheet name contains invalid characters.")

    temp_path = None

    try:
        # Create a temporary file in the destination directory.
        with tempfile.NamedTemporaryFile(
            suffix=file_path.suffix,
            prefix=".icebrew_",
            dir=file_path.parent,
            delete=False,
        ) as temp_file:
            temp_path = Path(temp_file.name)

        # Write to the temporary file first.
        if export_format == "csv":
            df.to_csv(
                temp_path,
                index=index,
                encoding=encoding,
            )

        elif export_format == "json":
            df.to_json(
                temp_path,
                orient="records",
                indent=2,
                force_ascii=False,
            )

        elif export_format == "jsonl":
            df.to_json(
                temp_path,
                orient="records",
                lines=True,
                force_ascii=False,
            )

        elif export_format == "xlsx":
            df.to_excel(
                temp_path,
                index=index,
                sheet_name=sheet_name,
                engine="openpyxl",
            )

        elif export_format == "parquet":
            df.to_parquet(
                temp_path,
                index=index,
                engine="pyarrow",
            )

        # Commit the temporary file to its destination.
        if overwrite:
            os.replace(temp_path, file_path)
        else:
            # Hard-link creation fails if the destination already exists.
            # This provides an atomic no-overwrite operation.
            os.link(temp_path, file_path)
            os.unlink(temp_path)

        temp_path = None

        return file_path

    except FileExistsError as exc:
        raise DataError(f"File already exists: {file_path}") from exc

    except ImportError as exc:
        raise DataError(
            f"Required export dependency is unavailable for "
            f"{export_format.upper()}: {exc}"
        ) from exc

    except Exception as exc:
        if isinstance(exc, DataError):
            raise

        raise DataError(
            f"Failed to export data to {file_path}: {exc}"
        ) from exc

    finally:
        if temp_path is not None and temp_path.exists():
            try:
                temp_path.unlink()
            except OSError:
                pass