
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import typer
from rich.console import Console
from rich.table import Table

from icebrew.cli.utils import load_dataset, save_dataset, print_dataframe
from icebrew.cli.transform import transform_app
from icebrew.cli.datetime import datetime_app
from icebrew.cli.compare import compare

data_app = typer.Typer(
    name="data",
    help="Dataset loading, inspection, analysis, cleaning and transformation.",
    no_args_is_help=True,
)

console = Console()

# Register subcommand groups
data_app.add_typer(transform_app, name="transform")
data_app.add_typer(datetime_app, name="datetime")

# Register standalone command
data_app.command("compare")(compare)


def parse_json(value: str, option_name: str = "value") -> Any:
    """Parse JSON CLI input and produce an actionable error."""
    try:
        return json.loads(value)
    except json.JSONDecodeError as exc:
        raise typer.BadParameter(
            f"{option_name} must contain valid JSON: {exc}"
        ) from exc


def print_report(report: dict, title: str = "Report") -> None:
    """Display a dictionary report using Rich."""
    table = Table(title=title)
    table.add_column("Property", style="cyan")
    table.add_column("Value", overflow="fold")

    for key, value in report.items():
        table.add_row(str(key), str(value))

    console.print(table)


@data_app.command("load")
def load(
    input_file: Path = typer.Argument(..., help="Dataset file to load."),
):
    """Load and display a dataset."""
    df = load_dataset(input_file)
    print_dataframe(df, title=f"Loaded: {input_file.name}")


@data_app.command("inspect")
def inspect(
    input_file: Path = typer.Argument(..., help="Dataset file."),
    preview_rows: int = typer.Option(
        5, "--rows", "-r", min=0, help="Number of preview rows."
    ),
):
    """Inspect dataset structure and basic metadata."""
    from icebrew.data.inspector import inspect_data

    df = load_dataset(input_file)
    report = inspect_data(df, preview_rows=preview_rows)

    print_report(
        {
            "Shape": report.get("shape"),
            "Columns": report.get("columns"),
            "Data types": report.get("dtypes"),
            "Missing values": report.get("missing"),
            "Duplicates": report.get("duplicates"),
            "Memory usage": report.get("memory_usage"),
        },
        title="Dataset Inspection",
    )

    if "preview" in report:
        print_dataframe(report["preview"], title="Preview")


@data_app.command("profile")
def profile(
    input_file: Path = typer.Argument(..., help="Dataset file."),
    top_n: int = typer.Option(5, "--top", min=1, help="Top values to display."),
    quantiles: bool = typer.Option(
        True, "--quantiles/--no-quantiles", help="Include numeric quantiles."
    ),
):
    """Generate a dataset profile."""
    from icebrew.data.profiler import profile_data

    df = load_dataset(input_file)
    report = profile_data(df, top_n=top_n, include_quantiles=quantiles)

    table = Table(title="Dataset Profile")
    table.add_column("Column", style="cyan")
    table.add_column("Details", overflow="fold")

    for column, details in report.items():
        table.add_row(str(column), str(details))

    console.print(table)


@data_app.command("quality")
def quality(
    input_file: Path = typer.Argument(..., help="Dataset file."),
):
    """Analyze dataset quality."""
    from icebrew.data.quality import analyze_quality

    df = load_dataset(input_file)
    report = analyze_quality(df)

    print_report(report, title="Data Quality")


@data_app.command("missing")
def missing(
    input_file: Path = typer.Argument(..., help="Dataset file."),
):
    """Analyze missing data."""
    from icebrew.data.missing import analyze_missing

    df = load_dataset(input_file)
    report = analyze_missing(df)

    print_report(report, title="Missing Data Analysis")


@data_app.command("sample")
def sample(
    input_file: Path = typer.Argument(..., help="Dataset file."),
    output: Path = typer.Option(..., "--output", "-o"),
    n: int | None = typer.Option(None, "--n", min=1),
    fraction: float | None = typer.Option(None, "--fraction", min=0.0, max=1.0),
    random_state: int | None = typer.Option(None, "--seed"),
    replace: bool = typer.Option(False, "--replace"),
    overwrite: bool = typer.Option(False, "--overwrite"),
):
    """Randomly sample rows from a dataset."""
    from icebrew.data.sampling import sample_data

    df = load_dataset(input_file)

    result = sample_data(
        df,
        n=n,
        fraction=fraction,
        random_state=random_state,
        replace=replace,
    )

    save_dataset(result, output, overwrite=overwrite)
    console.print(f"[green]Sample saved:[/green] {output}")


@data_app.command("clean")
def clean(
    input_file: Path = typer.Argument(..., help="Dataset file."),
    output: Path = typer.Option(..., "--output", "-o"),
    drop_duplicates: bool = typer.Option(False, "--drop-duplicates"),
    drop_empty_rows: bool = typer.Option(False, "--drop-empty-rows"),
    drop_empty_columns: bool = typer.Option(False, "--drop-empty-columns"),
    trim_whitespace: bool = typer.Option(False, "--trim-whitespace"),
    replace_values: str | None = typer.Option(
        None, "--replace", help="JSON mapping of replacement values."
    ),
    normalize_missing: str | None = typer.Option(
        None, "--normalize-missing", help="JSON list of missing-value tokens."
    ),
    rename_columns: str | None = typer.Option(
        None, "--rename", help="JSON mapping of old to new column names."
    ),
    overwrite: bool = typer.Option(False, "--overwrite"),
):
    """Clean a dataset."""
    from icebrew.data.cleaner import clean_data

    df = load_dataset(input_file)

    result = clean_data(
        df,
        drop_duplicates=drop_duplicates,
        drop_empty_rows=drop_empty_rows,
        drop_empty_columns=drop_empty_columns,
        trim_whitespace=trim_whitespace,
        replace_values=parse_json(replace_values, "--replace")
        if replace_values is not None
        else None,
        normalize_missing=parse_json(normalize_missing, "--normalize-missing")
        if normalize_missing is not None
        else None,
        rename_columns=parse_json(rename_columns, "--rename")
        if rename_columns is not None
        else None,
    )

    save_dataset(result, output, overwrite=overwrite)
    console.print(f"[green]Cleaned dataset saved:[/green] {output}")


