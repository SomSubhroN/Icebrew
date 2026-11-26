
"""CLI commands for Icebrew's data toolkit."""

import json
from pathlib import Path
from typing import Any
from icebrew.cli.datetime import datetime_app
import pandas as pd
import typer
from rich.console import Console
from rich.table import Table

from icebrew.cli.utils import (
    load_dataset,
    print_dataframe,
    print_dict,
    save_dataset,
)
from icebrew.cli.transform import transform_app

from icebrew.data.converter import convert_data
from icebrew.data.exporter import export_data
from icebrew.data.frequency import crosstab, value_counts
from icebrew.data.inspector import inspect_data
from icebrew.data.missing import analyze_missing
from icebrew.data.profiler import profile_data
from icebrew.data.quality import analyze_quality
from icebrew.data.sampling import sample_data

data_app = typer.Typer(
    name="data",
    help="Load, inspect, profile, clean, and analyze datasets.",
    no_args_is_help=True,
)

console = Console()

# Register nested command groups.
data_app.add_typer(transform_app, name="transform")


def parse_json(value: str, argument_name: str) -> Any:
    """Parse JSON and raise an actionable CLI error."""

    try:
        return json.loads(value)
    except json.JSONDecodeError as exc:
        raise typer.BadParameter(
            f"{argument_name} must contain valid JSON: {exc.msg}"
        ) from exc


def print_report(report: Any, title: str = "Report") -> None:
    """Print a structured report in a readable format."""

    if isinstance(report, dict):
        table = Table(title=title)
        table.add_column("Key", style="cyan")
        table.add_column("Value")

        for key, value in report.items():
            if isinstance(value, (dict, list)):
                value = json.dumps(value, indent=2, default=str)
            table.add_row(str(key), str(value))

        console.print(table)
        return

    console.print(report)


# ---------------------------------------------------------------------
# LOAD
# ---------------------------------------------------------------------


@data_app.command()
def load(
    file: Path = typer.Argument(..., help="Dataset to load."),
) -> None:
    """Load and display a dataset."""

    df = load_dataset(file)

    console.print(
        f"[green]Loaded dataset:[/green] {file}"
    )
    console.print(
        f"[bold]Shape:[/bold] {df.shape[0]} rows × {df.shape[1]} columns"
    )

    print_dataframe(df, title="Dataset")


# ---------------------------------------------------------------------
# INSPECT
# ---------------------------------------------------------------------


@data_app.command()
def inspect(
    file: Path = typer.Argument(..., help="Dataset to inspect."),
    preview: int = typer.Option(
        5,
        "--preview",
        "-n",
        min=0,
        help="Number of preview rows.",
    ),
) -> None:
    """Inspect a dataset's structure."""

    df = load_dataset(file)
    report = inspect_data(df, preview_rows=preview)

    console.print()
    console.print("[bold cyan]Dataset Inspection[/bold cyan]")
    console.print()

    for key, value in report.items():
        if key == "preview":
            continue

        if isinstance(value, (dict, list)):
            value = json.dumps(value, indent=2, default=str)

        console.print(f"[bold]{key}:[/bold] {value}")

    if "preview" in report and isinstance(report["preview"], pd.DataFrame):
        print_dataframe(
            report["preview"],
            title="Preview",
            max_rows=max(preview, 1),
        )


# ---------------------------------------------------------------------
# PROFILE
# ---------------------------------------------------------------------


@data_app.command()
def profile(
    file: Path = typer.Argument(..., help="Dataset to profile."),
    top: int = typer.Option(
        5,
        "--top",
        min=1,
        help="Number of top values for categorical columns.",
    ),
) -> None:
    """Generate a dataset profile."""

    df = load_dataset(file)
    report = profile_data(df, top_n=top)

    console.print()
    console.print("[bold cyan]Dataset Profile[/bold cyan]")
    console.print()

    for column, details in report.items():
        table = Table(title=str(column))
        table.add_column("Metric", style="cyan")
        table.add_column("Value")

        for key, value in details.items():
            if isinstance(value, (dict, list)):
                value = json.dumps(value, indent=2, default=str)

            table.add_row(str(key), str(value))

        console.print(table)


# ---------------------------------------------------------------------
# QUALITY
# ---------------------------------------------------------------------


@data_app.command()
def quality(
    file: Path = typer.Argument(..., help="Dataset to analyze."),
) -> None:
    """Analyze dataset quality."""

    df = load_dataset(file)
    report = analyze_quality(df)

    console.print()
    console.print("[bold cyan]Data Quality Report[/bold cyan]")
    console.print()

    print_report(report, "Quality Report")


