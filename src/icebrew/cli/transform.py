
"""CLI commands for dataset transformations."""

import json
from pathlib import Path
from typing import Any

import typer
from rich.console import Console

from icebrew.data.transform import (
    add_column,
    concatenate_data,
    drop_columns,
    filter_rows,
    group_aggregate,
    merge_data,
    select_columns,
    sort_data,
)
from icebrew.cli.utils import (
    load_dataset,
    save_dataset,
    print_dataframe,
)

from icebrew.cli.data import load_dataset, save_dataset, print_dataframe

transform_app = typer.Typer(
    name="transform",
    help="Transform datasets.",
    no_args_is_help=True,
)

console = Console()


def parse_json(value: str, argument_name: str) -> Any:
    """Parse a JSON argument and provide an actionable error."""
    try:
        return json.loads(value)
    except json.JSONDecodeError as exc:
        raise typer.BadParameter(
            f"{argument_name} must contain valid JSON: {exc.msg}"
        ) from exc


def ensure_output(
    df,
    output: str | None,
    overwrite: bool,
) -> None:
    """Display the transformed dataset and optionally export it."""
    print_dataframe(df, title="Transformed Data")

    if output:
        save_dataset(df, output, overwrite=overwrite)
        console.print(
            f"[green]Dataset saved to:[/green] {output}"
        )


@transform_app.command()
def select(
    file: Path = typer.Argument(..., help="Input dataset."),
    columns: str = typer.Option(
        ...,
        "--columns",
        "-c",
        help="Comma-separated column names.",
    ),
    output: str | None = typer.Option(
        None, "--output", "-o", help="Output file."
    ),
    overwrite: bool = typer.Option(
        False, "--overwrite", help="Overwrite output if it exists."
    ),
) -> None:
    """Select columns from a dataset."""

    df = load_dataset(file)
    selected_columns = [c.strip() for c in columns.split(",") if c.strip()]

    if not selected_columns:
        raise typer.BadParameter("At least one column must be specified.")

    result = select_columns(df, selected_columns)
    ensure_output(result, output, overwrite)


@transform_app.command()
def drop(
    file: Path = typer.Argument(..., help="Input dataset."),
    columns: str = typer.Option(
        ...,
        "--columns",
        "-c",
        help="Comma-separated columns to drop.",
    ),
    output: str | None = typer.Option(
        None, "--output", "-o", help="Output file."
    ),
    overwrite: bool = typer.Option(
        False, "--overwrite", help="Overwrite output if it exists."
    ),
) -> None:
    """Drop specified columns."""

    df = load_dataset(file)
    dropped_columns = [c.strip() for c in columns.split(",") if c.strip()]

    if not dropped_columns:
        raise typer.BadParameter("At least one column must be specified.")

    result = drop_columns(df, dropped_columns)
    ensure_output(result, output, overwrite)



@transform_app.command()
def filter(
    file: Path = typer.Argument(..., help="Input dataset."),
    condition: str = typer.Option(
        ...,
        "--condition",
        "-w",
        help=(
            'JSON condition, e.g. '
            '\'{"column":"age","operator":">","value":18}\''
        ),
    ),
    output: str | None = typer.Option(
        None, "--output", "-o", help="Output file."
    ),
    overwrite: bool = typer.Option(
        False, "--overwrite", help="Overwrite output if it exists."
    ),
) -> None:
    """Filter rows using a JSON condition."""

    df = load_dataset(file)
    spec = parse_json(condition, "--condition")

    if not isinstance(spec, dict):
        raise typer.BadParameter("Condition must be a JSON object.")

    required = {"column", "operator"}
    if not required.issubset(spec):
        raise typer.BadParameter(
            "Condition requires 'column' and 'operator'."
        )

    if spec["operator"] not in {"isna", "notna"} and "value" not in spec:
        raise typer.BadParameter(
            "This operator requires a 'value' in the condition."
        )

    conditions = {
        spec["column"]: (
            spec["operator"],
            spec.get("value"),
        )
    }

    result = filter_rows(df, conditions)

    ensure_output(result, output, overwrite)


@transform_app.command()
def sort(
    file: Path = typer.Argument(..., help="Input dataset."),
    columns: str = typer.Option(
        ...,
        "--columns",
        "-c",
        help="Comma-separated sort columns.",
    ),
    descending: bool = typer.Option(
        False,
        "--descending",
        "-d",
        help="Sort in descending order.",
    ),
    output: str | None = typer.Option(
        None, "--output", "-o", help="Output file."
    ),
    overwrite: bool = typer.Option(
        False, "--overwrite", help="Overwrite output if it exists."
    ),
) -> None:
    """Sort a dataset."""

    df = load_dataset(file)
    sort_columns = [c.strip() for c in columns.split(",") if c.strip()]

    if not sort_columns:
        raise typer.BadParameter("At least one sort column is required.")

    result = sort_data(
        df,
        by=sort_columns,
        ascending=not descending,
    )

    ensure_output(result, output, overwrite)



