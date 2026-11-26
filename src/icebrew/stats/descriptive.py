
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats

from icebrew.stats.utils import validate_numeric_series


def describe_numeric(
    data,
    *,
    quantiles=(0.25, 0.50, 0.75),
    ddof=1,
) -> dict:
    """Calculate descriptive statistics for numeric data."""
    series = validate_numeric_series(data)
    values = series.to_numpy(dtype=float)

    if isinstance(ddof, bool) or not isinstance(ddof, int):
        raise TypeError("ddof must be an integer.")

    if ddof < 0:
        raise ValueError("ddof must be non-negative.")

    if len(values) <= ddof:
        raise ValueError("Insufficient observations for the requested ddof.")

    quantiles = tuple(quantiles)

    if any(not 0 <= q <= 1 for q in quantiles):
        raise ValueError("Quantiles must be between 0 and 1.")

    q_values = series.quantile(quantiles)

    result = {
        "count": int(len(values)),
        "mean": float(np.mean(values)),
        "median": float(np.median(values)),
        "minimum": float(np.min(values)),
        "maximum": float(np.max(values)),
        "range": float(np.ptp(values)),
        "variance": float(np.var(values, ddof=ddof)),
        "std": float(np.std(values, ddof=ddof)),
        "sem": float(stats.sem(values, ddof=ddof)),
        "skewness": float(stats.skew(values, bias=False)),
        "kurtosis": float(stats.kurtosis(values, bias=False)),
        "sum": float(np.sum(values)),
    }

    for q, value in zip(quantiles, q_values):
        result[f"q{q:g}"] = float(value)

    return result


def describe_dataframe(
    df: pd.DataFrame,
    *,
    columns=None,
    quantiles=(0.25, 0.50, 0.75),
    ddof=1,
) -> dict:
    """Describe numeric columns of a DataFrame."""
    if not isinstance(df, pd.DataFrame):
        raise TypeError("df must be a pandas DataFrame.")

    if df.columns.duplicated().any():
        raise ValueError("Duplicate column names are not supported.")

    if columns is None:
        columns = df.select_dtypes(include="number").columns.tolist()

    if not columns:
        raise ValueError("No numeric columns selected.")

    missing_columns = [c for c in columns if c not in df.columns]
    if missing_columns:
        raise KeyError(f"Unknown columns: {missing_columns}")

    results = {}

    for column in columns:
        if not pd.api.types.is_numeric_dtype(df[column]):
            raise TypeError(f"Column {column!r} is not numeric.")

        results[column] = describe_numeric(
            df[column],
            quantiles=quantiles,
            ddof=ddof,
        )

    return results
