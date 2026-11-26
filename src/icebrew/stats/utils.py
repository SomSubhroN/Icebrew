
from __future__ import annotations

import numpy as np
import pandas as pd


def validate_numeric_series(
    data,
    *,
    name: str = "data",
    drop_missing: bool = True,
) -> pd.Series:
    """Validate and return a numeric Series."""
    if isinstance(data, pd.DataFrame):
        raise TypeError(
            f"{name} must be a Series or 1D array, not a DataFrame."
        )

    if isinstance(data, pd.Series):
        series = data.copy()
    else:
        try:
            series = pd.Series(data, name=name)
        except Exception as exc:
            raise TypeError(
                f"{name} must be convertible to a Series."
            ) from exc

    if series.empty:
        raise ValueError(f"{name} contains no observations.")

    if not pd.api.types.is_numeric_dtype(series):
        raise TypeError(f"{name} must contain numeric data.")

    series = series.replace([np.inf, -np.inf], np.nan)

    if drop_missing:
        series = series.dropna()
    elif series.isna().any():
        raise ValueError(
            f"{name} contains missing or infinite values."
        )

    if len(series) == 0:
        raise ValueError(f"{name} contains no valid observations.")

    return series


def validate_confidence_level(confidence: float) -> float:
    """Validate a confidence level."""
    if isinstance(confidence, bool) or not isinstance(
        confidence, (int, float)
    ):
        raise TypeError("confidence must be numeric.")

    if not 0 < confidence < 1:
        raise ValueError(
            "confidence must be strictly between 0 and 1."
        )

    return float(confidence)


def validate_sample_size(n: int) -> int:
    """Validate sample size."""
    if isinstance(n, bool) or not isinstance(n, (int, np.integer)):
        raise TypeError("Sample size must be an integer.")

    if n < 1:
        raise ValueError("Sample size must be at least 1.")

    return int(n)
