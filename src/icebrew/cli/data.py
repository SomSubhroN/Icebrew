
"""CLI commands for Icebrew data operations."""

from pathlib import Path
import json
from icebrew.data.converter import convert_data
from icebrew.data.validator import validate_data

import pandas as pd
import typer
from rich.console import Console
from rich.table import Table

from icebrew.data.cleaner import clean_data
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


def load_dataset(path: Path) -> pd.DataFrame:
    """Load supported datasets based on their extension."""

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
            f"Required dependency missing for {suffix}: {exc}"
        ) from exc
    except Exception as exc:
        raise typer.BadParameter(f"Could not load dataset: {exc}") from exc

    raise typer.BadParameter(
        f"Unsupported format: {suffix}. "
        "Supported formats: CSV, JSON, JSONL, XLSX, Parquet."
    )


def save_dataset(
    df: pd.DataFrame,
    output: Path | None,
    *,
    overwrite: bool = False,
) -> None:
    """Save a dataset only when an output path is explicitly provided."""

    if output is None:
        console.print(
            "[yellow]No output path specified. "
            "The source dataset was not modified.[/yellow]"
        )
        return

    try:
        export_data(
            df,
            output,
            overwrite=overwrite,
        )
    except Exception as exc:
        raise typer.BadParameter(f"Export failed: {exc}") from exc

    console.print(f"[green]Saved:[/green] {output}")


def print_dataframe(
    df: pd.DataFrame,
    *,
    title: str = "Data",
    max_rows: int = 20,
) -> None:
    """Display a DataFrame using Rich."""

    table = Table(title=title)

    for column in df.columns:
        table.add_column(str(column))

    displayed = df.head(max_rows)

    for _, row in displayed.iterrows():
        table.add_row(*(str(value) for value in row.values))

    console.print(table)

    if len(df) > max_rows:
        console.print(
            f"[dim]Showing {max_rows} of {len(df)} rows.[/dim]"
        )


def print_dict(data: dict, *, title: str = "Report") -> None:
    """Display dictionary data in a two-column table."""

    table = Table(title=title)
    table.add_column("Property", style="cyan")
    table.add_column("Value")

    for key, value in data.items():
        if isinstance(value, (dict, list)):
            value = json.dumps(value, default=str, indent=2)

        table.add_row(str(key), str(value))

    console.print(table)


# --------------------------------------------------
# LOAD
# --------------------------------------------------

@data_app.command("load")
def load_command(
    file: Path = typer.Argument(..., help="Dataset path."),
):
    """Load a dataset and display a preview."""

    df = load_dataset(file)

    console.print(
        f"[green]Loaded {len(df)} rows and {len(df.columns)} columns.[/green]"
    )

    print_dataframe(df.head(10), title=str(file))


# --------------------------------------------------
# INSPECT
# --------------------------------------------------

@data_app.command("inspect")
def inspect_command(
    file: Path = typer.Argument(..., help="Dataset path."),
    preview: int = typer.Option(5, "--preview", "-n", min=0),
):
    """Inspect dataset structure and preview."""

    df = load_dataset(file)
    report = inspect_data(df, preview_rows=preview)

    console.print(f"[bold cyan]Dataset:[/bold cyan] {file}")
    console.print(f"[bold]Shape:[/bold] {report['shape']}")
    console.print(f"[bold]Memory:[/bold] {report['memory_usage']}")
    console.print(f"[bold]Duplicates:[/bold] {report['duplicates']}")

    print_dataframe(
        pd.DataFrame(
            {
                "column": report["columns"],
                "dtype": report["dtypes"],
                "missing": [
                    report["missing"][column]
                    for column in report["columns"]
                ],
            }
        ),
        title="Column Overview",
    )

    print_dataframe(
        report["preview"],
        title="Preview",
        max_rows=max(preview, 1),
    )


# --------------------------------------------------
# PROFILE
# --------------------------------------------------

