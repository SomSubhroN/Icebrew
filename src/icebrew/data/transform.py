
"""Data transformation utilities for Icebrew."""

from collections.abc import Callable

import pandas as pd


def select_columns(
    df: pd.DataFrame,
    columns: list[str],
) -> pd.DataFrame:
    """Select specified columns."""

    _validate_dataframe(df)

    missing = [column for column in columns if column not in df.columns]

    if missing:
        raise KeyError(f"Columns not found: {missing}")

    return df.loc[:, columns].copy()


def drop_columns(
    df: pd.DataFrame,
    columns: list[str],
) -> pd.DataFrame:
    """Drop specified columns."""

    _validate_dataframe(df)

    missing = [column for column in columns if column not in df.columns]

    if missing:
        raise KeyError(f"Columns not found: {missing}")

    return df.drop(columns=columns).copy()


def filter_rows(
    df: pd.DataFrame,
    conditions: dict,
) -> pd.DataFrame:
    """Filter rows using conditions combined with logical AND.

    Supported operators:
        ==, !=, >, >=, <, <=, in, not_in,
        contains, startswith, endswith, isna, notna

    Examples:
        {"age": (">=", 18)}
        {"category": ("in", ["A", "B"])}
        {"name": ("contains", "Smith")}
        {"score": ("isna", None)}
    """

    _validate_dataframe(df)

    result_mask = pd.Series(True, index=df.index)

    for column, condition in conditions.items():

        if column not in df.columns:
            raise KeyError(f"Column not found: {column}")

        if not isinstance(condition, tuple) or len(condition) != 2:
            raise ValueError(
                f"Condition for '{column}' must be an "
                "operator-value tuple."
            )

        operator, value = condition
        series = df[column]

        if operator == "==":
            mask = series == value

        elif operator == "!=":
            mask = series != value

        elif operator == ">":
            mask = series > value

        elif operator == ">=":
            mask = series >= value

        elif operator == "<":
            mask = series < value

        elif operator == "<=":
            mask = series <= value

        elif operator == "in":
            mask = series.isin(value)

        elif operator == "not_in":
            mask = ~series.isin(value)

        elif operator == "contains":
            mask = series.astype("string").str.contains(
                value, na=False, regex=False
            )

        elif operator == "startswith":
            mask = series.astype("string").str.startswith(
                value, na=False
            )

        elif operator == "endswith":
            mask = series.astype("string").str.endswith(
                value, na=False
            )

        elif operator == "isna":
            mask = series.isna()

        elif operator == "notna":
            mask = series.notna()

        else:
            raise ValueError(f"Unsupported filter operator: {operator}")

        result_mask &= mask.fillna(False)

    return df.loc[result_mask].copy()


def sort_data(
    df: pd.DataFrame,
    by: str | list[str],
    ascending: bool | list[bool] = True,
) -> pd.DataFrame:
    """Sort rows by one or more columns."""

    _validate_dataframe(df)

    sort_columns = [by] if isinstance(by, str) else by

    missing = [column for column in sort_columns if column not in df.columns]

    if missing:
        raise KeyError(f"Columns not found: {missing}")

    return df.sort_values(
        by=by,
        ascending=ascending,
    ).copy()


def add_column(
    df: pd.DataFrame,
    name: str,
    values: list | pd.Series | Callable[[pd.DataFrame], object],
) -> pd.DataFrame:
    """Add a derived column using values or a callable."""

    _validate_dataframe(df)

    result = df.copy(deep=True)

    if callable(values):
        computed = values(result.copy(deep=True))

        if not isinstance(computed, (pd.Series, list)):
            raise TypeError(
                "Callable must return a pandas Series or list."
            )

        if isinstance(computed, pd.Series):
            if not computed.index.equals(result.index):
                raise ValueError(
                    "Returned Series must have the same index as the DataFrame."
                )

        if len(computed) != len(result):
            raise ValueError(
                "Computed column length must match DataFrame length."
            )

        result[name] = computed

    else:
        if len(values) != len(result):
            raise ValueError(
                "Values length must match DataFrame length."
            )

        result[name] = values

    return result


def group_aggregate(
    df: pd.DataFrame,
    by: str | list[str],
    aggregations: dict,
) -> pd.DataFrame:
    """Group rows and apply specified aggregations."""

    _validate_dataframe(df)

    group_columns = [by] if isinstance(by, str) else by

    missing = [
        column
        for column in group_columns + list(aggregations.keys())
        if column not in df.columns
    ]

    if missing:
        raise KeyError(f"Columns not found: {missing}")

    if not aggregations:
        raise ValueError("At least one aggregation is required.")

    return (
        df.groupby(by, dropna=False)
        .agg(aggregations)
        .reset_index()
    )


def merge_data(
    left: pd.DataFrame,
    right: pd.DataFrame,
    *,
    on: str | list[str] | None = None,
    left_on: str | list[str] | None = None,
    right_on: str | list[str] | None = None,
    how: str = "inner",
    suffixes: tuple[str, str] = ("_x", "_y"),
) -> pd.DataFrame:
    """Merge two DataFrames."""

    _validate_dataframe(left)
    _validate_dataframe(right)

    if on is None and (left_on is None or right_on is None):
        raise ValueError(
            "Specify 'on' or both 'left_on' and 'right_on'."
        )

    return pd.merge(
        left.copy(),
        right.copy(),
        on=on,
        left_on=left_on,
        right_on=right_on,
        how=how,
        suffixes=suffixes,
    )


def concatenate_data(
    frames: list[pd.DataFrame],
    *,
    axis: int = 0,
    ignore_index: bool = True,
) -> pd.DataFrame:
    """Concatenate multiple DataFrames."""

    if not isinstance(frames, list) or not frames:
        raise ValueError("Provide a non-empty list of DataFrames.")

    for frame in frames:
        _validate_dataframe(frame)

    if axis not in (0, 1):
        raise ValueError("axis must be 0 or 1.")

    # Ignore row indexes when stacking rows, not column labels.
    return pd.concat(
        [frame.copy() for frame in frames],
        axis=axis,
        ignore_index=ignore_index if axis == 0 else False,
    )

def _validate_dataframe(df: pd.DataFrame) -> None:
    """Validate DataFrame input."""

    if not isinstance(df, pd.DataFrame):
        raise TypeError("Expected a pandas DataFrame.")
