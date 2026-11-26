
import pandas as pd
import pytest

from icebrew.data.comparison import compare_datasets


def test_basic_comparison():
    left = pd.DataFrame({"a": [1, 2, 3], "b": ["x", "y", "x"]})
    right = pd.DataFrame({"a": [1, 4, 3], "b": ["x", "z", "x"]})

    report = compare_datasets(left, right)

    assert report["summary"]["left_shape"] == (3, 2)
    assert report["summary"]["right_shape"] == (3, 2)
    assert report["schema"]["common_columns"] == ["a", "b"]


def test_row_difference():
    left = pd.DataFrame({"a": [1, 2]})
    right = pd.DataFrame({"a": [1, 2, 3]})

    report = compare_datasets(left, right)

    assert report["summary"]["row_difference"] == 1


def test_column_difference():
    left = pd.DataFrame({"a": [1], "b": [2]})
    right = pd.DataFrame({"a": [1], "c": [3]})

    report = compare_datasets(left, right)

    assert report["schema"]["left_only_columns"] == ["b"]
    assert report["schema"]["right_only_columns"] == ["c"]


def test_dtype_difference():
    left = pd.DataFrame({"a": [1, 2]})
    right = pd.DataFrame({"a": ["1", "2"]})

    report = compare_datasets(left, right)

    assert "a" in report["schema"]["dtype_differences"]


def test_missing_values():
    left = pd.DataFrame({"a": [1, None, 3]})
    right = pd.DataFrame({"a": [1, 2, None]})

    report = compare_datasets(left, right)

    details = report["columns"]["a"]

    assert details["left"]["missing"] == 1
    assert details["right"]["missing"] == 1
    assert details["missing_difference"]["count"] == 0


def test_missing_percentage_difference():
    left = pd.DataFrame({"a": [1, None, 3, 4]})
    right = pd.DataFrame({"a": [None, None, 3, 4]})

    report = compare_datasets(left, right)

    assert report["columns"]["a"]["missing_difference"]["percentage_points"] == 25.0


def test_numeric_statistics():
    left = pd.DataFrame({"a": [1, 2, 3]})
    right = pd.DataFrame({"a": [2, 4, 6]})

    report = compare_datasets(left, right)

    numeric = report["columns"]["a"]["numeric"]

    assert numeric["left"]["mean"] == 2.0
    assert numeric["right"]["mean"] == 4.0
    assert numeric["difference"]["mean"] == 2.0


def test_numeric_std_single_value():
    left = pd.DataFrame({"a": [5]})
    right = pd.DataFrame({"a": [10]})

    report = compare_datasets(left, right)

    assert report["columns"]["a"]["numeric"]["left"]["std"] is None


def test_distribution_comparison():
    left = pd.DataFrame({"category": ["a", "a", "b"]})
    right = pd.DataFrame({"category": ["a", "b", "b"]})

    report = compare_datasets(left, right)

    changes = report["columns"]["category"]["distribution"]["changes"]

    assert changes["a"]["count_difference"] == -1
    assert changes["b"]["count_difference"] == 1


def test_distribution_disabled():
    left = pd.DataFrame({"category": ["a", "b"]})
    right = pd.DataFrame({"category": ["a", "c"]})

    report = compare_datasets(
        left,
        right,
        include_distributions=False,
    )

    assert "distribution" not in report["columns"]["category"]


def test_top_n_validation():
    left = pd.DataFrame({"a": [1]})
    right = pd.DataFrame({"a": [1]})

    with pytest.raises(ValueError):
        compare_datasets(left, right, top_n=0)


def test_non_dataframe_validation():
    with pytest.raises(TypeError):
        compare_datasets([1, 2], pd.DataFrame({"a": [1]}))


def test_duplicate_column_validation():
    left = pd.DataFrame([[1, 2]], columns=["a", "a"])
    right = pd.DataFrame({"a": [1]})

    with pytest.raises(ValueError):
        compare_datasets(left, right)


def test_row_comparison():
    left = pd.DataFrame({"a": [1, 2], "b": ["x", "y"]})
    right = pd.DataFrame({"a": [1, 3], "b": ["x", "z"]})

    report = compare_datasets(left, right, compare_rows=True)

    row_report = report["row_comparison"]

    assert row_report["rows_compared"] == 2
    assert row_report["differing_rows"] == 1
    assert row_report["different_cells"] == 2


def test_row_comparison_different_lengths():
    left = pd.DataFrame({"a": [1, 2, 3]})
    right = pd.DataFrame({"a": [1, 2]})

    report = compare_datasets(left, right, compare_rows=True)

    assert report["row_comparison"]["rows_compared"] == 2


def test_row_comparison_missing_values():
    left = pd.DataFrame({"a": [1, None]})
    right = pd.DataFrame({"a": [1, None]})

    report = compare_datasets(left, right, compare_rows=True)

    assert report["row_comparison"]["differing_rows"] == 0


def test_non_mutation():
    left = pd.DataFrame({"a": [1, 2], "b": ["x", "y"]})
    right = pd.DataFrame({"a": [3, 4], "b": ["z", "w"]})

    left_original = left.copy(deep=True)
    right_original = right.copy(deep=True)

    compare_datasets(left, right, compare_rows=True)

    pd.testing.assert_frame_equal(left, left_original)
    pd.testing.assert_frame_equal(right, right_original)


def test_column_order_difference():
    left = pd.DataFrame({"a": [1], "b": [2]})
    right = pd.DataFrame({"b": [2], "a": [1]})

    report = compare_datasets(left, right)

    assert report["schema"]["column_names_identical"]
    assert not report["schema"]["column_order_identical"]
