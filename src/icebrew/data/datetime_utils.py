
"""Datetime utilities for Icebrew."""

import pandas as pd


def _validate_dataframe(df: pd.DataFrame) -> None:
    if not isinstance(df, pd.DataFrame):
        raise TypeError("Expected a pandas DataFrame.")

    if df.columns.duplicated().any():
        raise ValueError("DataFrame contains duplicate column names.")


def _validate_column(df: pd.DataFrame, column: str) -> None:
    if column not in df.columns:
        raise KeyError(f"Column not found: {column}")


def parse_datetime(
    df: pd.DataFrame,
    columns,
    *,
    format=None,
    dayfirst=False,
    yearfirst=False,
    utc=False,
    errors="raise",
) -> pd.DataFrame:
    """Convert selected columns to datetime without modifying the source."""

    _validate_dataframe(df)

    if isinstance(columns, str):
        columns = [columns]

    if not columns:
        raise ValueError("At least one column must be specified.")

    if errors not in {"raise", "coerce", "ignore"}:
        raise ValueError("errors must be 'raise', 'coerce', or 'ignore'.")

    result = df.copy(deep=True)

    for column in columns:
        _validate_column(result, column)

        original = result[column].copy()

        try:
            result[column] = pd.to_datetime(
                result[column],
                format=format,
                dayfirst=dayfirst,
                yearfirst=yearfirst,
                utc=utc,
                errors="coerce" if errors == "coerce" else "raise",
            )
        except Exception:
            if errors == "ignore":
                result[column] = original
            else:
                raise

    return result


def extract_datetime(
    df: pd.DataFrame,
    column: str,
    *,
    components=None,
    prefix=None,
) -> pd.DataFrame:
    """Extract datetime components into new columns."""

    _validate_dataframe(df)
    _validate_column(df, column)

    if not pd.api.types.is_datetime64_any_dtype(df[column]):
        raise TypeError(
            f"Column '{column}' must have a datetime dtype. "
            "Use parse_datetime() first."
        )

    available = {
        "year": lambda s: s.dt.year,
        "month": lambda s: s.dt.month,
        "day": lambda s: s.dt.day,
        "hour": lambda s: s.dt.hour,
        "minute": lambda s: s.dt.minute,
        "second": lambda s: s.dt.second,
        "dayofweek": lambda s: s.dt.day_of_week,
        "dayofyear": lambda s: s.dt.dayofyear,
        "week": lambda s: s.dt.isocalendar().week,
        "quarter": lambda s: s.dt.quarter,
        "date": lambda s: s.dt.date,
        "time": lambda s: s.dt.time,
        "is_month_start": lambda s: s.dt.is_month_start,
        "is_month_end": lambda s: s.dt.is_month_end,
        "is_quarter_start": lambda s: s.dt.is_quarter_start,
        "is_quarter_end": lambda s: s.dt.is_quarter_end,
        "is_year_start": lambda s: s.dt.is_year_start,
        "is_year_end": lambda s: s.dt.is_year_end,
    }

    if components is None:
        components = ["year", "month", "day", "dayofweek"]

    if isinstance(components, str):
        components = [components]

    invalid = set(components) - set(available)

    if invalid:
        raise ValueError(f"Unsupported datetime components: {sorted(invalid)}")

    result = df.copy(deep=True)

    prefix = prefix or column

    for component in components:
        new_column = f"{prefix}_{component}"

        if new_column in result.columns and new_column != column:
            raise ValueError(
                f"Output column already exists: {new_column}"
            )

        result[new_column] = available[component](result[column])

    return result


