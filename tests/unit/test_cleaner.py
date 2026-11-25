
import pandas as pd
import pytest

from icebrew.data.cleaner import clean_data


def test_drop_duplicates():
    df = pd.DataFrame({
        "name": ["Alice", "Bob", "Alice"],
        "age": [20, 25, 20],
    })

    result = clean_data(df, drop_duplicates=True)

    assert len(result) == 2


def test_drop_empty_rows():
    df = pd.DataFrame({
        "a": [1, None, 3],
        "b": [2, None, 4],
    })

    result = clean_data(df, drop_empty_rows=True)

    assert len(result) == 2
    assert result.index.tolist() == [0, 2]


def test_drop_empty_columns():
    df = pd.DataFrame({
        "a": [1, 2],
        "empty": [None, None],
    })

    result = clean_data(df, drop_empty_columns=True)

    assert list(result.columns) == ["a"]


def test_trim_whitespace():
    df = pd.DataFrame({
        "name": [" Alice ", " Bob ", "Charlie"],
    })

    result = clean_data(df, trim_whitespace=True)

    assert result["name"].tolist() == [
        "Alice", "Bob", "Charlie"
    ]


def test_trim_whitespace_preserves_non_strings():
    df = pd.DataFrame({
        "mixed": ["  hello  ", 10, None],
    })

    result = clean_data(df, trim_whitespace=True)

    assert result["mixed"].iloc[0] == "hello"
    assert result["mixed"].iloc[1] == 10
    assert pd.isna(result["mixed"].iloc[2])


def test_replace_values():
    df = pd.DataFrame({
        "status": ["yes", "no", "yes"],
    })

    result = clean_data(
        df,
        replace_values={"yes": "approved", "no": "rejected"},
    )

    assert result["status"].tolist() == [
        "approved", "rejected", "approved"
    ]


def test_normalize_missing():
    df = pd.DataFrame({
        "score": [10, "NA", "null", 20],
    })

    result = clean_data(
        df,
        normalize_missing=["NA", "null"],
    )

    assert pd.isna(result["score"].iloc[1])
    assert pd.isna(result["score"].iloc[2])


def test_rename_columns():
    df = pd.DataFrame({
        "old_name": [1, 2],
    })

    result = clean_data(
        df,
        rename_columns={"old_name": "new_name"},
    )

    assert list(result.columns) == ["new_name"]


def test_combined_operations():
    df = pd.DataFrame({
        "name": [" Alice ", " Alice ", None],
        "status": ["yes", "yes", "NA"],
        "empty": [None, None, None],
    })

    result = clean_data(
        df,
        trim_whitespace=True,
        normalize_missing=["NA"],
        drop_empty_rows=True,
        drop_empty_columns=True,
        drop_duplicates=True,
        replace_values={"yes": "approved"},
        rename_columns={"name": "person"},
    )

    assert list(result.columns) == ["person", "status"]
    assert len(result) == 1
    assert result.iloc[0]["person"] == "Alice"
    assert result.iloc[0]["status"] == "approved"


def test_non_destructive():
    df = pd.DataFrame({
        "name": [" Alice ", "Bob"],
        "score": [10, 20],
    })

    original = df.copy(deep=True)

    clean_data(
        df,
        trim_whitespace=True,
        drop_duplicates=True,
    )

    pd.testing.assert_frame_equal(df, original)


def test_invalid_input():
    with pytest.raises(TypeError):
        clean_data([1, 2, 3])


def test_invalid_replace_values():
    df = pd.DataFrame({"a": [1, 2]})

    with pytest.raises(TypeError):
        clean_data(df, replace_values=["invalid"])


def test_invalid_rename_columns():
    df = pd.DataFrame({"a": [1, 2]})

    with pytest.raises(TypeError):
        clean_data(df, rename_columns=["invalid"])