# ---------------------------------------------------------------------
# MISSING DATA
# ---------------------------------------------------------------------


@data_app.command()
def missing(
    file: Path = typer.Argument(..., help="Dataset to analyze."),
) -> None:
    """Analyze missing values."""

    df = load_dataset(file)
    report = analyze_missing(df)

    console.print()
    console.print("[bold cyan]Missing Data Analysis[/bold cyan]")
    console.print()

    print_report(report, "Missing Data")


# ---------------------------------------------------------------------
# SAMPLE
# ---------------------------------------------------------------------


@data_app.command()
def sample(
    file: Path = typer.Argument(..., help="Dataset to sample."),
    n: int | None = typer.Option(
        None,
        "--n",
        min=1,
        help="Number of rows to sample.",
    ),
    fraction: float | None = typer.Option(
        None,
        "--fraction",
        min=0.0,
        max=1.0,
        help="Fraction of rows to sample.",
    ),
    seed: int | None = typer.Option(
        None,
        "--seed",
        help="Random seed.",
    ),
    output: Path | None = typer.Option(
        None,
        "--output",
        "-o",
        help="Output file.",
    ),
    overwrite: bool = typer.Option(
        False,
        "--overwrite",
        help="Overwrite output if it exists.",
    ),
) -> None:
    """Sample rows from a dataset."""

    if n is not None and fraction is not None:
        raise typer.BadParameter(
            "Specify either --n or --fraction, not both."
        )

    if n is None and fraction is None:
        raise typer.BadParameter(
            "Specify either --n or --fraction."
        )

    df = load_dataset(file)

    result = sample_data(
        df,
        n=n,
        fraction=fraction,
        random_state=seed,
    )

    print_dataframe(result, title="Sample")

    if output:
        save_dataset(result, output, overwrite=overwrite)
        console.print(
            f"[green]Sample saved to:[/green] {output}"
        )


# ---------------------------------------------------------------------
# CLEAN
# ---------------------------------------------------------------------


@data_app.command()
def clean(
    file: Path = typer.Argument(..., help="Dataset to clean."),
    drop_duplicates: bool = typer.Option(
        False,
        "--drop-duplicates",
        help="Remove duplicate rows.",
    ),
    drop_empty_rows: bool = typer.Option(
        False,
        "--drop-empty-rows",
        help="Remove fully empty rows.",
    ),
    drop_empty_columns: bool = typer.Option(
        False,
        "--drop-empty-columns",
        help="Remove fully empty columns.",
    ),
    trim_whitespace: bool = typer.Option(
        False,
        "--trim-whitespace",
        help="Trim whitespace from string values.",
    ),
    output: Path | None = typer.Option(
        None,
        "--output",
        "-o",
        help="Output file.",
    ),
    overwrite: bool = typer.Option(
        False,
        "--overwrite",
        help="Overwrite output if it exists.",
    ),
) -> None:
    """Clean a dataset."""

    from icebrew.data.cleaner import clean_data

    df = load_dataset(file)

    result = clean_data(
        df,
        drop_duplicates=drop_duplicates,
        drop_empty_rows=drop_empty_rows,
        drop_empty_columns=drop_empty_columns,
        trim_whitespace=trim_whitespace,
    )

    print_dataframe(result, title="Cleaned Data")

    console.print(
        f"[bold]Original shape:[/bold] {df.shape}"
    )
    console.print(
        f"[bold]Result shape:[/bold] {result.shape}"
    )

    if output:
        save_dataset(result, output, overwrite=overwrite)
        console.print(
            f"[green]Cleaned dataset saved to:[/green] {output}"
        )


# ---------------------------------------------------------------------
# FREQUENCIES
# ---------------------------------------------------------------------


@data_app.command()
def frequencies(
    file: Path = typer.Argument(..., help="Dataset to analyze."),
    column: str = typer.Option(
        ...,
        "--column",
        "-c",
        help="Column to analyze.",
    ),
    normalize: bool = typer.Option(
        False,
        "--normalize",
        help="Display relative frequencies.",
    ),
    top: int | None = typer.Option(
        None,
        "--top",
        min=1,
        help="Limit displayed categories.",
    ),
    output: Path | None = typer.Option(
        None,
        "--output",
        "-o",
        help="Output file.",
    ),
    overwrite: bool = typer.Option(
        False,
        "--overwrite",
        help="Overwrite output if it exists.",
    ),
) -> None:
    """Calculate value frequencies."""

    df = load_dataset(file)

    result = value_counts(
        df,
        column,
        normalize=normalize,
        top_n=top,
    )

    if isinstance(result, pd.Series):
        result = result.to_frame(name="frequency")

    print_dataframe(result, title="Frequencies")

    if output:
        save_dataset(result, output, overwrite=overwrite)
        console.print(
            f"[green]Frequencies saved to:[/green] {output}"
        )


