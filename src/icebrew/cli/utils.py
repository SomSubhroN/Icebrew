
"""Shared CLI utilities for Icebrew."""

import json
from pathlib import Path

import pandas as pd
import typer
from rich.console import Console
from rich.table import Table

from icebrew.data.exporter import export_data

console = Console()


def load_dataset(path: str | Path) -> pd.DataFrame:
    """Load a supported dataset into a DataFrame."""

    path = Path(path)

    if not path.exists():
        raise typer.BadParameter(f"File not found: {path}")

    if not path.is_file():
        raise typer.BadParameter(f"Not a file: {path}")

    suffix = path.suffix.lower()

    try:
        if suffix == ".csv":
            return pd.read_csv(path)

        if suffix == ".json":
            return pd.read_json(path)

        if suffix == ".jsonl":
            return pd.read_json(path, lines=True)

        if suffix in {".xlsx", ".xls"}:
            return pd.read_excel(path)

        if suffix == ".parquet":
            return pd.read_parquet(path)

    except ImportError as exc:
        raise typer.BadParameter(
            f"Required dependency is unavailable for {suffix}: {exc}"
        ) from exc
    except Exception as exc:
        raise typer.BadParameter(
            f"Unable to load {path}: {exc}"
        ) from exc

    raise typer.BadParameter(
        f"Unsupported file format: {suffix or '(no extension)'}"
    )


def save_dataset(
    df: pd.DataFrame,
    output: str | Path,
    overwrite: bool = False,
) -> None:
    """Export a DataFrame using Icebrew's safe exporter."""

    output = Path(output)

    export_data(
        df,
        output,
        overwrite=overwrite,
    )


def print_dataframe(
    df: pd.DataFrame,
    title: str = "Data",
    max_rows: int = 20,
) -> None:
    """Display a DataFrame as a Rich table."""

    table = Table(title=title)

    for column in df.columns:
        table.add_column(str(column))

    display_df = df.head(max_rows)

    for row in display_df.itertuples(index=False, name=None):
        table.add_row(
            *[
                str(value) if value is not None else "None"
                for value in row
            ]
        )

    console.print(table)

    if len(df) > max_rows:
        console.print(
            f"[dim]Showing {max_rows} of {len(df)} rows.[/dim]"
        )


def print_dict(
    data: dict,
    title: str = "Report",
) -> None:
    """Display a dictionary as a Rich table."""

    table = Table(title=title)
    table.add_column("Key", style="cyan")
    table.add_column("Value")

    for key, value in data.items():
        table.add_row(str(key), str(value))

    console.print(table)
