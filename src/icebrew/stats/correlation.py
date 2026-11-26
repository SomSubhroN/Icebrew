
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats


_SUPPORTED_METHODS = {
    "pearson": stats.pearsonr,
    "spearman": stats.spearmanr,
    "kendall": stats.kendalltau,
}


def correlation(
    x,
    y,
    *,
    method: str = "pearson",
    nan_policy: str = "pairwise",
) -> dict:
    """Calculate correlation between two numeric variables.

    Parameters
    ----------
    x, y : array-like
        Numeric observations of equal length.
    method : {"pearson", "spearman", "kendall"}
        Correlation method.
    nan_policy : {"pairwise", "raise"}
        Pairwise removal of missing/infinite values or raise an error.

    Returns
    -------
    dict
        Correlation coefficient, p-value, sample size and method.
    """
    if method not in _SUPPORTED_METHODS:
        raise ValueError(
            "method must be one of: pearson, spearman, kendall."
        )

    if nan_policy not in {"pairwise", "raise"}:
        raise ValueError("nan_policy must be 'pairwise' or 'raise'.")

    if isinstance(x, pd.DataFrame) or isinstance(y, pd.DataFrame):
        raise TypeError("x and y must be one-dimensional inputs.")

    try:
        x = pd.Series(x).reset_index(drop=True)
        y = pd.Series(y).reset_index(drop=True)
    except Exception as exc:
        raise TypeError("x and y must be array-like.") from exc

    if len(x) != len(y):
        raise ValueError("x and y must have equal lengths.")

    if not pd.api.types.is_numeric_dtype(x):
        raise TypeError("x must contain numeric data.")

    if not pd.api.types.is_numeric_dtype(y):
        raise TypeError("y must contain numeric data.")

    pair = pd.DataFrame({"x": x, "y": y})

    pair = pair.replace(
        [np.inf, -np.inf],
        np.nan,
    )

    if nan_policy == "raise" and pair.isna().any().any():
        raise ValueError("Missing or infinite values detected.")

    if nan_policy == "pairwise":
        pair = pair.dropna()

    if len(pair) < 2:
        raise ValueError(
            "At least two valid paired observations are required."
        )

    if pair["x"].nunique() < 2 or pair["y"].nunique() < 2:
        raise ValueError(
            "Both variables must contain at least two distinct values."
        )

    result = _SUPPORTED_METHODS[method](
        pair["x"].to_numpy(dtype=float),
        pair["y"].to_numpy(dtype=float),
    )

    coefficient = float(result.statistic)
    p_value = float(result.pvalue)

    if not np.isfinite(coefficient):
        raise ValueError("Correlation coefficient is not finite.")

    return {
        "method": method,
        "coefficient": coefficient,
        "p_value": p_value,
        "n": int(len(pair)),
        "nan_policy": nan_policy,
    }


def correlation_matrix(
    df: pd.DataFrame,
    *,
    columns=None,
    method: str = "pearson",
):
    """Calculate a correlation matrix for numeric DataFrame columns."""
    if not isinstance(df, pd.DataFrame):
        raise TypeError("df must be a pandas DataFrame.")

    if df.columns.duplicated().any():
        raise ValueError("Duplicate column names are not supported.")

    if method not in {"pearson", "spearman", "kendall"}:
        raise ValueError(
            "method must be one of: pearson, spearman, kendall."
        )

    if columns is None:
        columns = df.select_dtypes(include="number").columns.tolist()
    else:
        columns = list(columns)

    if len(columns) < 2:
        raise ValueError("At least two columns are required.")

    if len(set(columns)) != len(columns):
        raise ValueError("Duplicate column selections are not allowed.")

    missing_columns = [c for c in columns if c not in df.columns]

    if missing_columns:
        raise KeyError(f"Unknown columns: {missing_columns}")

    selected = df.loc[:, columns]

    non_numeric = [
        c for c in columns
        if not pd.api.types.is_numeric_dtype(selected[c])
    ]

    if non_numeric:
        raise TypeError(
            f"Non-numeric columns selected: {non_numeric}"
        )

    selected = selected.replace(
        [np.inf, -np.inf],
        np.nan,
    )

    return selected.corr(method=method)
