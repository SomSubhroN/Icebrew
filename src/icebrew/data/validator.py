"""Dataset validation utilities for Icebrew."""

import pandas as pd


def validate_data(
    df: pd.DataFrame,
    *,
    required_columns: list[str] | None = None,
    expected_dtypes: dict[str, str] | None = None,
    allowed_values: dict[str, list] | None = None,
    numeric_ranges: dict[str, tuple[float | None, float | None]] | None = None,
    non_nullable: list[str] | None = None,
    unique_columns: list[str] | None = None,
) -> dict:
    """Validate a DataFrame against explicitly defined constraints."""

    if not isinstance(df, pd.DataFrame):
        raise TypeError("Expected a pandas DataFrame.")

    issues = []

    # Structural validation
    if df.columns.duplicated().any():
        duplicate_names = df.columns[df.columns.duplicated()].tolist()
        issues.append({
            "type": "duplicate_columns",
            "columns": duplicate_names,
        })

    required_columns = required_columns or []
    expected_dtypes = expected_dtypes or {}
    allowed_values = allowed_values or {}
    numeric_ranges = numeric_ranges or {}
    non_nullable = non_nullable or []
    unique_columns = unique_columns or []

    # Check required columns
    missing_columns = [
        column for column in required_columns
        if column not in df.columns
    ]

    if missing_columns:
        issues.append({
            "type": "missing_columns",
            "columns": missing_columns,
        })

    # Check data types
    for column, expected_dtype in expected_dtypes.items():
        if column not in df.columns:
            continue

        actual_dtype = str(df[column].dtype)

        if actual_dtype != expected_dtype:
            issues.append({
                "type": "dtype_mismatch",
                "column": column,
                "expected": expected_dtype,
                "actual": actual_dtype,
            })

    # Check non-nullable columns
    for column in non_nullable:
        if column not in df.columns:
            continue

        missing_count = int(df[column].isna().sum())

        if missing_count:
            issues.append({
                "type": "null_values",
                "column": column,
                "count": missing_count,
            })

    # Check allowed values
    for column, values in allowed_values.items():
        if column not in df.columns:
            continue

        invalid_mask = df[column].notna() & ~df[column].isin(values)
        invalid_count = int(invalid_mask.sum())

        if invalid_count:
            issues.append({
                "type": "invalid_values",
                "column": column,
                "allowed": values,
                "invalid_count": invalid_count,
                "invalid_values": df.loc[invalid_mask, column].unique().tolist(),
            })

    # Check numeric ranges
    for column, bounds in numeric_ranges.items():
        if column not in df.columns:
            continue

        if not pd.api.types.is_numeric_dtype(df[column]):
            issues.append({
                "type": "non_numeric_range_column",
                "column": column,
            })
            continue

        lower, upper = bounds
        invalid_mask = pd.Series(False, index=df.index)

        if lower is not None:
            invalid_mask |= df[column] < lower

        if upper is not None:
            invalid_mask |= df[column] > upper

        invalid_mask &= df[column].notna()

        invalid_count = int(invalid_mask.sum())

        if invalid_count:
            issues.append({
                "type": "numeric_range_violation",
                "column": column,
                "lower": lower,
                "upper": upper,
                "invalid_count": invalid_count,
                "invalid_values": df.loc[invalid_mask, column].tolist(),
            })

    # Check uniqueness
    for column in unique_columns:
        if column not in df.columns:
            continue

        duplicate_mask = df[column].duplicated(keep=False)
        duplicate_count = int(duplicate_mask.sum())

        if duplicate_count:
            issues.append({
                "type": "non_unique_values",
                "column": column,
                "duplicate_count": duplicate_count,
                "duplicate_values": df.loc[
                    duplicate_mask, column
                ].unique().tolist(),
            })

    return {
        "valid": len(issues) == 0,
        "issues_count": len(issues),
        "issues": issues,
        "shape": df.shape,
    }