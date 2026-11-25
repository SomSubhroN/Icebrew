
import pandas as pd
import pytest

from icebrew.data.transform import (
    select_columns,
    drop_columns,
    filter_rows,
    sort_data,
    add_column,
    group_aggregate,
    merge_data,
    concatenate_data,
)


# ---------- Column operations ----------

def test_select_columns():
    df = pd.DataFrame({"a": [1, 2], "b": [3, 4]})

    result = select_columns(df, ["b"])

    assert list(result.columns) == ["b"]


def test_drop_columns():
    df = pd.DataFrame({"a": [1, 2], "b": [3, 4]})

    result = drop_columns(df, ["b"])

    assert list(result.columns) == ["a"]


def test_select_missing_column():
    df = pd.DataFrame({"a": [1, 2]})

    with pytest.raises(KeyError):
        select_columns(df, ["missing"])


def test_drop_missing_column():
    df = pd.DataFrame({"a": [1, 2]})

    with pytest.raises(KeyError):
        drop_columns(df, ["missing"])


# ---------- Filtering ----------

def test_filter_equality():
    df = pd.DataFrame({"a": [1, 2, 3]})

    result = filter_rows(df, {"a": ("==", 2)})

    assert result["a"].tolist() == [2]


def test_filter_greater_than():
    df = pd.DataFrame({"a": [1, 2, 3]})

    result = filter_rows(df, {"a": (">", 1)})

    assert result["a"].tolist() == [2, 3]


def test_filter_multiple_conditions():
    df = pd.DataFrame({
        "age": [18, 25, 30],
        "score": [50, 80, 90],
    })

    result = filter_rows(
        df,
        {
            "age": (">=", 25),
            "score": (">", 70),
        },
    )

    assert result.shape[0] == 2


def test_filter_in():
    df = pd.DataFrame({"category": ["A", "B", "C"]})

    result = filter_rows(
        df,
        {"category": ("in", ["A", "C"])},
    )

    assert result["category"].tolist() == ["A", "C"]


def test_filter_not_in():
    df = pd.DataFrame({"category": ["A", "B", "C"]})

    result = filter_rows(
        df,
        {"category": ("not_in", ["B"])},
    )

    assert result["category"].tolist() == ["A", "C"]


def test_filter_contains():
    df = pd.DataFrame({"name": ["Alice", "Bob", "Alfred"]})

    result = filter_rows(
        df,
        {"name": ("contains", "Al")},
    )

    assert result["name"].tolist() == ["Alice", "Alfred"]


def test_filter_startswith():
    df = pd.DataFrame({"name": ["Alice", "Bob", "Alfred"]})

    result = filter_rows(
        df,
        {"name": ("startswith", "Al")},
    )

    assert result["name"].tolist() == ["Alice", "Alfred"]


def test_filter_endswith():
    df = pd.DataFrame({"name": ["Alice", "Bob", "Charlie"]})

    result = filter_rows(
        df,
        {"name": ("endswith", "e")},
    )

    assert result["name"].tolist() == ["Alice", "Charlie"]


def test_filter_isna():
    df = pd.DataFrame({"a": [1, None, 3]})

    result = filter_rows(df, {"a": ("isna", None)})

    assert len(result) == 1


def test_filter_notna():
    df = pd.DataFrame({"a": [1, None, 3]})

    result = filter_rows(df, {"a": ("notna", None)})

    assert len(result) == 2


def test_filter_unknown_operator():
    df = pd.DataFrame({"a": [1, 2]})

    with pytest.raises(ValueError):
        filter_rows(df, {"a": ("invalid", 1)})


def test_filter_unknown_column():
    df = pd.DataFrame({"a": [1, 2]})

    with pytest.raises(KeyError):
        filter_rows(df, {"missing": (">", 1)})


def test_filter_invalid_condition():
    df = pd.DataFrame({"a": [1, 2]})

    with pytest.raises(ValueError):
        filter_rows(df, {"a": "> 1"})


# ---------- Sorting ----------

def test_sort_data():
    df = pd.DataFrame({"a": [3, 1, 2]})

    result = sort_data(df, "a")

    assert result["a"].tolist() == [1, 2, 3]


def test_sort_descending():
    df = pd.DataFrame({"a": [3, 1, 2]})

    result = sort_data(df, "a", ascending=False)

    assert result["a"].tolist() == [3, 2, 1]


def test_sort_multiple_columns():
    df = pd.DataFrame({
        "a": [2, 1, 1],
        "b": [2, 3, 1],
    })

    result = sort_data(
        df,
        ["a", "b"],
        ascending=[True, True],
    )

    assert result[["a", "b"]].values.tolist() == [
        [1, 1],
        [1, 3],
        [2, 2],
    ]


