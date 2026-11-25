
import pandas as pd
import pytest

from icebrew.data.quality import analyze_quality


def test_quality_basic_missing_values():
    df = pd.DataFrame({
        "name": ["Alice", None, "Bob"],
        "age": [20, 25, None],
    })

    result = analyze_quality(df)

    assert result["missing_total"] == 2
    assert result["missing_percent"] == pytest.approx(
        33.3333333333
    )


def test_empty_rows():
    df = pd.DataFrame({
        "a": [1, None, 3],
        "b": [2, None, 4],
    })

    result = analyze_quality(df)

    assert result["empty_rows"] == [1]
    assert result["empty_rows_count"] == 1


def test_empty_columns():
    df = pd.DataFrame({
        "a": [1, 2],
        "empty": [None, None],
    })

    result = analyze_quality(df)

    assert result["empty_columns"] == ["empty"]
    assert result["empty_columns_count"] == 1


def test_duplicate_rows():
    df = pd.DataFrame({
        "name": ["Alice", "Bob", "Alice"],
        "age": [20, 25, 20],
    })

    result = analyze_quality(df)

    assert result["duplicate_rows"] == 1
    assert result["duplicate_row_indices"] == [2]


def test_whitespace_only_cells():
    df = pd.DataFrame({
        "name": ["Alice", " ", "\t", "Bob"],
    })

    result = analyze_quality(df)

    assert result["whitespace_only_total"] == 2
    assert result["whitespace_only"][0]["count"] == 2


def test_duplicate_column_names():
    df = pd.DataFrame(
        [[1, 2, 3]],
        columns=["a", "b", "a"],
    )

    result = analyze_quality(df)

    assert result["duplicate_columns"] == ["a"]
    assert result["duplicate_columns_count"] == 1


def test_column_quality():
    df = pd.DataFrame({
        "score": [10, 20, None],
        "name": ["Alice", "Bob", "Charlie"],
    })

    result = analyze_quality(df)

    assert len(result["columns"]) == 2
    assert result["columns"][0]["column"] == "score"
    assert result["columns"][0]["missing"] == 1
    assert result["columns"][0]["dtype"] == "float64"


def test_empty_dataframe():
    df = pd.DataFrame()

    result = analyze_quality(df)

    assert result["shape"] == (0, 0)
    assert result["missing_total"] == 0
    assert result["missing_percent"] == 0.0
    assert result["duplicate_rows"] == 0


def test_non_destructive():
    df = pd.DataFrame({
        "a": [1, None, 1],
        "b": ["x", " ", "x"],
    })

    original = df.copy(deep=True)

    analyze_quality(df)

    pd.testing.assert_frame_equal(df, original)


def test_invalid_input():
    with pytest.raises(TypeError):
        analyze_quality([1, 2, 3])
