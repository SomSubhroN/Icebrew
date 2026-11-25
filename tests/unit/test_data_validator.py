import pandas as pd

from icebrew.data.validator import validate_data


def test_valid_dataframe():
    df = pd.DataFrame({"age": [20, 21], "name": ["A", "B"]})

    result = validate_data(df, required_columns=["age", "name"])

    assert result["valid"] is True


def test_missing_required_columns():
    df = pd.DataFrame({"age": [20]})

    result = validate_data(df, required_columns=["age", "name"])

    assert result["valid"] is False
    assert "name" in result["issues"][0]["columns"]


def test_dtype_mismatch():
    df = pd.DataFrame({"age": [20, 21]})

    result = validate_data(df, expected_dtypes={"age": "float64"})

    assert result["valid"] is False


def test_non_nullable():
    df = pd.DataFrame({"age": [20, None]})

    result = validate_data(df, non_nullable=["age"])

    assert result["valid"] is False


def test_allowed_values():
    df = pd.DataFrame({"status": ["active", "unknown"]})

    result = validate_data(
        df,
        allowed_values={"status": ["active", "inactive"]},
    )

    assert result["valid"] is False


def test_numeric_ranges():
    df = pd.DataFrame({"score": [10, 120]})

    result = validate_data(
        df,
        numeric_ranges={"score": (0, 100)},
    )

    assert result["valid"] is False


def test_unique_columns():
    df = pd.DataFrame({"id": [1, 1, 2]})

    result = validate_data(df, unique_columns=["id"])

    assert result["valid"] is False


def test_valid_numeric_range():
    df = pd.DataFrame({"score": [0, 50, 100]})

    result = validate_data(
        df,
        numeric_ranges={"score": (0, 100)},
    )

    assert result["valid"] is True


def test_missing_column_constraint_is_skipped():
    df = pd.DataFrame({"age": [20]})

    result = validate_data(
        df,
        expected_dtypes={"missing": "int64"},
    )

    assert result["valid"] is True


def test_invalid_dataframe():
    try:
        validate_data([1, 2, 3])
    except TypeError:
        pass
    else:
        raise AssertionError("Expected TypeError")