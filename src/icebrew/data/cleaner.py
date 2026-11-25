
"""Non-destructive data cleaning utilities for Icebrew."""

import pandas as pd


def clean_data(
    df: pd.DataFrame,
    *,
    drop_duplicates: bool = False,
    drop_empty_rows: bool = False,
    drop_empty_columns: bool = False,
    trim_whitespace: bool = False,
    replace_values: dict | None = None,
    normalize_missing: list | None = None,
    rename_columns: dict | None = None,
) -> pd.DataFrame:
    """Clean a DataFrame using explicitly selected operations."""

    if not isinstance(df, pd.DataFrame):
        raise TypeError("Expected a pandas DataFrame.")

    result = df.copy(deep=True)

    # Normalize selected missing-value representations.
    if normalize_missing is not None:
        result = result.replace(normalize_missing, pd.NA)

    # Trim leading and trailing whitespace from string cells.
    if trim_whitespace:
        result = result.map(
            lambda value: value.strip()
            if isinstance(value, str)
            else value
        )

    # Replace selected values.
    if replace_values is not None:
        if not isinstance(replace_values, dict):
            raise TypeError("replace_values must be a dictionary.")

        result = result.replace(replace_values)

    # Rename columns.
    if rename_columns is not None:
        if not isinstance(rename_columns, dict):
            raise TypeError("rename_columns must be a dictionary.")

        result = result.rename(columns=rename_columns)

    # Remove fully empty rows.
    if drop_empty_rows:
        result = result.dropna(how="all")

    # Remove fully empty columns.
    if drop_empty_columns:
        result = result.dropna(axis=1, how="all")

    # Remove duplicate rows.
    if drop_duplicates:
        result = result.drop_duplicates()

    return result
