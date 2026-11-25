"""Tests for Icebrew data export."""

import json

import pandas as pd
import pytest

from icebrew.data.exporter import export_data
from icebrew.core.exceptions import DataError


@pytest.fixture
def sample_df():
    return pd.DataFrame({
        "name": ["Alice", "Bob", "Charlie"],
        "score": [85, 90, 78],
    })


def test_export_csv(sample_df, tmp_path):
    path = tmp_path / "output.csv"

    result = export_data(sample_df, path)

    assert result == path
    assert path.exists()

    loaded = pd.read_csv(path)
    assert loaded.equals(sample_df)


def test_export_json(sample_df, tmp_path):
    path = tmp_path / "output.json"

    export_data(sample_df, path)

    loaded = pd.read_json(path)
    assert loaded.equals(sample_df)


def test_export_jsonl(sample_df, tmp_path):
    path = tmp_path / "output.jsonl"

    export_data(sample_df, path)

    lines = path.read_text(encoding="utf-8").splitlines()

    assert len(lines) == 3
    assert json.loads(lines[0])["name"] == "Alice"


def test_export_xlsx(sample_df, tmp_path):
    path = tmp_path / "output.xlsx"

    export_data(sample_df, path)

    loaded = pd.read_excel(path)
    assert loaded.equals(sample_df)


def test_export_parquet(sample_df, tmp_path):
    path = tmp_path / "output.parquet"

    try:
        export_data(sample_df, path)
    except DataError as exc:
        if "dependency" in str(exc).lower():
            pytest.skip("Parquet engine unavailable")
        raise

    loaded = pd.read_parquet(path)
    assert loaded.equals(sample_df)


def test_export_with_index(sample_df, tmp_path):
    path = tmp_path / "output.csv"

    export_data(sample_df, path, index=True)

    loaded = pd.read_csv(path)
    assert "Unnamed: 0" in loaded.columns


def test_export_with_explicit_format(sample_df, tmp_path):
    path = tmp_path / "output.data"

    export_data(sample_df, path, format="csv")

    assert path.exists()


def test_export_no_overwrite(sample_df, tmp_path):
    path = tmp_path / "output.csv"
    path.write_text("original", encoding="utf-8")

    with pytest.raises(DataError):
        export_data(sample_df, path)

    assert path.read_text(encoding="utf-8") == "original"


def test_export_overwrite(sample_df, tmp_path):
    path = tmp_path / "output.csv"
    path.write_text("original", encoding="utf-8")

    export_data(sample_df, path, overwrite=True)

    loaded = pd.read_csv(path)
    assert loaded.equals(sample_df)


def test_export_missing_directory(sample_df, tmp_path):
    path = tmp_path / "missing" / "output.csv"

    with pytest.raises(DataError):
        export_data(sample_df, path)


def test_export_directory_path(sample_df, tmp_path):
    with pytest.raises(DataError):
        export_data(sample_df, tmp_path)


def test_export_invalid_format(sample_df, tmp_path):
    path = tmp_path / "output.xyz"

    with pytest.raises(DataError):
        export_data(sample_df, path)


def test_export_invalid_dataframe(tmp_path):
    path = tmp_path / "output.csv"

    with pytest.raises(TypeError):
        export_data([1, 2, 3], path)


def test_export_empty_dataframe(tmp_path):
    df = pd.DataFrame()
    path = tmp_path / "empty.csv"

    export_data(df, path)

    assert path.exists()


def test_export_sheet_name_validation(sample_df, tmp_path):
    path = tmp_path / "output.xlsx"

    with pytest.raises(ValueError):
        export_data(
            sample_df,
            path,
            sheet_name="This sheet name is far too long for Excel",
        )


def test_export_invalid_sheet_characters(sample_df, tmp_path):
    path = tmp_path / "output.xlsx"

    with pytest.raises(ValueError):
        export_data(sample_df, path, sheet_name="Bad/Sheet")