def datetime_difference(
    df: pd.DataFrame,
    start_column: str,
    end_column: str,
    *,
    unit="days",
    output_column=None,
) -> pd.DataFrame:
    """Calculate the temporal difference between two datetime columns."""

    _validate_dataframe(df)
    _validate_column(df, start_column)
    _validate_column(df, end_column)

    for column in (start_column, end_column):
        if not pd.api.types.is_datetime64_any_dtype(df[column]):
            raise TypeError(
                f"Column '{column}' must have a datetime dtype."
            )

    supported_units = {
        "days": "days",
        "hours": "hours",
        "minutes": "minutes",
        "seconds": "seconds",
        "milliseconds": "milliseconds",
        "microseconds": "microseconds",
        "nanoseconds": "nanoseconds",
    }

    if unit not in supported_units:
        raise ValueError(f"Unsupported unit: {unit}")

    result = df.copy(deep=True)

    difference = result[end_column] - result[start_column]

    result_column = output_column or f"{end_column}_minus_{start_column}"

    if result_column in result.columns:
        raise ValueError(f"Output column already exists: {result_column}")

    result[result_column] = difference.dt.total_seconds()

    divisors = {
        "days": 86400,
        "hours": 3600,
        "minutes": 60,
        "seconds": 1,
        "milliseconds": 0.001,
        "microseconds": 0.000001,
        "nanoseconds": 0.000000001,
    }

    result[result_column] = result[result_column] / divisors[unit]

    return result


def filter_datetime(
    df: pd.DataFrame,
    column: str,
    *,
    start=None,
    end=None,
    inclusive="both",
) -> pd.DataFrame:
    """Filter rows within a datetime range."""

    _validate_dataframe(df)
    _validate_column(df, column)

    if not pd.api.types.is_datetime64_any_dtype(df[column]):
        raise TypeError(
            f"Column '{column}' must have a datetime dtype."
        )

    if inclusive not in {"both", "neither", "left", "right"}:
        raise ValueError(
            "inclusive must be 'both', 'neither', 'left', or 'right'."
        )

    mask = pd.Series(True, index=df.index)

    if start is not None:
        start = pd.Timestamp(start)

        if df[column].dt.tz is not None and start.tzinfo is None:
            raise ValueError(
                "Timezone-aware column requires timezone-aware start."
            )

        if df[column].dt.tz is None and start.tzinfo is not None:
            raise ValueError(
                "Timezone-naive column requires timezone-naive start."
            )

        mask &= (
            df[column] >= start
            if inclusive in {"both", "left"}
            else df[column] > start
        )

    if end is not None:
        end = pd.Timestamp(end)

        if df[column].dt.tz is not None and end.tzinfo is None:
            raise ValueError(
                "Timezone-aware column requires timezone-aware end."
            )

        if df[column].dt.tz is None and end.tzinfo is not None:
            raise ValueError(
                "Timezone-naive column requires timezone-naive end."
            )

        mask &= (
            df[column] <= end
            if inclusive in {"both", "right"}
            else df[column] < end
        )

    return df.loc[mask].copy()


def convert_timezone(
    df: pd.DataFrame,
    column: str,
    timezone: str,
    *,
    assume_timezone=None,
    ambiguous="raise",
    nonexistent="raise",
) -> pd.DataFrame:
    """Convert a datetime column to a target timezone."""

    _validate_dataframe(df)
    _validate_column(df, column)

    if not pd.api.types.is_datetime64_any_dtype(df[column]):
        raise TypeError(
            f"Column '{column}' must have a datetime dtype."
        )

    result = df.copy(deep=True)

    series = result[column]

    if series.dt.tz is None:
        if assume_timezone is None:
            raise ValueError(
                "Naive datetimes require assume_timezone to be specified."
            )

        series = series.dt.tz_localize(
            assume_timezone,
            ambiguous=ambiguous, # type: ignore
            nonexistent=nonexistent, # type: ignore
        )

    result[column] = series.dt.tz_convert(timezone)

    return result


def round_datetime(
    df: pd.DataFrame,
    column: str,
    *,
    frequency,
    method="round",
    output_column=None,
) -> pd.DataFrame:
    """Round, floor, or ceil datetime values to a specified frequency."""

    _validate_dataframe(df)
    _validate_column(df, column)

    if not pd.api.types.is_datetime64_any_dtype(df[column]):
        raise TypeError(
            f"Column '{column}' must have a datetime dtype."
        )

    if method not in {"round", "floor", "ceil"}:
        raise ValueError("method must be 'round', 'floor', or 'ceil'.")

    result = df.copy(deep=True)

    output_column = output_column or column

    if output_column != column and output_column in result.columns:
        raise ValueError(f"Output column already exists: {output_column}")

    result[output_column] = getattr(result[column].dt, method)(frequency)

    return result