@data_app.command("profile")
def profile_command(
    file: Path = typer.Argument(..., help="Dataset path."),
    top: int = typer.Option(5, "--top", min=1),
):
    """Profile dataset columns."""

    df = load_dataset(file)
    report = profile_data(df, top_n=top)

    table = Table(title="Dataset Profile")
    table.add_column("Column")
    table.add_column("Type")
    table.add_column("Count")
    table.add_column("Missing")
    table.add_column("Unique")
    table.add_column("Statistics")

    for column, details in report.items():
        statistics = {
            key: value
            for key, value in details.items()
            if key not in {
                "position",
                "dtype",
                "count",
                "missing",
                "missing_percent",
                "unique",
            }
        }

        table.add_row(
            str(column),
            str(details.get("dtype")),
            str(details.get("count")),
            f"{details.get('missing')} "
            f"({details.get('missing_percent', 0):.2f}%)",
            str(details.get("unique")),
            json.dumps(statistics, default=str),
        )

    console.print(table)


# --------------------------------------------------
# QUALITY
# --------------------------------------------------

@data_app.command("quality")
def quality_command(
    file: Path = typer.Argument(..., help="Dataset path."),
):
    """Analyze dataset quality."""

    df = load_dataset(file)
    report = analyze_quality(df)

    print_dict(
        {
            key: value
            for key, value in report.items()
            if key != "columns"
        },
        title="Quality Summary",
    )

    if "columns" in report:
        print_dict(report["columns"], title="Column Quality")


# --------------------------------------------------
# MISSING
# --------------------------------------------------

@data_app.command("missing")
def missing_command(
    file: Path = typer.Argument(..., help="Dataset path."),
):
    """Analyze missing values."""

    df = load_dataset(file)
    report = analyze_missing(df)

    print_dict(report, title="Missing Data Analysis")


# --------------------------------------------------
# SAMPLE
# --------------------------------------------------

@data_app.command("sample")
def sample_command(
    file: Path = typer.Argument(..., help="Dataset path."),
    n: int | None = typer.Option(None, "--n", min=1),
    fraction: float | None = typer.Option(None, "--fraction", min=0, max=1),
    seed: int | None = typer.Option(None, "--seed"),
    output: Path | None = typer.Option(None, "--output", "-o"),
    overwrite: bool = typer.Option(False, "--overwrite"),
):
    """Randomly sample a dataset."""

    if n is not None and fraction is not None:
        raise typer.BadParameter("Use either --n or --fraction, not both.")

    if n is None and fraction is None:
        raise typer.BadParameter("Specify --n or --fraction.")

    df = load_dataset(file)

    sampled = sample_data(
        df,
        n=n,
        fraction=fraction,
        random_state=seed,
    )

    console.print(
        f"[green]Sampled {len(sampled)} rows from {len(df)} rows.[/green]"
    )

    print_dataframe(sampled, title="Sample", max_rows=20)

    save_dataset(sampled, output, overwrite=overwrite)


# --------------------------------------------------
# CLEAN
# --------------------------------------------------

@data_app.command("clean")
def clean_command(
    file: Path = typer.Argument(..., help="Dataset path."),
    drop_duplicates: bool = typer.Option(False, "--drop-duplicates"),
    drop_empty_rows: bool = typer.Option(False, "--drop-empty-rows"),
    drop_empty_columns: bool = typer.Option(False, "--drop-empty-columns"),
    trim_whitespace: bool = typer.Option(False, "--trim-whitespace"),
    output: Path | None = typer.Option(None, "--output", "-o"),
    overwrite: bool = typer.Option(False, "--overwrite"),
):
    """Apply selected non-destructive cleaning operations."""

    df = load_dataset(file)

    cleaned = clean_data(
        df,
        drop_duplicates=drop_duplicates,
        drop_empty_rows=drop_empty_rows,
        drop_empty_columns=drop_empty_columns,
        trim_whitespace=trim_whitespace,
    )

    console.print(
        f"Original shape: [cyan]{df.shape}[/cyan]"
    )
    console.print(
        f"Cleaned shape: [green]{cleaned.shape}[/green]"
    )

    print_dataframe(cleaned.head(10), title="Cleaned Preview")

    save_dataset(cleaned, output, overwrite=overwrite)


# --------------------------------------------------
# FREQUENCIES
# --------------------------------------------------

@data_app.command("frequencies")
def frequencies_command(
    file: Path = typer.Argument(..., help="Dataset path."),
    column: str = typer.Option(..., "--column", "-c"),
    normalize: bool = typer.Option(False, "--normalize"),
    top: int | None = typer.Option(None, "--top", min=1),
    output: Path | None = typer.Option(None, "--output", "-o"),
    overwrite: bool = typer.Option(False, "--overwrite"),
):
    """Calculate frequencies for a column."""

    df = load_dataset(file)

    result = value_counts(
        df,
        column,
        normalize=normalize,
        top_n=top,
    )

    print_dataframe(result.reset_index(), title=f"Frequencies: {column}")

    save_dataset(result.reset_index(), output, overwrite=overwrite)


