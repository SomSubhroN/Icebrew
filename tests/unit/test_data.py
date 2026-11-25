
import pandas as pd
import pytest

from icebrew.data.loader import load_csv


def test_load_csv(tmp_path):
    file_path = tmp_path / "sample.csv"
    file_path.write_text(
        "name,age\nAlice,21\nBob,22\n",
        encoding="utf-8",
    )

    df = load_csv(file_path)

    assert isinstance(df, pd.DataFrame)
    assert df.shape == (2, 2)
    assert list(df.columns) == ["name", "age"]
    assert df.iloc[0]["name"] == "Alice"


def test_load_csv_missing_file(tmp_path):
    file_path = tmp_path / "does_not_exist.csv"

    with pytest.raises(FileNotFoundError):
        load_csv(file_path)


def test_load_csv_directory(tmp_path):
    with pytest.raises(ValueError):
        load_csv(tmp_path)


def test_load_csv_header_only(tmp_path):
    file_path = tmp_path / "empty_dataset.csv"
    file_path.write_text("name,age\n", encoding="utf-8")

    df = load_csv(file_path)

    assert isinstance(df, pd.DataFrame)
    assert df.empty
    assert list(df.columns) == ["name", "age"]


def test_load_csv_custom_delimiter(tmp_path):
    file_path = tmp_path / "semicolon.csv"
    file_path.write_text(
        "name;age\nAlice;21\nBob;22\n",
        encoding="utf-8",
    )

    df = load_csv(file_path, delimiter=";")

    assert df.shape == (2, 2)
    assert list(df.columns) == ["name", "age"]
    assert df.iloc[1]["name"] == "Bob"
    assert df.iloc[1]["age"] == 22

def test_load_csv_encoding(tmp_path):
    file_path = tmp_path / "encoded.csv"
    file_path.write_text(
        "name\nCafé\n",
        encoding="utf-8",
    )

    df = load_csv(file_path, encoding="utf-8")

    assert df.iloc[0]["name"] == "Café"

@pytest.mark.parametrize("delimiter", ["", ";;", "abc"])
def test_load_csv_invalid_delimiter(tmp_path, delimiter):
    file_path = tmp_path / "sample.csv"
    file_path.write_text("name,age\nAlice,21\n", encoding="utf-8")

    with pytest.raises(ValueError):
        load_csv(file_path, delimiter=delimiter)

def test_load_csv_custom_na_values(tmp_path):
    file_path = tmp_path / "missing.csv"
    file_path.write_text(
        "name,score\nAlice,10\nBob,NA\n",
        encoding="utf-8",
    )

    df = load_csv(file_path, na_values=["NA"])

    assert pd.isna(df.iloc[1]["score"])

def test_load_csv_without_header(tmp_path):
    file_path = tmp_path / "no_header.csv"
    file_path.write_text("Alice,21\nBob,22\n", encoding="utf-8")

    df = load_csv(file_path, header=None)

    assert list(df.columns) == [0, 1]
    assert df.shape == (2, 2)
    assert df.iloc[0, 0] == "Alice"

def test_load_csv_skiprows(tmp_path):
    file_path = tmp_path / "skip.csv"
    file_path.write_text(
        "metadata\nname,age\nAlice,21\nBob,22\n",
        encoding="utf-8",
    )

    df = load_csv(file_path, skiprows=1)

    assert list(df.columns) == ["name", "age"]
    assert df.shape == (2, 2)

def test_load_csv_nrows(tmp_path):
    file_path = tmp_path / "large.csv"
    file_path.write_text(
        "name,age\nAlice,21\nBob,22\nCharlie,23\n",
        encoding="utf-8",
    )

    df = load_csv(file_path, nrows=2)

    assert df.shape == (2, 2)
    assert list(df["name"]) == ["Alice", "Bob"]