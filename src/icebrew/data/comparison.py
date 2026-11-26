
from __future__ import annotations

from typing import Any

import pandas as pd


def _validate_dataframe(df: pd.DataFrame, name: str) -> None:
    if not isinstance(df, pd.DataFrame):
        raise TypeError(f"{name} must be a pandas DataFrame.")

    if df.columns.has_duplicates:
        raise ValueError(f"{name} contains duplicate column names.")


def _missing_percentage(series: pd.Series) -> float:
    if len(series) == 0:
        return 0.0
    return float(series.isna().mean() * 100)


def _numeric_summary(series: pd.Series) -> dict[str, Any]:
    numeric = pd.to_numeric(series, errors="coerce")
    numeric = numeric.dropna()

    if numeric.empty:
        return {
            "count": 0,
            "mean": None,
            "median": None,
            "std": None,
            "min": None,
            "max": None,
        }

    return {
        "count": int(numeric.count()),
        "mean": float(numeric.mean()),
        "median": float(numeric.median()),
        "std": float(numeric.std()) if numeric.count() > 1 else None,
        "min": float(numeric.min()),
        "max": float(numeric.max()),
    }


def _distribution(series: pd.Series, top_n: int) -> dict[str, Any]:
    counts = series.value_counts(dropna=False)

    total = len(series)
    entries = []

    for value, count in counts.head(top_n).items():
        label = "<NA>" if pd.isna(value) else str(value)

        entries.append(
            {
                "value": label,
                "count": int(count),
                "percentage": float(count / total * 100) if total else 0.0,
            }
        )

    return {
        "total": total,
        "unique": int(series.nunique(dropna=True)),
        "values": entries,
    }


def _column_comparison(
    left: pd.Series,
    right: pd.Series,
    *,
    top_n: int,
    include_distributions: bool,
) -> dict[str, Any]:
    result: dict[str, Any] = {
        "left": {
            "dtype": str(left.dtype),
            "count": int(left.count()),
            "missing": int(left.isna().sum()),
            "missing_percentage": _missing_percentage(left),
            "unique": int(left.nunique(dropna=True)),
        },
        "right": {
            "dtype": str(right.dtype),
            "count": int(right.count()),
            "missing": int(right.isna().sum()),
            "missing_percentage": _missing_percentage(right),
            "unique": int(right.nunique(dropna=True)),
        },
    }

    result["missing_difference"] = {
        "count": result["right"]["missing"] - result["left"]["missing"],
        "percentage_points": (
            result["right"]["missing_percentage"]
            - result["left"]["missing_percentage"]
        ),
    }

    if (
        pd.api.types.is_numeric_dtype(left)
        and pd.api.types.is_numeric_dtype(right)
    ):
        left_summary = _numeric_summary(left)
        right_summary = _numeric_summary(right)

        result["numeric"] = {
            "left": left_summary,
            "right": right_summary,
            "difference": {
                key: (
                    right_summary[key] - left_summary[key]
                    if left_summary[key] is not None
                    and right_summary[key] is not None
                    else None
                )
                for key in ("mean", "median", "std", "min", "max")
            },
        }

    if include_distributions:
        left_dist = _distribution(left, top_n)
        right_dist = _distribution(right, top_n)

        left_counts = {
            item["value"]: item["count"]
            for item in left_dist["values"]
        }
        right_counts = {
            item["value"]: item["count"]
            for item in right_dist["values"]
        }

        left_percentages = {
            item["value"]: item["percentage"]
            for item in left_dist["values"]
        }
        right_percentages = {
            item["value"]: item["percentage"]
            for item in right_dist["values"]
        }

        all_values = sorted(
            set(left_counts) | set(right_counts)
        )

        distribution_changes = {}

        for value in all_values:
            distribution_changes[value] = {
                "left_count": left_counts.get(value, 0),
                "right_count": right_counts.get(value, 0),
                "count_difference": (
                    right_counts.get(value, 0)
                    - left_counts.get(value, 0)
                ),
                "left_percentage": left_percentages.get(value, 0.0),
                "right_percentage": right_percentages.get(value, 0.0),
                "percentage_point_difference": (
                    right_percentages.get(value, 0.0)
                    - left_percentages.get(value, 0.0)
                ),
            }

        result["distribution"] = {
            "left": left_dist,
            "right": right_dist,
            "changes": distribution_changes,
        }

    return result


