"""Sampling and dataset splitting utilities for Icebrew."""

import pandas as pd


def sample_data(
    df: pd.DataFrame,
    *,
    n: int | None = None,
    fraction: float | None = None,
    random_state: int | None = None,
    replace: bool = False,
) -> pd.DataFrame:
    """Randomly sample rows from a DataFrame."""

    if not isinstance(df, pd.DataFrame):
        raise TypeError("Expected a pandas DataFrame.")

    if n is not None and fraction is not None:
        raise ValueError("Specify either n or fraction, not both.")

    if n is None and fraction is None:
        raise ValueError("Specify n or fraction.")

    if n is not None:
        if isinstance(n, bool) or not isinstance(n, int):
            raise TypeError("n must be an integer.")
        if n < 0:
            raise ValueError("n cannot be negative.")
        if n > len(df) and not replace:
            raise ValueError("n cannot exceed dataset size without replacement.")

    if fraction is not None:
        if isinstance(fraction, bool) or not isinstance(fraction, (int, float)):
            raise TypeError("fraction must be numeric.")
        if not 0 <= fraction <= 1:
            raise ValueError("fraction must be between 0 and 1.")

    if not isinstance(replace, bool):
        raise TypeError("replace must be a boolean.")

    return df.sample(
        n=n,
        frac=fraction,
        replace=replace,
        random_state=random_state,
    ).copy()


def stratified_sample(
    df: pd.DataFrame,
    column: str,
    *,
    n: int | None = None,
    fraction: float | None = None,
    random_state: int | None = None,
) -> pd.DataFrame:
    """Sample proportionally from each category of a column."""

    if not isinstance(df, pd.DataFrame):
        raise TypeError("Expected a pandas DataFrame.")

    if column not in df.columns:
        raise KeyError(f"Column not found: {column}")

    if n is not None and fraction is not None:
        raise ValueError("Specify either n or fraction, not both.")

    if n is None and fraction is None:
        raise ValueError("Specify n or fraction.")

    if n is not None:
        if isinstance(n, bool) or not isinstance(n, int):
            raise TypeError("n must be an integer.")
        if n < 0 or n > len(df):
            raise ValueError("n must be between 0 and dataset size.")

        fraction = n / len(df) if len(df) else 0.0

    if fraction is not None:
        if isinstance(fraction, bool) or not isinstance(fraction, (int, float)):
            raise TypeError("fraction must be numeric.")
        if not 0 <= fraction <= 1:
            raise ValueError("fraction must be between 0 and 1.")

    # Stratification cannot preserve a category containing only missing values
    # with dropna=True, so missing strata are explicitly rejected.
    if df[column].isna().any():
        raise ValueError(
            "Stratified sampling requires non-missing values "
            "in the stratification column."
        )

    result = (
        df.groupby(column, group_keys=False, observed=True)
        .sample(frac=fraction, random_state=random_state)
    )

    return result.copy()


def split_data(
    df: pd.DataFrame,
    *,
    test_size: float = 0.2,
    random_state: int | None = None,
    shuffle: bool = True,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Split a DataFrame into train and test datasets."""

    if not isinstance(df, pd.DataFrame):
        raise TypeError("Expected a pandas DataFrame.")

    if isinstance(test_size, bool) or not isinstance(test_size, (int, float)):
        raise TypeError("test_size must be numeric.")

    if not 0 < test_size < 1:
        raise ValueError("test_size must be between 0 and 1.")

    if not isinstance(shuffle, bool):
        raise TypeError("shuffle must be a boolean.")

    if len(df) < 2:
        raise ValueError("Dataset must contain at least two rows.")

    if shuffle:
        shuffled = df.sample(frac=1, random_state=random_state)
    else:
        shuffled = df.copy()

    test_count = max(1, round(len(df) * test_size))
    test_count = min(test_count, len(df) - 1)

    test_df = shuffled.iloc[:test_count].copy()
    train_df = shuffled.iloc[test_count:].copy()

    return train_df, test_df