@transform_app.command("add-column")
def add(
    file: Path = typer.Argument(..., help="Input dataset."),
    column: str = typer.Option(
        ...,
        "--column",
        "-c",
        help="Name of the new column.",
    ),
    value: str = typer.Option(
        ...,
        "--value",
        "-v",
        help="JSON value or literal string.",
    ),
    output: str | None = typer.Option(
        None, "--output", "-o", help="Output file."
    ),
    overwrite: bool = typer.Option(
        False, "--overwrite", help="Overwrite output if it exists."
    ),
) -> None:
    """Add a constant-valued column."""

    df = load_dataset(file)

    try:
        parsed_value = json.loads(value)
    except json.JSONDecodeError:
        parsed_value = value

    values = [parsed_value] * len(df)

    result = add_column(
        df,
        name=column,
        values=values,
    )

    ensure_output(result, output, overwrite)

@transform_app.command()
def group(
    file: Path = typer.Argument(..., help="Input dataset."),
    by: str = typer.Option(
        ...,
        "--by",
        help="Comma-separated grouping columns.",
    ),
    aggregations: str = typer.Option(
        ...,
        "--aggregations",
        "-a",
        help=(
            'JSON aggregation mapping, e.g. '
            '\'{"sales":["sum","mean"],"quantity":"sum"}\''
        ),
    ),
    output: str | None = typer.Option(
        None, "--output", "-o", help="Output file."
    ),
    overwrite: bool = typer.Option(
        False, "--overwrite", help="Overwrite output if it exists."
    ),
) -> None:
    """Group a dataset and perform aggregations."""

    df = load_dataset(file)
    grouping_columns = [c.strip() for c in by.split(",") if c.strip()]
    agg_spec = parse_json(aggregations, "--aggregations")

    if not grouping_columns:
        raise typer.BadParameter("At least one grouping column is required.")

    if not isinstance(agg_spec, dict) or not agg_spec:
        raise typer.BadParameter(
            "Aggregations must be a non-empty JSON object."
        )

    result = group_aggregate(
        df,
        by=grouping_columns,
        aggregations=agg_spec,
    )

    ensure_output(result, output, overwrite)


@transform_app.command()
def merge(
    left_file: Path = typer.Argument(..., help="Left dataset."),
    right_file: Path = typer.Argument(..., help="Right dataset."),
    keys: str = typer.Option(
        ...,
        "--keys",
        "-k",
        help="Comma-separated merge key columns.",
    ),
    how: str = typer.Option(
        "inner",
        "--how",
        help="Merge type: inner, left, right, outer.",
    ),
    output: str | None = typer.Option(
        None, "--output", "-o", help="Output file."
    ),
    overwrite: bool = typer.Option(
        False, "--overwrite", help="Overwrite output if it exists."
    ),
) -> None:
    """Merge two datasets."""

    left = load_dataset(left_file)
    right = load_dataset(right_file)
    merge_keys = [k.strip() for k in keys.split(",") if k.strip()]

    if not merge_keys:
        raise typer.BadParameter("At least one merge key is required.")

    if how not in {"inner", "left", "right", "outer"}:
        raise typer.BadParameter(
            "Merge type must be inner, left, right, or outer."
        )

    result = merge_data(
        left,
        right,
        on=merge_keys,
        how=how,
    )

    ensure_output(result, output, overwrite)



@transform_app.command()
def concat(
    left_file: Path = typer.Argument(..., help="First dataset."),
    right_file: Path = typer.Argument(..., help="Second dataset."),
    axis: int = typer.Option(
        0,
        "--axis",
        help="0 for rows, 1 for columns.",
    ),
    output: str | None = typer.Option(
        None, "--output", "-o", help="Output file."
    ),
    overwrite: bool = typer.Option(
        False, "--overwrite", help="Overwrite output if it exists."
    ),
) -> None:
    """Concatenate two datasets."""

    if axis not in (0, 1):
        raise typer.BadParameter("Axis must be 0 or 1.")

    left = load_dataset(left_file)
    right = load_dataset(right_file)

    result = concatenate_data(
        [left, right],
        axis=axis,
    )

    ensure_output(result, output, overwrite)
