
"""Non-destructive data quality analysis for Icebrew."""

import pandas as pd


def analyze_quality(df: pd.DataFrame) -> dict:
    """Analyze a DataFrame for common data quality issues."""

    if not isinstance(df, pd.DataFrame):
        raise TypeError("Expected a pandas DataFrame.")

    total_cells = df.size
    missing_total = int(df.isna().sum().sum())

    missing_percent = (
        float((missing_total / total_cells) * 100)
        if total_cells else 0.0
    )

    empty_rows = df.index[df.isna().all(axis=1)].tolist()
    empty_columns = [
        df.columns[i]
        for i in range(len(df.columns))
        if df.iloc[:, i].isna().all()
    ]

    duplicate_row_positions = (
        df.index[df.duplicated(keep="first")].tolist()
    )

    duplicate_rows_count = int(df.duplicated().sum())

    whitespace_only = []

    for i, column in enumerate(df.columns):
        series = df.iloc[:, i]

        whitespace_count = int(
            series.map(
                lambda value: isinstance(value, str)
                and value.strip() == ""
            ).sum()
        )

        if whitespace_count:
            whitespace_only.append({
                "column": column,
                "position": i,
                "count": whitespace_count,
            })

    duplicate_columns = [
        column
        for column in df.columns[df.columns.duplicated(keep="first")]
    ]

    column_quality = []

    for i, column in enumerate(df.columns):
        series = df.iloc[:, i]

        column_quality.append({
            "column": column,
            "position": i,
            "dtype": str(series.dtype),
            "missing": int(series.isna().sum()),
            "missing_percent": (
                float(series.isna().mean() * 100)
                if len(series) else 0.0
            ),
            "unique": int(series.nunique(dropna=True)),
        })

    return {
        "shape": df.shape,
        "total_cells": total_cells,
        "missing_total": missing_total,
        "missing_percent": missing_percent,
        "empty_rows": empty_rows,
        "empty_rows_count": len(empty_rows),
        "empty_columns": empty_columns,
        "empty_columns_count": len(empty_columns),
        "duplicate_rows": duplicate_rows_count,
        "duplicate_row_indices": duplicate_row_positions,
        "duplicate_columns": duplicate_columns,
        "duplicate_columns_count": len(duplicate_columns),
        "whitespace_only": whitespace_only,
        "whitespace_only_total": sum(
            item["count"] for item in whitespace_only
        ),
        "columns": column_quality,
    }
