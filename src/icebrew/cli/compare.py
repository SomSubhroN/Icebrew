
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import typer
from rich.console import Console
from rich.table import Table

from icebrew.cli.utils import load_dataset
from icebrew.data.comparison import compare_datasets

console = Console()


def _write_json(report: dict[str, Any], output: Path) -> None:
    """Write a comparison report to JSON without silently overwriting."""
    if output.exists():
        raise typer.BadParameter(
            f"Report already exists: {output}. Choose another path."
        )

    output.parent.mkdir(parents=True, exist_ok=True)

    try:
        with output.open("x", encoding="utf-8") as file:
            json.dump(report, file, indent=2, ensure_ascii=False, default=str)
    except FileExistsError as exc:
        raise typer.BadParameter(
            f"Report already exists: {output}."
        ) from exc


def _display_summary(report: dict[str, Any]) -> None:
    summary = report["summary"]

    table = Table(title="Dataset Comparison Summary")
    table.add_column("Metric", style="cyan")
    table.add_column("Dataset A")
    table.add_column("Dataset B")
    table.add_column("Difference")

    table.add_row(
        "Rows",
        str(summary["left_shape"][0]),
        str(summary["right_shape"][0]),
        str(summary["row_difference"]),
    )

    table.add_row(
        "Columns",
        str(summary["left_shape"][1]),
        str(summary["right_shape"][1]),
        str(summary["column_difference"]),
    )

    table.add_row(
        "Duplicate rows",
        str(summary["left_duplicate_rows"]),
        str(summary["right_duplicate_rows"]),
        str(
            summary["right_duplicate_rows"]
            - summary["left_duplicate_rows"]
        ),
    )

    console.print(table)


def _display_schema(report: dict[str, Any]) -> None:
    schema = report["schema"]

    table = Table(title="Schema Comparison")
    table.add_column("Property", style="cyan")
    table.add_column("Details", overflow="fold")

    table.add_row(
        "Common columns",
        ", ".join(map(str, schema["common_columns"])) or "None",
    )
    table.add_row(
        "A-only columns",
        ", ".join(map(str, schema["left_only_columns"])) or "None",
    )
    table.add_row(
        "B-only columns",
        ", ".join(map(str, schema["right_only_columns"])) or "None",
    )
    table.add_row(
        "Column order identical",
        str(schema["column_order_identical"]),
    )

    console.print(table)

    if schema["dtype_differences"]:
        dtype_table = Table(title="Data Type Differences")
        dtype_table.add_column("Column", style="cyan")
        dtype_table.add_column("Dataset A")
        dtype_table.add_column("Dataset B")

        for column, details in schema["dtype_differences"].items():
            dtype_table.add_row(
                str(column),
                details["left"],
                details["right"],
            )

        console.print(dtype_table)


def _display_columns(report: dict[str, Any]) -> None:
    table = Table(title="Common Column Analysis")
    table.add_column("Column", style="cyan")
    table.add_column("Missing A")
    table.add_column("Missing B")
    table.add_column("Missing Δ")
    table.add_column("Unique A")
    table.add_column("Unique B")

    for column, details in report["columns"].items():
        table.add_row(
            str(column),
            str(details["left"]["missing"]),
            str(details["right"]["missing"]),
            str(details["missing_difference"]["count"]),
            str(details["left"]["unique"]),
            str(details["right"]["unique"]),
        )

    console.print(table)


def _display_numeric(report: dict[str, Any]) -> None:
    table = Table(title="Numeric Comparisons")
    table.add_column("Column", style="cyan")
    table.add_column("Mean A")
    table.add_column("Mean B")
    table.add_column("Mean Δ")
    table.add_column("Median Δ")

    found = False

    for column, details in report["columns"].items():
        numeric = details.get("numeric")

        if numeric is None:
            continue

        found = True
        difference = numeric["difference"]

        table.add_row(
            str(column),
            str(numeric["left"]["mean"]),
            str(numeric["right"]["mean"]),
            str(difference["mean"]),
            str(difference["median"]),
        )

    if found:
        console.print(table)


def _display_row_comparison(report: dict[str, Any]) -> None:
    row_report = report.get("row_comparison")

    if row_report is None:
        return

    table = Table(title="Positional Row Comparison")
    table.add_column("Metric", style="cyan")
    table.add_column("Value")

    table.add_row("Rows compared", str(row_report["rows_compared"]))
    table.add_row("Columns compared", str(row_report["columns_compared"]))
    table.add_row("Differing rows", str(row_report["differing_rows"]))
    table.add_row("Different cells", str(row_report["different_cells"]))
    table.add_row(
        "Cell difference (%)",
        f"{row_report['cell_difference_percentage']:.2f}%",
    )

    console.print(table)
    console.print(
        f"[yellow]{row_report['warning']}[/yellow]"
    )


def compare(
    dataset_a: Path = typer.Argument(..., help="First dataset."),
    dataset_b: Path = typer.Argument(..., help="Second dataset."),
    top_n: int = typer.Option(
        10, "--top", min=1, help="Top category values to compare."
    ),
    distributions: bool = typer.Option(
        True,
        "--distributions/--no-distributions",
        help="Include categorical distributions.",
    ),
    rows: bool = typer.Option(
        False,
        "--rows",
        help="Compare rows positionally using common columns.",
    ),
    json_output: Path | None = typer.Option(
        None,
        "--json",
        help="Optional path to save the full JSON report.",
    ),
):
    """Compare two datasets descriptively."""
    left = load_dataset(dataset_a)
    right = load_dataset(dataset_b)

    report = compare_datasets(
        left,
        right,
        top_n=top_n,
        include_distributions=distributions,
        compare_rows=rows,
    )

    _display_summary(report)
    _display_schema(report)
    _display_columns(report)
    _display_numeric(report)
    _display_row_comparison(report)

    if json_output is not None:
        _write_json(report, json_output)
        console.print(
            f"[green]JSON comparison report saved:[/green] {json_output}"
        )




