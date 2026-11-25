import pandas as pd


def inspect_data(df: pd.DataFrame, preview_rows: int = 5) -> dict:
    if not isinstance(df, pd.DataFrame):
        raise TypeError("Expected a pandas DataFrame.")

    if preview_rows < 0:
        raise ValueError("preview_rows cannot be negative.")

    return {
        "shape": df.shape,
        "columns": list(df.columns),
        "dtypes": df.dtypes.astype(str).to_dict(),
        "missing_values": df.isna().sum().to_dict(),
        "duplicates": int(df.duplicated().sum()),
        "memory_usage_bytes": int(
            df.memory_usage(index=True, deep=True).sum()
        ),
        "preview": df.head(preview_rows).to_dict(orient="records"),
    }