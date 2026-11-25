
"""Missing data analysis and handling utilities for Icebrew."""

import pandas as pd


def analyze_missing(df: pd.DataFrame) -> dict:
    """Generate a missing-data report without modifying the DataFrame."""

    if not isinstance(df, pd.DataFrame):
        raise TypeError("Expected a pandas DataFrame.")

    total_cells = df.size
    missing_total = int(df.isna().sum().sum())

    columns = {}

    for position, column in enumerate(df.columns):
        series = df.iloc[:, position]
        missing = int(series.isna().sum())

        columns[column] = {
            "missing": missing,
            "missing_percent": (
                float(missing / len(df) * 100)
                if len(df) else 0.0
            ),
            "present": int(series.notna().sum()),
        }

    rows_with_missing = {}

    for position, index in enumerate(df.index):
        missing_count = int(df.iloc[position].isna().sum())

        if missing_count:
            rows_with_missing[index] = missing_count

    return {
        "shape": df.shape,
        "total_cells": total_cells,
        "missing_total": missing_total,
        "missing_percent": (
            float(missing_total / total_cells * 100)
            if total_cells else 0.0
        ),
        "columns": columns,
        "rows_with_missing": rows_with_missing,
        "rows_with_missing_count": len(rows_with_missing),
    }


def handle_missing(
    df: pd.DataFrame,
    *,
    drop_rows_threshold: float | None = None,
    drop_columns_threshold: float | None = None,
    impute: dict | None = None,
) -> pd.DataFrame:
    """Handle missing values through explicitly selected operations.

    Thresholds are percentages from 0 to 100.

    Row dropping:
        Drops rows strictly above the specified missingness threshold.

    Column dropping:
        Drops columns at or above the specified missingness threshold.

    Supported methods:
        mean, median, mode, ffill, bfill

    Constant imputation:
        {"column": {"method": "constant", "value": X}}

    Literal-value imputation:
        {"column": X}
    """

    if not isinstance(df, pd.DataFrame):
        raise TypeError("Expected a pandas DataFrame.")

    for name, threshold in (
        ("drop_rows_threshold", drop_rows_threshold),
        ("drop_columns_threshold", drop_columns_threshold),
    ):
        if threshold is not None:
            if isinstance(threshold, bool) or not isinstance(
                threshold, (int, float)
            ):
                raise TypeError(f"{name} must be numeric.")

            if not 0 <= threshold <= 100:
                raise ValueError(f"{name} must be between 0 and 100.")

    if impute is not None and not isinstance(impute, dict):
        raise TypeError("impute must be a dictionary.")

    result = df.copy(deep=True)

    # Drop columns at or above the missingness threshold.
    if drop_columns_threshold is not None and len(result):
        column_missing_percent = result.isna().mean() * 100

        columns_to_drop = column_missing_percent[
            column_missing_percent >= drop_columns_threshold
        ].index

        result = result.drop(columns=columns_to_drop)

    # Drop rows strictly above the missingness threshold.
    if drop_rows_threshold is not None and len(result.columns):
        row_missing_percent = result.isna().mean(axis=1) * 100

        rows_to_drop = row_missing_percent[
            row_missing_percent > drop_rows_threshold
        ].index

        result = result.drop(index=rows_to_drop)

    # Explicit imputation.
    if impute is not None:
        for column, strategy in impute.items():

            if column not in result.columns:
                raise KeyError(f"Column not found: {column}")

            series = result[column]

            # Explicit constant imputation.
            if isinstance(strategy, dict):
                if strategy.get("method") != "constant":
                    raise ValueError(
                        "Dictionary imputation supports "
                        "only the 'constant' method."
                    )

                if "value" not in strategy:
                    raise ValueError(
                        "Constant imputation requires a value."
                    )

                result[column] = series.fillna(strategy["value"])
                continue

            # Statistical or propagation-based methods.
            if isinstance(strategy, str):

                if strategy == "mean":
                    if not pd.api.types.is_numeric_dtype(series):
                        raise TypeError(
                            f"Mean imputation requires numeric data: {column}"
                        )

                    result[column] = series.fillna(series.mean())

                elif strategy == "median":
                    if not pd.api.types.is_numeric_dtype(series):
                        raise TypeError(
                            f"Median imputation requires numeric data: {column}"
                        )

                    result[column] = series.fillna(series.median())

                elif strategy == "mode":
                    modes = series.mode(dropna=True)

                    if not modes.empty:
                        result[column] = series.fillna(modes.iloc[0])

                elif strategy == "ffill":
                    result[column] = series.ffill()

                elif strategy == "bfill":
                    result[column] = series.bfill()

                else:
                    raise ValueError(
                        f"Unknown imputation method: {strategy}"
                    )

            else:
                # Literal-value imputation.
                result[column] = series.fillna(strategy)

    return result