def _row_comparison(
    left: pd.DataFrame,
    right: pd.DataFrame,
    common_columns: list[str],
) -> dict[str, Any]:
    rows_compared = min(len(left), len(right))

    left_aligned = left.iloc[:rows_compared][common_columns].reset_index(drop=True)
    right_aligned = right.iloc[:rows_compared][common_columns].reset_index(drop=True)

    differences = {}

    for column in common_columns:
        left_series = left_aligned[column]
        right_series = right_aligned[column]

        equal = left_series.eq(right_series) | (
            left_series.isna() & right_series.isna()
        )

        differences[column] = {
            "different_cells": int((~equal).sum()),
            "equal_cells": int(equal.sum()),
        }

    total_cells = rows_compared * len(common_columns)
    differing_cells = sum(
        details["different_cells"]
        for details in differences.values()
    )

    differing_rows = 0

    if rows_compared and common_columns:
        row_equal = (
            left_aligned.eq(right_aligned)
            | (left_aligned.isna() & right_aligned.isna())
        ).all(axis=1)

        differing_rows = int((~row_equal).sum())

    return {
        "alignment": "positional",
        "rows_compared": rows_compared,
        "columns_compared": len(common_columns),
        "differing_rows": differing_rows,
        "different_cells": differing_cells,
        "total_cells": total_cells,
        "cell_difference_percentage": (
            float(differing_cells / total_cells * 100)
            if total_cells
            else 0.0
        ),
        "columns": differences,
        "warning": (
            "Rows were compared by position, not by a primary key. "
            "This comparison does not establish record identity."
        ),
    }


def compare_datasets(
    left: pd.DataFrame,
    right: pd.DataFrame,
    *,
    top_n: int = 10,
    include_distributions: bool = True,
    compare_rows: bool = False,
) -> dict[str, Any]:
    """Compare two datasets descriptively without modifying either dataset."""

    _validate_dataframe(left, "left")
    _validate_dataframe(right, "right")

    if top_n < 1:
        raise ValueError("top_n must be at least 1.")

    left_columns = list(left.columns)
    right_columns = list(right.columns)

    common_columns = [
        column for column in left_columns
        if column in right_columns
    ]

    left_only = [
        column for column in left_columns
        if column not in right_columns
    ]

    right_only = [
        column for column in right_columns
        if column not in left_columns
    ]

    schema = {
        "left_columns": left_columns,
        "right_columns": right_columns,
        "common_columns": common_columns,
        "left_only_columns": left_only,
        "right_only_columns": right_only,
        "column_order_identical": left_columns == right_columns,
        "column_names_identical": set(left_columns) == set(right_columns),
        "dtype_differences": {
            column: {
                "left": str(left[column].dtype),
                "right": str(right[column].dtype),
            }
            for column in common_columns
            if str(left[column].dtype) != str(right[column].dtype)
        },
    }

    columns = {}

    for column in common_columns:
        columns[column] = _column_comparison(
            left[column],
            right[column],
            top_n=top_n,
            include_distributions=include_distributions,
        )

    summary = {
        "left_shape": tuple(left.shape),
        "right_shape": tuple(right.shape),
        "row_difference": len(right) - len(left),
        "column_difference": len(right.columns) - len(left.columns),
        "left_duplicate_rows": int(left.duplicated().sum()),
        "right_duplicate_rows": int(right.duplicated().sum()),
        "common_column_count": len(common_columns),
        "left_only_column_count": len(left_only),
        "right_only_column_count": len(right_only),
    }

    report: dict[str, Any] = {
        "summary": summary,
        "schema": schema,
        "columns": columns,
    }

    if compare_rows:
        report["row_comparison"] = _row_comparison(
            left,
            right,
            common_columns,
        )

    return report