@data_app.command("frequencies")
def frequencies(
    input_file: Path = typer.Argument(..., help="Dataset file."),
    column: str = typer.Option(..., "--column", "-c"),
    normalize: bool = typer.Option(False, "--normalize"),
    dropna: bool = typer.Option(True, "--dropna/--keepna"),
    sort: bool = typer.Option(True, "--sort/--no-sort"),
    ascending: bool = typer.Option(False, "--ascending"),
    top_n: int | None = typer.Option(None, "--top", min=1),
):
    """Calculate value frequencies for a column."""
    from icebrew.data.frequency import value_counts

    df = load_dataset(input_file)

    result = value_counts(
        df,
        column,
        normalize=normalize,
        dropna=dropna,
        sort=sort,
        ascending=ascending,
        top_n=top_n,
    )

    print_dataframe(result.reset_index(), title=f"Frequencies: {column}")


@data_app.command("crosstab")
def crosstab_command(
    input_file: Path = typer.Argument(..., help="Dataset file."),
    index: str = typer.Option(..., "--index"),
    columns: str = typer.Option(..., "--columns"),
    normalize: bool = typer.Option(False, "--normalize"),
    margins: bool = typer.Option(False, "--margins"),
    dropna: bool = typer.Option(True, "--dropna/--keepna"),
):
    """Create a cross-tabulation."""
    from icebrew.data.frequency import crosstab

    df = load_dataset(input_file)

    result = crosstab(
        df,
        index=index,
        columns=columns,
        normalize=normalize,
        margins=margins,
        dropna=dropna,
    )

    print_dataframe(result, title="Cross-tabulation")


@data_app.command("export")
def export(
    input_file: Path = typer.Argument(..., help="Dataset file."),
    output: Path = typer.Option(..., "--output", "-o"),
    format: str | None = typer.Option(None, "--format"),
    overwrite: bool = typer.Option(False, "--overwrite"),
    index: bool = typer.Option(False, "--index"),
    encoding: str = typer.Option("utf-8", "--encoding"),
    sheet_name: str = typer.Option("Sheet1", "--sheet"),
):
    """Export a dataset into another format."""
    from icebrew.data.exporter import export_data

    df = load_dataset(input_file)

    export_data(
        df,
        output,
        format=format,
        overwrite=overwrite,
        index=index,
        encoding=encoding,
        sheet_name=sheet_name,
    )

    console.print(f"[green]Export completed:[/green] {output}")


@data_app.command("convert")
def convert(
    input_file: Path = typer.Argument(..., help="Dataset file."),
    conversions: str = typer.Option(
        ..., "--conversions", help="JSON mapping of columns to target types."
    ),
    output: Path = typer.Option(..., "--output", "-o"),
    errors: str = typer.Option("raise", "--errors"),
    overwrite: bool = typer.Option(False, "--overwrite"),
):
    """Convert column data types."""
    from icebrew.data.converter import convert_data

    df = load_dataset(input_file)
    mapping = parse_json(conversions, "--conversions")

    result = convert_data(df, mapping, errors=errors)
    save_dataset(result, output, overwrite=overwrite)

    console.print(f"[green]Conversion completed:[/green] {output}")


@data_app.command("validate")
def validate(
    input_file: Path = typer.Argument(..., help="Dataset file."),
    required_columns: str | None = typer.Option(
        None, "--required-columns", help="Comma-separated required column names."
    ),
    expected_dtypes: str | None = typer.Option(
        None, "--dtypes", help="JSON mapping of columns to expected types."
    ),
    allowed_values: str | None = typer.Option(
        None, "--allowed-values", help="JSON mapping of columns to allowed values."
    ),
    numeric_ranges: str | None = typer.Option(
        None, "--numeric-ranges", help="JSON mapping of columns to numeric ranges."
    ),
    non_nullable: str | None = typer.Option(
        None, "--non-nullable", help="Comma-separated non-nullable columns."
    ),
    unique_columns: str | None = typer.Option(
        None, "--unique", help="Comma-separated columns that must be unique."
    ),
):
    """Validate dataset against specified constraints."""
    from icebrew.data.validator import validate_data

    df = load_dataset(input_file)

    report = validate_data(
        df,
        required_columns=[c.strip() for c in required_columns.split(",")]
        if required_columns
        else None,
        expected_dtypes=parse_json(expected_dtypes, "--dtypes")
        if expected_dtypes
        else None,
        allowed_values=parse_json(allowed_values, "--allowed-values")
        if allowed_values
        else None,
        numeric_ranges=parse_json(numeric_ranges, "--numeric-ranges")
        if numeric_ranges
        else None,
        non_nullable=[c.strip() for c in non_nullable.split(",")]
        if non_nullable
        else None,
        unique_columns=[c.strip() for c in unique_columns.split(",")]
        if unique_columns
        else None,
    )

    print_report(report, title="Validation Results")

    if not report.get("valid", False):
        raise typer.Exit(code=1)
