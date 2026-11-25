
import pandas as pd
import pytest

from icebrew.data.frequency import (
    crosstab,
    grouped_value_counts,
    value_counts,
)


@pytest.fixture
def sample_df():
    return pd.DataFrame(
        {
            "department": ["CS", "CS", "Math", "Math", "CS", "Math"],
            "gender": ["M", "F", "M", "F", "M", "F"],
            "grade": ["A", "B", "A", "B", "A", "C"],
            "score": [90, 80, 90, 75, 85, 60],
        }
    )


def test_value_counts(sample_df):
    result = value_counts(sample_df, "department")

    assert result.loc["CS", "count"] == 3
    assert result.loc["Math", "count"] == 3


def test_value_counts_normalized(sample_df):
    result = value_counts(sample_df, "department", normalize=True)

    assert result.loc["CS", "proportion"] == pytest.approx(0.5)
    assert result.loc["Math", "proportion"] == pytest.approx(0.5)


def test_value_counts_top_n(sample_df):
    result = value_counts(sample_df, "grade", top_n=2)

    assert len(result) == 2


def test_value_counts_ascending(sample_df):
    result = value_counts(sample_df, "grade", ascending=True)

    assert result["count"].iloc[0] == 1


def test_value_counts_missing():
    df = pd.DataFrame({"x": ["A", "B", None, "A"]})

    result = value_counts(df, "x", dropna=False)

    assert result["count"].sum() == 4


def test_grouped_value_counts(sample_df):
    result = grouped_value_counts(sample_df, ["department", "gender"])

    assert len(result) == 4
    assert result["count"].sum() == 6


def test_grouped_value_counts_normalized(sample_df):
    result = grouped_value_counts(
        sample_df,
        ["department", "gender"],
        normalize=True,
    )

    assert "proportion" in result.columns
    assert result["proportion"].sum() == pytest.approx(1.0)


def test_grouped_value_counts_top_n(sample_df):
    result = grouped_value_counts(
        sample_df,
        ["department", "gender"],
        top_n=2,
    )

    assert len(result) == 2


def test_crosstab_counts(sample_df):
    result = crosstab(sample_df, "department", "gender")

    assert result.loc["CS", "M"] == 2
    assert result.loc["CS", "F"] == 1


def test_crosstab_normalize_all(sample_df):
    result = crosstab(
        sample_df,
        "department",
        "gender",
        normalize=True,
    )

    assert result.values.sum() == pytest.approx(1.0)


def test_crosstab_normalize_index(sample_df):
    result = crosstab(
        sample_df,
        "department",
        "gender",
        normalize="index",
    )

    assert result.loc["CS"].sum() == pytest.approx(1.0)


def test_crosstab_normalize_columns(sample_df):
    result = crosstab(
        sample_df,
        "department",
        "gender",
        normalize="columns",
    )

    assert result["M"].sum() == pytest.approx(1.0)


def test_crosstab_margins(sample_df):
    result = crosstab(
        sample_df,
        "department",
        "gender",
        margins=True,
    )

    assert "All" in result.index
    assert "All" in result.columns


def test_crosstab_multiple_columns(sample_df):
    result = crosstab(
        sample_df,
        ["department", "grade"],
        "gender",
    )

    assert isinstance(result.index, pd.MultiIndex)


def test_crosstab_multiple_variables(sample_df):
    result = crosstab(
        sample_df,
        "department",
        ["gender", "grade"],
    )

    assert isinstance(result.columns, pd.MultiIndex)


def test_missing_column():
    df = pd.DataFrame({"x": [1, 2]})

    with pytest.raises(KeyError):
        value_counts(df, "missing")


def test_invalid_top_n():
    df = pd.DataFrame({"x": [1, 2]})

    with pytest.raises(ValueError):
        value_counts(df, "x", top_n=0)


def test_invalid_normalization():
    df = pd.DataFrame({"x": [1, 2], "y": [3, 4]})

    with pytest.raises(ValueError):
        crosstab(df, "x", "y", normalize="invalid")


def test_non_dataframe():
    with pytest.raises(TypeError):
        value_counts([1, 2, 3], "x")


def test_non_mutating(sample_df):
    original = sample_df.copy(deep=True)

    value_counts(sample_df, "department")
    grouped_value_counts(sample_df, ["department", "gender"])
    crosstab(sample_df, "department", "gender")

    pd.testing.assert_frame_equal(sample_df, original)