def test_sort_missing_column():
    df = pd.DataFrame({"a": [1, 2]})

    with pytest.raises(KeyError):
        sort_data(df, "missing")


# ---------- Derived columns ----------

def test_add_column_values():
    df = pd.DataFrame({"a": [1, 2, 3]})

    result = add_column(df, "b", [4, 5, 6])

    assert result["b"].tolist() == [4, 5, 6]


def test_add_column_callable():
    df = pd.DataFrame({"a": [1, 2, 3]})

    result = add_column(
        df,
        "double",
        lambda frame: frame["a"] * 2,
    )

    assert result["double"].tolist() == [2, 4, 6]


def test_add_column_wrong_length():
    df = pd.DataFrame({"a": [1, 2, 3]})

    with pytest.raises(ValueError):
        add_column(df, "b", [1, 2])


def test_add_column_callable_wrong_return():
    df = pd.DataFrame({"a": [1, 2]})

    with pytest.raises(TypeError):
        add_column(df, "b", lambda frame: 10)


# ---------- Grouping ----------

def test_group_aggregate():
    df = pd.DataFrame({
        "category": ["A", "A", "B"],
        "value": [10, 20, 30],
    })

    result = group_aggregate(
        df,
        "category",
        {"value": "mean"},
    )

    assert result["value"].tolist() == [15, 30]


def test_group_multiple_aggregations():
    df = pd.DataFrame({
        "category": ["A", "A", "B"],
        "value": [10, 20, 30],
    })

    result = group_aggregate(
        df,
        "category",
        {"value": ["mean", "sum"]},
    )

    assert len(result) == 2


def test_group_missing_column():
    df = pd.DataFrame({"a": [1, 2]})

    with pytest.raises(KeyError):
        group_aggregate(df, "missing", {"a": "sum"})


def test_group_empty_aggregations():
    df = pd.DataFrame({"a": [1, 2]})

    with pytest.raises(ValueError):
        group_aggregate(df, "a", {})


# ---------- Merge ----------

def test_merge_inner():
    left = pd.DataFrame({"id": [1, 2], "a": [10, 20]})
    right = pd.DataFrame({"id": [1, 3], "b": [100, 300]})

    result = merge_data(left, right, on="id")

    assert result["id"].tolist() == [1]


def test_merge_left():
    left = pd.DataFrame({"id": [1, 2]})
    right = pd.DataFrame({"id": [1], "b": [100]})

    result = merge_data(left, right, on="id", how="left")

    assert len(result) == 2


def test_merge_different_keys():
    left = pd.DataFrame({"left_id": [1, 2]})
    right = pd.DataFrame({"right_id": [1, 2]})

    result = merge_data(
        left,
        right,
        left_on="left_id",
        right_on="right_id",
    )

    assert len(result) == 2


def test_merge_missing_keys():
    left = pd.DataFrame({"a": [1]})
    right = pd.DataFrame({"b": [1]})

    with pytest.raises(ValueError):
        merge_data(left, right)


# ---------- Concatenation ----------

def test_concat_rows():
    df1 = pd.DataFrame({"a": [1, 2]})
    df2 = pd.DataFrame({"a": [3, 4]})

    result = concatenate_data([df1, df2])

    assert result["a"].tolist() == [1, 2, 3, 4]


def test_concat_columns():
    df1 = pd.DataFrame({"a": [1, 2]})
    df2 = pd.DataFrame({"b": [3, 4]})

    result = concatenate_data([df1, df2], axis=1)

    assert list(result.columns) == ["a", "b"]


def test_concat_empty_list():
    with pytest.raises(ValueError):
        concatenate_data([])


def test_concat_invalid_axis():
    df = pd.DataFrame({"a": [1]})

    with pytest.raises(ValueError):
        concatenate_data([df], axis=2)


# ---------- Safety ----------

def test_non_destructive_transformations():
    df = pd.DataFrame({
        "a": [3, 1, 2],
        "b": [10, 20, 30],
    })

    original = df.copy(deep=True)

    select_columns(df, ["a"])
    drop_columns(df, ["b"])
    filter_rows(df, {"a": (">", 1)})
    sort_data(df, "a")
    add_column(df, "c", [1, 2, 3])

    pd.testing.assert_frame_equal(df, original)


def test_invalid_dataframe():
    with pytest.raises(TypeError):
        select_columns([1, 2, 3], ["a"])