# ---------------------------------------------------------------------
# CROSSTAB
# ---------------------------------------------------------------------


@data_app.command("crosstab")
def crosstab_command(
    file: Path = typer.Argument(..., help="Dataset to analyze."),
    index: str = typer.Option(
        ...,
        "--index",
        "-i",
        help="Row variable.",
    ),
    columns: str = typer.Option(
        ...,
        "--columns",
        "-c",
        help="Column variable.",
    ),
    normalize: str = typer.Option(
        "none",
        "--normalize",
        help="Normalization: none, all, index, columns.",
    ),
    margins: bool = typer.Option(
        False,
        "--margins",
        help="Include totals.",
    ),
    output: Path | None = typer.Option(
        None,
        "--output",
        "-o",
        help="Output file.",
    ),
    overwrite: bool = typer.Option(
        False,
        "--overwrite",
        help="Overwrite output if it exists.",
    ),
) -> None:
    """Create a cross-tabulation."""

    df = load_dataset(file)

    normalization_map = {
        "none": False,
        "all": True,
        "index": "index",
        "columns": "columns",
    }

    if normalize not in normalization_map:
        raise typer.BadParameter(
            "Normalize must be none, all, index, or columns."
        )

    result = crosstab(
        df,
        index=index,
        columns=columns,
        normalize=normalization_map[normalize],
        margins=margins,
    )

    print_dataframe(result, title="Cross-tabulation")

    if output:
        save_dataset(result, output, overwrite=overwrite)
        console.print(
            f"[green]Cross-tabulation saved to:[/green] {output}"
        )


# ---------------------------------------------------------------------
# EXPORT
# ---------------------------------------------------------------------


@data_app.command()
def export(
    file: Path = typer.Argument(..., help="Input dataset."),
    output: Path = typer.Argument(..., help="Output file."),
    overwrite: bool = typer.Option(
        False,
        "--overwrite",
        help="Overwrite output if it exists.",
    ),
) -> None:
    """Export a dataset to another supported format."""

    df = load_dataset(file)

    export_data(
        df,
        output,
        overwrite=overwrite,
    )

    console.print(
        f"[green]Dataset exported to:[/green] {output}"
    )


# ---------------------------------------------------------------------
# CONVERT
# ---------------------------------------------------------------------


@data_app.command()
def convert(
    file: Path = typer.Argument(..., help="Input dataset."),
    spec: str = typer.Option(
        ...,
        "--spec",
        help="JSON mapping of columns to data types.",
    ),
    output: Path | None = typer.Option(
        None,
        "--output",
        "-o",
        help="Output file.",
    ),
    errors: str = typer.Option(
        "raise",
        "--errors",
        help="Conversion error mode: raise, coerce, ignore.",
    ),
    overwrite: bool = typer.Option(
        False,
        "--overwrite",
        help="Overwrite output if it exists.",
    ),
) -> None:
    """Convert column data types."""

    df = load_dataset(file)
    conversion_spec = parse_json(spec, "--spec")

    if not isinstance(conversion_spec, dict) or not conversion_spec:
        raise typer.BadParameter(
            "Conversion specification must be a non-empty JSON object."
        )

    if errors not in {"raise", "coerce", "ignore"}:
        raise typer.BadParameter(
            "Errors must be raise, coerce, or ignore."
        )

    result = convert_data(
        df,
        conversion_spec,
        errors=errors,
    )

    print_dataframe(result, title="Converted Data")

    if output:
        save_dataset(result, output, overwrite=overwrite)
        console.print(
            f"[green]Converted dataset saved to:[/green] {output}"
        )


# ---------------------------------------------------------------------
# VALIDATE
# ---------------------------------------------------------------------


@data_app.command()
def validate(
    file: Path = typer.Argument(..., help="Dataset to validate."),
    spec: str = typer.Option(
        ...,
        "--spec",
        help="JSON validation specification.",
    ),
) -> None:
    """Validate a dataset against a specification."""

    from icebrew.data.validator import validate_data

    df = load_dataset(file)
    validation_spec = parse_json(spec, "--spec")

    if not isinstance(validation_spec, dict):
        raise typer.BadParameter(
            "Validation specification must be a JSON object."
        )

    result = validate_data(df, **validation_spec)

    print_report(result, "Validation Report")

    if not result.get("valid", False):
        console.print(
            "[bold red]Dataset validation failed.[/bold red]"
        )
        raise typer.Exit(code=1)

    console.print(
        "[bold green]Dataset validation passed.[/bold green]"
    )
