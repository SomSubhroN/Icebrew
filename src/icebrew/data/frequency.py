
"""Frequency analysis and crosstabulation utilities for Icebrew."""

from collections.abc import Sequence

import pandas as pd


def _validate_dataframe(df: pd.DataFrame) -> None:
    if not isinstance(df, pd.DataFrame):
        raise TypeError("Expected a pandas DataFrame.")

    if df.columns.duplicated().any():
        raise ValueError("DataFrame contains duplicate column names.")


def _validate_column(df: pd.DataFrame, column: str) -> None:
    if column not in df.columns:
        raise KeyError(f"Column not found: {column}")


def value_counts(
    df: pd.DataFrame,
    column: str,
    *,
    normalize: bool = False,
    dropna: bool = True,
    sort: bool = True,
    ascending: bool = False,
    top_n: int | None = None,
) -> pd.DataFrame:
    """Calculate frequency counts for a single column."""

    _validate_dataframe(df)
    _validate_column(df, column)

    if not isinstance(normalize, bool):
        raise TypeError("normalize must be a boolean.")

    if not isinstance(dropna, bool):
        raise TypeError("dropna must be a boolean.")

    if not isinstance(sort, bool):
        raise TypeError("sort must be a boolean.")

    if not isinstance(ascending, bool):
        raise TypeError("ascending must be a boolean.")

    if top_n is not None:
        if isinstance(top_n, bool) or not isinstance(top_n, int):
            raise TypeError("top_n must be an integer.")
        if top_n < 1:
            raise ValueError("top_n must be greater than zero.")

    counts = df[column].value_counts(
        normalize=normalize,
        dropna=dropna,
        sort=sort,
        ascending=ascending,
    )

    if top_n is not None:
        counts = counts.head(top_n)

    result = counts.rename("proportion" if normalize else "count")
    result.index.name = column

    return result.to_frame()


def grouped_value_counts(
    df: pd.DataFrame,
    columns: Sequence[str],
    *,
    normalize: bool = False,
    dropna: bool = True,
    sort: bool = True,
    ascending: bool = False,
    top_n: int | None = None,
) -> pd.DataFrame:
    """Calculate frequency counts for combinations of columns."""

    _validate_dataframe(df)

    if isinstance(columns, str):
        columns = [columns]

    if not isinstance(columns, Sequence) or len(columns) == 0:
        raise ValueError("columns must be a non-empty sequence.")

    columns = list(columns)

    if len(columns) != len(set(columns)):
        raise ValueError("columns must not contain duplicates.")

    for column in columns:
        _validate_column(df, column)

    if top_n is not None:
        if isinstance(top_n, bool) or not isinstance(top_n, int):
            raise TypeError("top_n must be an integer.")
        if top_n < 1:
            raise ValueError("top_n must be greater than zero.")

    result = (
        df.groupby(columns, dropna=dropna, observed=True)
        .size()
        .rename("count")
        .reset_index()
    )

    if sort:
        result = result.sort_values(
            "count",
            ascending=ascending,
            kind="stable",
        )

    if normalize:
        total = result["count"].sum()
        result["proportion"] = (
            result["count"] / total if total else 0.0
        )

    if top_n is not None:
        result = result.head(top_n)

    return result.reset_index(drop=True)


def crosstab(
    df: pd.DataFrame,
    index: str | Sequence[str],
    columns: str | Sequence[str],
    *,
    normalize: bool | str = False,
    margins: bool = False,
    dropna: bool = True,
) -> pd.DataFrame:
    """Generate a contingency table between categorical variables."""

    _validate_dataframe(df)

    if isinstance(index, str):
        index = [index]

    if isinstance(columns, str):
        columns = [columns]

    if not isinstance(index, Sequence) or len(index) == 0:
        raise ValueError("index must be a non-empty sequence.")

    if not isinstance(columns, Sequence) or len(columns) == 0:
        raise ValueError("columns must be a non-empty sequence.")

    index = list(index)
    columns = list(columns)

    for column in index + columns:
        _validate_column(df, column)

    if normalize not in (False, True, "index", "columns"):
        raise ValueError(
            "normalize must be False, True, 'index', or 'columns'."
        )

    if normalize is True:
        normalize = "all"

    result = pd.crosstab(
        index=[df[column] for column in index],
        columns=[df[column] for column in columns],
        normalize=normalize,
        margins=margins,
        dropna=dropna,
    )

    if len(index) == 1:
        result.index.name = index[0]
    else:
        result.index.names = index

    if len(columns) == 1:
        result.columns.name = columns[0]
    else:
        result.columns.names = columns

    return result
