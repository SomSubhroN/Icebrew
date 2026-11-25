
import pandas as pd
import pytest

from icebrew.data.missing import analyze_missing, handle_missing


# ---------- Analysis ----------

def test_missing_report():
    df = pd.DataFrame({
        "a": [1, None, 3],
        "b": [None, 2, None],
    })

    result = analyze_missing(df)

    assert result["missing_total"] == 3
    assert result["missing_percent"] == pytest.approx(50.0)
    assert result["columns"]["a"]["missing"] == 1
    assert result["columns"]["b"]["missing"] == 2


def test_rows_with_missing():
    df = pd.DataFrame({
        "a": [1, None, 3],
        "b": [2, None, None],
    })

    result = analyze_missing(df)

    assert result["rows_with_missing"] == {1: 2, 2: 1}
    assert result["rows_with_missing_count"] == 2


def test_missing_report_empty_dataframe():
    df = pd.DataFrame()

    result = analyze_missing(df)

    assert result["missing_total"] == 0
    assert result["missing_percent"] == 0.0


def test_missing_report_empty_rows():
    df = pd.DataFrame(columns=["a", "b"])

    result = analyze_missing(df)

    assert result["missing_total"] == 0
    assert result["columns"]["a"]["missing_percent"] == 0.0


def test_missing_invalid_input():
    with pytest.raises(TypeError):
        analyze_missing([1, 2, 3])


# ---------- Row and column dropping ----------

def test_drop_rows_threshold():
    df = pd.DataFrame({
        "a": [1, None, None],
        "b": [2, None, 4],
    })

    result = handle_missing(df, drop_rows_threshold=50)

    assert len(result) == 2
    assert result.index.tolist() == [0, 2]


def test_drop_columns_threshold():
    df = pd.DataFrame({
        "a": [1, 2, 3],
        "b": [None, None, 3],
    })

    result = handle_missing(df, drop_columns_threshold=50)

    assert list(result.columns) == ["a"]


def test_drop_threshold_zero():
    df = pd.DataFrame({
        "a": [1, None],
        "b": [2, 3],
    })

    result = handle_missing(df, drop_columns_threshold=0)

    assert result.shape[1] == 0


def test_invalid_threshold():
    df = pd.DataFrame({"a": [1, None]})

    with pytest.raises(ValueError):
        handle_missing(df, drop_rows_threshold=101)


def test_threshold_type():
    df = pd.DataFrame({"a": [1, None]})

    with pytest.raises(TypeError):
        handle_missing(df, drop_rows_threshold="50")


# ---------- Imputation ----------

def test_mean_imputation():
    df = pd.DataFrame({"score": [10.0, None, 30.0]})

    result = handle_missing(df, impute={"score": "mean"})

    assert result["score"].tolist() == [10.0, 20.0, 30.0]


def test_median_imputation():
    df = pd.DataFrame({"score": [10.0, None, 100.0]})

    result = handle_missing(df, impute={"score": "median"})

    assert result["score"].tolist() == [10.0, 55.0, 100.0]


def test_mode_imputation():
    df = pd.DataFrame({"category": ["A", None, "A", "B"]})

    result = handle_missing(df, impute={"category": "mode"})

    assert result["category"].tolist() == ["A", "A", "A", "B"]


def test_constant_imputation():
    df = pd.DataFrame({"category": ["A", None, "B"]})

    result = handle_missing(
        df,
        impute={
            "category": {
                "method": "constant",
                "value": "Unknown",
            }
        },
    )

    assert result["category"].tolist() == ["A", "Unknown", "B"]


def test_literal_imputation():
    df = pd.DataFrame({"score": [10, None, 30]})

    result = handle_missing(df, impute={"score": 0})

    assert result["score"].tolist() == [10, 0, 30]


def test_forward_fill():
    df = pd.DataFrame({"score": [10, None, None, 40]})

    result = handle_missing(df, impute={"score": "ffill"})

    assert result["score"].tolist() == [10, 10, 10, 40]


def test_backward_fill():
    df = pd.DataFrame({"score": [None, 20, None, 40]})

    result = handle_missing(df, impute={"score": "bfill"})

    assert result["score"].tolist() == [20, 20, 40, 40]


def test_selective_imputation():
    df = pd.DataFrame({
        "score": [10.0, None],
        "category": ["A", None],
    })

    result = handle_missing(df, impute={"score": "mean"})

    assert result["score"].isna().sum() == 0
    assert result["category"].isna().sum() == 1


def test_mean_imputation_non_numeric():
    df = pd.DataFrame({"category": ["A", None, "B"]})

    with pytest.raises(TypeError):
        handle_missing(df, impute={"category": "mean"})


def test_unknown_column():
    df = pd.DataFrame({"a": [1, None]})

    with pytest.raises(KeyError):
        handle_missing(df, impute={"missing_column": "mean"})


def test_invalid_imputation_method():
    df = pd.DataFrame({"a": [1, None]})

    with pytest.raises(ValueError):
        handle_missing(df, impute={"a": "invalid_method"})


def test_constant_missing_value():
    df = pd.DataFrame({"a": [1, None]})

    with pytest.raises(ValueError):
        handle_missing(
            df,
            impute={"a": {"method": "constant"}},
        )


def test_non_destructive():
    df = pd.DataFrame({
        "a": [10.0, None, 30.0],
    })

    original = df.copy(deep=True)

    handle_missing(df, impute={"a": "mean"})

    pd.testing.assert_frame_equal(df, original)


def test_invalid_dataframe():
    with pytest.raises(TypeError):
        handle_missing([1, 2, 3])