# --------------------------------------------------
# CROSSTAB
# --------------------------------------------------

@data_app.command("crosstab")
def crosstab_command(
    file: Path = typer.Argument(..., help="Dataset path."),
    index: str = typer.Option(..., "--index", "-i"),
    columns: str = typer.Option(..., "--columns", "-c"),
    normalize: str | None = typer.Option(
        None,
        "--normalize",
        help="all, index, or columns",
    ),
    margins: bool = typer.Option(False, "--margins"),
    output: Path | None = typer.Option(None, "--output", "-o"),
    overwrite: bool = typer.Option(False, "--overwrite"),
):
    """Generate a contingency table."""

    if normalize not in {None, "all", "index", "columns"}:
        raise typer.BadParameter(
            "--normalize must be all, index, or columns."
        )

    df = load_dataset(file)

    result = crosstab(
        df,
        index,
        columns,
        normalize=normalize if normalize else False,
        margins=margins,
    )

    print_dataframe(
        result.reset_index(),
        title=f"Crosstab: {index} × {columns}",
    )

    save_dataset(
        result.reset_index(),
        output,
        overwrite=overwrite,
    )


# --------------------------------------------------
# EXPORT
# --------------------------------------------------

@data_app.command("export")
def export_command(
    file: Path = typer.Argument(..., help="Source dataset."),
    output: Path = typer.Argument(..., help="Destination path."),
    overwrite: bool = typer.Option(False, "--overwrite"),
):
    """Convert a dataset to another supported format."""

    df = load_dataset(file)

    save_dataset(
        df,
        output,
        overwrite=overwrite,
    )


# --------------------------------------------------
# CONVERT
# --------------------------------------------------

@data_app.command("convert")
def convert_command(
    file: Path = typer.Argument(..., help="Dataset path."),
    specification: Path = typer.Option(
        ...,
        "--spec",
        help="JSON file containing conversion specifications.",
    ),
    output: Path | None = typer.Option(None, "--output", "-o"),
    errors: str = typer.Option("raise", "--errors"),
    overwrite: bool = typer.Option(False, "--overwrite"),
):
    """Convert dataset column types using a JSON specification."""

    if errors not in {"raise", "coerce", "ignore"}:
        raise typer.BadParameter(
            "--errors must be raise, coerce, or ignore."
        )

    if not specification.exists():
        raise typer.BadParameter(
            f"Specification file not found: {specification}"
        )

    try:
        conversions = json.loads(
            specification.read_text(encoding="utf-8")
        )
    except Exception as exc:
        raise typer.BadParameter(
            f"Could not read conversion specification: {exc}"
        ) from exc

    if not isinstance(conversions, dict):
        raise typer.BadParameter(
            "Conversion specification must be a JSON object."
        )

    df = load_dataset(file)

    converted = convert_data(
        df,
        conversions,
        errors=errors,
    )

    print_dataframe(
        converted.head(10),
        title="Converted Preview",
    )

    save_dataset(
        converted,
        output,
        overwrite=overwrite,
    )


# --------------------------------------------------
# VALIDATE
# --------------------------------------------------

@data_app.command("validate")
def validate_command(
    file: Path = typer.Argument(..., help="Dataset path."),
    specification: Path = typer.Option(
        ...,
        "--spec",
        help="JSON file containing validation rules.",
    ),
):
    """Validate a dataset against a JSON specification."""

    if not specification.exists():
        raise typer.BadParameter(
            f"Specification file not found: {specification}"
        )

    try:
        rules = json.loads(
            specification.read_text(encoding="utf-8")
        )
    except Exception as exc:
        raise typer.BadParameter(
            f"Could not read validation specification: {exc}"
        ) from exc

    if not isinstance(rules, dict):
        raise typer.BadParameter(
            "Validation specification must be a JSON object."
        )

    df = load_dataset(file)

    report = validate_data(
        df,
        **rules,
    )

    print_dict(report, title="Validation Report")

    if not report.get("valid", False):
        console.print("[bold red]Dataset validation failed.[/bold red]")
        raise typer.Exit(code=1)

    console.print("[bold green]Dataset validation passed.[/bold green]")
