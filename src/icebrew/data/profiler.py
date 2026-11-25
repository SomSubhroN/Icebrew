import pandas as pd


def profile_data(df: pd.DataFrame) -> dict:
    if not isinstance(df, pd.DataFrame):
        raise TypeError("Expected a pandas DataFrame.")

    profile = {}

    for column in df.columns:
        series = df[column]

        profile[column] = {
            "dtype": str(series.dtype),
            "count": int(series.count()),
            "missing": int(series.isna().sum()),
            "missing_percent": float(
                series.isna().mean() * 100
            ),
            "unique": int(series.nunique(dropna=True)),
        }

        if pd.api.types.is_numeric_dtype(series):
            profile[column].update({
                "mean": float(series.mean()) if series.count() else None,
                "median": float(series.median()) if series.count() else None,
                "std": float(series.std()) if series.count() > 1 else None,
                "min": series.min() if series.count() else None,
                "max": series.max() if series.count() else None,
            })

        elif pd.api.types.is_string_dtype(series) or series.dtype == object:
            profile[column]["top_values"] = (
                series.value_counts(dropna=True).head(5).to_dict()
            )

    return profile