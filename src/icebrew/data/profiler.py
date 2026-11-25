"""Dataset profiling utilities for Icebrew."""

import pandas as pd


def profile_data(
    df: pd.DataFrame,
    *,
    top_n: int = 5,
    include_quantiles: bool = True,
) -> dict:
    """Generate a comprehensive profile without modifying the DataFrame."""

    if not isinstance(df, pd.DataFrame):
        raise TypeError("Expected a pandas DataFrame.")

    if isinstance(top_n, bool) or not isinstance(top_n, int):
        raise TypeError("top_n must be an integer.")

    if top_n < 0:
        raise ValueError("top_n cannot be negative.")

    profile = {}

    for position, column in enumerate(df.columns):
        series = df.iloc[:, position]
        count = int(series.count())
        missing = int(series.isna().sum())

        column_profile = {
            "position": position,
            "dtype": str(series.dtype),
            "count": count,
            "missing": missing,
            "missing_percent": float(series.isna().mean() * 100),
            "unique": int(series.nunique(dropna=True)),
        }

        if pd.api.types.is_numeric_dtype(series):
            column_profile.update({
                "mean": float(series.mean()) if count else None,
                "median": float(series.median()) if count else None,
                "std": float(series.std()) if count > 1 else None,
                "min": series.min() if count else None,
                "max": series.max() if count else None,
            })

            if include_quantiles and count:
                quantiles = series.quantile([0.25, 0.5, 0.75])
                column_profile["quantiles"] = {
                    str(q): float(value)
                    for q, value in quantiles.items()
                }

        else:
            if count:
                frequencies = series.value_counts(dropna=True).head(top_n)
                column_profile["top_values"] = frequencies.to_dict()
            else:
                column_profile["top_values"] = {}

        profile[column] = column_profile

    return profile