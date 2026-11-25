from pathlib import Path

import pandas as pd


def load_csv(
    file_path: str | Path,
    delimiter: str = ",",
    encoding: str = "utf-8",
    na_values=None,
    header=0,
    skiprows=None,
    nrows=None,
    usecols=None,
    dtype=None,
    parse_dates=None,
    comment=None,
    quotechar='"',
    decimal=".",
    thousands=None,
    skip_blank_lines=True,
    on_bad_lines="error",
) -> pd.DataFrame:

    file_path = Path(file_path)

    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    if not file_path.is_file():
        raise ValueError(f"Path is not a file: {file_path}")

    if not isinstance(delimiter, str) or len(delimiter) != 1:
        raise ValueError("Delimiter must be a single character.")

    if not isinstance(quotechar, str) or len(quotechar) != 1:
        raise ValueError("Quote character must be a single character.")

    return pd.read_csv(
        file_path,
        sep=delimiter,
        encoding=encoding,
        na_values=na_values,
        header=header,
        skiprows=skiprows,
        nrows=nrows,
        usecols=usecols,
        dtype=dtype,
        parse_dates=parse_dates,
        comment=comment,
        quotechar=quotechar,
        decimal=decimal,
        thousands=thousands,
        skip_blank_lines=skip_blank_lines,
        on_bad_lines=on_bad_lines,
    )