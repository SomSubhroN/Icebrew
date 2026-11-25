"""Tests for Icebrew data conversion."""

import pandas as pd
import pytest

from icebrew.data.converter import convert_data


@pytest.fixture
def sample_df():
    return pd.DataFrame({
        "age": ["20", "25", "30"],
        "score": ["85.5", "90.2", "78.0"],
        "active": ["True", "False", "True"],
        "date": ["2026-01-01", "2026-01-02", "2026-01-03"],
        "status": ["A", "B", "A"],
    })


def test_convert_integer(sample_df):
    result = convert_data(sample_df, {"age": "int"})

    assert str(result["age"].dtype) == "Int64"
    assert result["age"].tolist() == [20, 25, 30]


def test_convert_float(sample_df):
    result = convert_data(sample_df, {"score": "float"})

    assert result["score"].dtype == "float64"


def test_convert_string(sample_df):
    result = convert_data(sample_df, {"age": "string"})

    assert str(result["age"].dtype) == "string"


def test_convert_boolean(sample_df):
    result = convert_data(sample_df, {"active": "bool"})

    assert str(result["active"].dtype) == "boolean"
    assert result["active"].tolist() == [True, False, True]


def test_convert_datetime(sample_df):
    result = convert_data(sample_df, {"date": "datetime"})

    assert pd.api.types.is_datetime64_any_dtype(result["date"])


def test_convert_datetime_with_format():
    df = pd.DataFrame({"date": ["01-02-2026", "03-04-2026"]})

    result = convert_data(
        df,
        {"date": {"type": "datetime", "format": "%d-%m-%Y"}},
    )

    assert result["date"].iloc[0] == pd.Timestamp("2026-02-01")


def test_convert_category(sample_df):
    result = convert_data(sample_df, {"status": "category"})

    assert isinstance(result["status"].dtype, pd.CategoricalDtype)


def test_convert_ordered_category():
    df = pd.DataFrame({"grade": ["low", "high", "medium"]})

    result = convert_data(
        df,
        {
            "grade": {
                "type": "category",
                "categories": ["low", "medium", "high"],
                "ordered": True,
            }
        },
    )

    assert result["grade"].cat.ordered is True
    assert result["grade"].cat.categories.tolist() == ["low", "medium", "high"]


def test_convert_object(sample_df):
    result = convert_data(sample_df, {"age": "object"})

    assert result["age"].dtype == object


def test_coerce_invalid_integer():
    df = pd.DataFrame({"age": ["20", "bad", "30"]})

    result = convert_data(df, {"age": "int"}, errors="coerce")

    assert result["age"].isna().sum() == 1


def test_coerce_invalid_float():
    df = pd.DataFrame({"score": ["10.5", "invalid", "20"]})

    result = convert_data(df, {"score": "float"}, errors="coerce")

    assert result["score"].isna().sum() == 1


def test_coerce_invalid_datetime():
    df = pd.DataFrame({"date": ["2026-01-01", "invalid"]})

    result = convert_data(df, {"date": "datetime"}, errors="coerce")

    assert result["date"].isna().sum() == 1


def test_coerce_invalid_boolean():
    df = pd.DataFrame({"active": ["True", "unknown", "False"]})

    result = convert_data(df, {"active": "boolean"}, errors="coerce")

    assert result["active"].isna().sum() == 1


def test_custom_boolean_mapping():
    df = pd.DataFrame({"active": ["yes", "no", "yes"]})

    result = convert_data(
        df,
        {
            "active": {
                "type": "boolean",
                "true_values": ["yes"],
                "false_values": ["no"],
            }
        },
    )

    assert result["active"].tolist() == [True, False, True]


def test_boolean_invalid_raises():
    df = pd.DataFrame({"active": ["yes", "unknown"]})

    with pytest.raises(ValueError):
        convert_data(
            df,
            {
                "active": {
                    "type": "boolean",
                    "true_values": ["yes"],
                    "false_values": ["no"],
                }
            },
        )


def test_ignore_conversion_error():
    df = pd.DataFrame({"age": ["20", "invalid"]})

    result = convert_data(df, {"age": "int"}, errors="ignore")

    assert result["age"].equals(df["age"])


def test_missing_column():
    df = pd.DataFrame({"age": ["20"]})

    with pytest.raises(KeyError):
        convert_data(df, {"missing": "int"})


def test_invalid_type():
    df = pd.DataFrame({"age": ["20"]})

    with pytest.raises(ValueError):
        convert_data(df, {"age": "unsupported"})


def test_invalid_errors_mode():
    df = pd.DataFrame({"age": ["20"]})

    with pytest.raises(ValueError):
        convert_data(df, {"age": "int"}, errors="invalid")


def test_invalid_conversion_specification():
    df = pd.DataFrame({"age": ["20"]})

    with pytest.raises(ValueError):
        convert_data(df, {"age": {}})


def test_invalid_dataframe():
    with pytest.raises(TypeError):
        convert_data([1, 2, 3], {"age": "int"})


def test_invalid_conversion_mapping():
    df = pd.DataFrame({"age": ["20"]})

    with pytest.raises(TypeError):
        convert_data(df, ["age"])


def test_conversion_does_not_mutate(sample_df):
    original = sample_df.copy(deep=True)

    convert_data(sample_df, {"age": "int"})

    assert sample_df.equals(original)


def test_duplicate_columns_rejected():
    df = pd.DataFrame([[1, 2]], columns=["age", "age"])

    with pytest.raises(ValueError):
        convert_data(df, {"age": "int"})


def test_nullable_integer():
    df = pd.DataFrame({"age": ["20", None, "30"]})

    result = convert_data(df, {"age": "int"})

    assert str(result["age"].dtype) == "Int64"
    assert result["age"].isna().sum() == 1