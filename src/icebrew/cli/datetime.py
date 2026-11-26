from __future__ import annotations

import json
from pathlib import Path

import typer
from rich.console import Console

from icebrew.cli.utils import load_dataset, save_dataset, print_dataframe
from icebrew.data.datetime_utils import (
    parse_datetime,
    extract_datetime,
    datetime_difference,
    filter_datetime,
    convert_timezone,
    round_datetime,
)

datetime_app = typer.Typer(
    name="datetime",
    help="Datetime processing and temporal analysis.",
    no_args_is_help=True,
)

console = Console()


@datetime_app.command("parse")
def parse(
    input_file: Path = typer.Argument(..., help="Input dataset."),
    columns: str = typer.Option(..., "--columns", "-c", help="Comma-separated columns."),
    output: Path = typer.Option(..., "--output", "-o", help="Output dataset."),
    format: str | None = typer.Option(None, "--format", help="Datetime format."),
    dayfirst: bool = typer.Option(False, "--dayfirst"),
    yearfirst: bool = typer.Option(False, "--yearfirst"),
    utc: bool = typer.Option(False, "--utc"),
    errors: str = typer.Option("raise", "--errors", help="raise or coerce."),
    overwrite: bool = typer.Option(False, "--overwrite"),
):
    """Parse columns into datetime values."""
    df = load_dataset(input_file)

    result = parse_datetime(
        df,
        [c.strip() for c in columns.split(",")],
        format=format,
        dayfirst=dayfirst,
        yearfirst=yearfirst,
        utc=utc,
        errors=errors,
    )

    save_dataset(result, output, overwrite=overwrite)
    console.print(f"[green]Datetime parsing completed.[/green] {output}")


@datetime_app.command("extract")
def extract(
    input_file: Path = typer.Argument(..., help="Input dataset."),
    column: str = typer.Option(..., "--column", "-c"),
    components: str = typer.Option(
        "year,month,day",
        "--components",
        help="Comma-separated datetime components.",
    ),
    output: Path = typer.Option(..., "--output", "-o"),
    prefix: str | None = typer.Option(None, "--prefix"),
    overwrite: bool = typer.Option(False, "--overwrite"),
):
    """Extract datetime components into new columns."""
    df = load_dataset(input_file)

    result = extract_datetime(
        df,
        column,
        components=[c.strip() for c in components.split(",")],
        prefix=prefix,
    )

    save_dataset(result, output, overwrite=overwrite)
    console.print(f"[green]Datetime components extracted.[/green] {output}")


@datetime_app.command("difference")
def difference(
    input_file: Path = typer.Argument(..., help="Input dataset."),
    start_column: str = typer.Option(..., "--start"),
    end_column: str = typer.Option(..., "--end"),
    output: Path = typer.Option(..., "--output", "-o"),
    unit: str = typer.Option("days", "--unit"),
    output_column: str | None = typer.Option(None, "--output-column"),
    overwrite: bool = typer.Option(False, "--overwrite"),
):
    """Calculate differences between two datetime columns."""
    df = load_dataset(input_file)

    result = datetime_difference(
        df,
        start_column,
        end_column,
        unit=unit,
        output_column=output_column,
    )

    save_dataset(result, output, overwrite=overwrite)
    console.print(f"[green]Datetime difference calculated.[/green] {output}")


@datetime_app.command("filter")
def filter_dates(
    input_file: Path = typer.Argument(..., help="Input dataset."),
    column: str = typer.Option(..., "--column", "-c"),
    output: Path = typer.Option(..., "--output", "-o"),
    start: str | None = typer.Option(None, "--start"),
    end: str | None = typer.Option(None, "--end"),
    inclusive: str = typer.Option("both", "--inclusive"),
    overwrite: bool = typer.Option(False, "--overwrite"),
):
    """Filter rows using a datetime range."""
    df = load_dataset(input_file)

    result = filter_datetime(
        df,
        column,
        start=start,
        end=end,
        inclusive=inclusive,
    )

    save_dataset(result, output, overwrite=overwrite)
    console.print(f"[green]Datetime filtering completed.[/green] {output}")


@datetime_app.command("timezone")
def timezone(
    input_file: Path = typer.Argument(..., help="Input dataset."),
    column: str = typer.Option(..., "--column", "-c"),
    timezone_name: str = typer.Option(..., "--timezone", "-t"),
    output: Path = typer.Option(..., "--output", "-o"),
    assume_timezone: str | None = typer.Option(None, "--assume"),
    ambiguous: str = typer.Option("raise", "--ambiguous"),
    nonexistent: str = typer.Option("raise", "--nonexistent"),
    overwrite: bool = typer.Option(False, "--overwrite"),
):
    """Convert datetime values between timezones."""
    df = load_dataset(input_file)

    result = convert_timezone(
        df,
        column,
        timezone_name,
        assume_timezone=assume_timezone,
        ambiguous=ambiguous,
        nonexistent=nonexistent,
    )

    save_dataset(result, output, overwrite=overwrite)
    console.print(f"[green]Timezone conversion completed.[/green] {output}")


@datetime_app.command("round")
def round_dates(
    input_file: Path = typer.Argument(..., help="Input dataset."),
    column: str = typer.Option(..., "--column", "-c"),
    frequency: str = typer.Option(..., "--frequency", "-f"),
    output: Path = typer.Option(..., "--output", "-o"),
    method: str = typer.Option("round", "--method"),
    output_column: str | None = typer.Option(None, "--output-column"),
    overwrite: bool = typer.Option(False, "--overwrite"),
):
    """Round, floor or ceil datetime values."""
    df = load_dataset(input_file)

    result = round_datetime(
        df,
        column,
        frequency=frequency,
        method=method,
        output_column=output_column,
    )

    save_dataset(result, output, overwrite=overwrite)
    console.print(f"[green]Datetime rounding completed.[/green] {output}")