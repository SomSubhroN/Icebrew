"""Data type conversion utilities for Icebrew."""

import pandas as pd


SUPPORTED_TYPES = {
    "int",
    "integer",
    "float",
    "numeric",
    "str",
    "string",
    "bool",
    "boolean",
    "datetime",
    "category",
    "object",
}


def convert_data(
    df: pd.DataFrame,
    conversions: dict,
    *,
    errors: str = "raise",
) -> pd.DataFrame:
    """Convert specified DataFrame columns to requested data types.

    Parameters
    ----------
    df : pd.DataFrame
        Input DataFrame.
    conversions : dict
        Column-to-type mapping.

        Supported specifications:
        {"age": "int"}
        {"score": "float"}
        {"date": {"type": "datetime", "format": "%Y-%m-%d"}}
        {"status": {"type": "category", "categories": ["A", "B"], "ordered": True}}
    errors : str
        'raise', 'coerce', or 'ignore'.

    Returns
    -------
    pd.DataFrame
        Converted copy of the original DataFrame.
    """

    if not isinstance(df, pd.DataFrame):
        raise TypeError("Expected a pandas DataFrame.")

    if not isinstance(conversions, dict):
        raise TypeError("conversions must be a dictionary.")

    if errors not in {"raise", "coerce", "ignore"}:
        raise ValueError("errors must be 'raise', 'coerce', or 'ignore'.")

    if df.columns.duplicated().any():
        raise ValueError("DataFrame contains duplicate column names.")

    result = df.copy(deep=True)

    for column, specification in conversions.items():

        if column not in result.columns:
            raise KeyError(f"Column not found: {column}")

        options = (
            specification.copy()
            if isinstance(specification, dict)
            else {"type": specification}
        )

        if "type" not in options:
            raise ValueError(f"Missing conversion type for column: {column}")

        target_type = options["type"]

        if not isinstance(target_type, str):
            raise TypeError(f"Conversion type must be a string: {column}")

        target_type = target_type.lower()

        if target_type not in SUPPORTED_TYPES:
            raise ValueError(
                f"Unsupported conversion type '{target_type}' for column '{column}'."
            )

        original = result[column].copy()

        try:
            if target_type in {"int", "integer"}:
                result[column] = pd.to_numeric(
                    result[column],
                    errors="coerce" if errors == "coerce" else "raise",
                ).astype("Int64")

            elif target_type in {"float", "numeric"}:
                result[column] = pd.to_numeric(
                    result[column],
                    errors="coerce" if errors == "coerce" else "raise",
                ).astype("float64")

            elif target_type in {"str", "string"}:
                result[column] = result[column].astype("string")

            elif target_type in {"bool", "boolean"}:
                result[column] = _convert_boolean(
                    result[column],
                    options,
                    errors,
                )

            elif target_type == "datetime":
                result[column] = pd.to_datetime(
                    result[column],
                    format=options.get("format"),
                    errors="coerce" if errors == "coerce" else "raise",
                    dayfirst=options.get("dayfirst", False),
                    yearfirst=options.get("yearfirst", False),
                    utc=options.get("utc", False),
                )

            elif target_type == "category":
                result[column] = pd.Categorical(
                    result[column],
                    categories=options.get("categories"),
                    ordered=options.get("ordered", False),
                )

            elif target_type == "object":
                result[column] = result[column].astype(object)

        except Exception:
            if errors == "ignore":
                result[column] = original
                continue
            raise

    return result


def _convert_boolean(series, options, errors):
    """Convert values to nullable boolean."""

    true_values = options.get("true_values", [True, 1, "1", "true", "True", "TRUE"])
    false_values = options.get("false_values", [False, 0, "0", "false", "False", "FALSE"])

    if set(true_values) & set(false_values):
        raise ValueError("true_values and false_values must not overlap.")

    mapping = {}
    for value in true_values:
        mapping[value] = True

    for value in false_values:
        mapping[value] = False

    converted = series.map(mapping)

    invalid_mask = series.notna() & converted.isna()

    if invalid_mask.any():
        if errors == "raise":
            invalid_values = series[invalid_mask].unique().tolist()
            raise ValueError(f"Invalid boolean values: {invalid_values}")

        if errors == "ignore":
            return series.copy()

    return converted.astype("boolean")