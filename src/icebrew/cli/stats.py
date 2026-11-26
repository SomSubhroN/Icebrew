
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import typer

from icebrew.cli.utils import load_dataset, print_dict
from icebrew.stats.descriptive import describe_numeric
from icebrew.stats.correlation import correlation, correlation_matrix
from icebrew.stats.confidence import (
    mean_confidence_interval,
    proportion_confidence_interval,
)
from icebrew.stats.effect_size import cohens_d, hedges_g
from icebrew.stats.hypothesis import (
    one_sample_t_test,
    one_sample_z_test,
)
from icebrew.stats.independent import independent_t_test
from icebrew.stats.paired import paired_t_test, wilcoxon_signed_rank_test
from icebrew.stats.nonparametric import (
    mann_whitney_u_test,
    kruskal_wallis_test,
)

stats_app = typer.Typer(
    name="stats",
    help="Statistical analysis tools.",
    no_args_is_help=True,
)


def _load_column(file_path: str, column: str) -> pd.Series:
    df = load_dataset(file_path)

    if column not in df.columns:
        raise typer.BadParameter(
            f"Column '{column}' not found in dataset."
        )

    series = df[column]

    if isinstance(series, pd.DataFrame):
        raise typer.BadParameter(
            f"Column '{column}' is duplicated in the dataset."
        )

    return series


def _load_columns(file_path: str, columns: list[str]) -> pd.DataFrame:
    df = load_dataset(file_path)

    missing = [column for column in columns if column not in df.columns]

    if missing:
        raise typer.BadParameter(
            f"Columns not found: {', '.join(missing)}"
        )

    selected = df.loc[:, columns]

    if selected.columns.has_duplicates:
        raise typer.BadParameter(
            "Selected columns must be unique."
        )

    return selected


def _emit(result: Any, json_output: bool) -> None:
    if json_output:
        typer.echo(
            json.dumps(
                result,
                indent=2,
                ensure_ascii=False,
                default=_json_default,
            )
        )
    else:
        print_dict(result)


def _json_default(value: Any) -> Any:
    if isinstance(value, (np.integer,)):
        return int(value)

    if isinstance(value, (np.floating,)):
        return float(value)

    if isinstance(value, (np.bool_,)):
        return bool(value)

    if isinstance(value, (np.ndarray,)):
        return value.tolist()

    if isinstance(value, (pd.Series,)):
        return value.tolist()

    if isinstance(value, (pd.Timestamp,)):
        return value.isoformat()

    if isinstance(value, Path):
        return str(value)

    raise TypeError(f"Cannot serialize {type(value).__name__}")


@stats_app.command("describe")
def describe(
    file_path: str = typer.Argument(..., help="Dataset path."),
    columns: list[str] | None = typer.Option(
        None, "--column", "-c", help="Column to describe. Repeat as needed."
    ),
    json_output: bool = typer.Option(
        False, "--json", help="Output JSON."
    ),
):
    """Calculate descriptive statistics."""

    df = load_dataset(file_path)

    if columns is None:
        columns = list(df.select_dtypes(include="number").columns)

    if not columns:
        raise typer.BadParameter(
            "No numeric columns available for descriptive statistics."
        )

    results = {}

    for column in columns:
        if column not in df.columns:
            raise typer.BadParameter(
                f"Column '{column}' not found."
            )

        if isinstance(df[column], pd.DataFrame):
            raise typer.BadParameter(
                f"Column '{column}' is duplicated."
            )

        results[column] = describe_numeric(df[column]).copy()

    _emit(results, json_output)


@stats_app.command("correlation")
def correlation_command(
    file_path: str = typer.Argument(..., help="Dataset path."),
    x: str | None = typer.Option(None, "--x", help="First variable."),
    y: str | None = typer.Option(None, "--y", help="Second variable."),
    columns: list[str] | None = typer.Option(
        None, "--column", "-c", help="Column for matrix. Repeat as needed."
    ),
    method: str = typer.Option(
        "pearson", "--method", help="pearson, spearman, or kendall."
    ),
    json_output: bool = typer.Option(
        False, "--json", help="Output JSON."
    ),
):
    """Calculate pairwise correlation or a correlation matrix."""

    if x is not None or y is not None:
        if x is None or y is None:
            raise typer.BadParameter(
                "Both --x and --y must be supplied."
            )

        left = _load_column(file_path, x)
        right = _load_column(file_path, y)

        result = correlation(
            left,
            right,
            method=method,
        )

        _emit(result, json_output)
        return

    if columns is None:
        df = load_dataset(file_path)
        columns = list(df.select_dtypes(include="number").columns)

    if len(columns) < 2:
        raise typer.BadParameter(
            "At least two columns are required for a correlation matrix."
        )

    df = _load_columns(file_path, columns)

    result = correlation_matrix(
        df,
        columns=columns,
        method=method,
    )

    _emit(result.to_dict(), json_output)


@stats_app.command("ci-mean")
def ci_mean(
    file_path: str = typer.Argument(..., help="Dataset path."),
    column: str = typer.Option(..., "--column", "-c"),
    confidence: float = typer.Option(
        0.95, "--confidence", help="Confidence level (0-1)."
    ),
    json_output: bool = typer.Option(
        False, "--json", help="Output JSON."
    ),
):
    """Calculate a confidence interval for the population mean."""

    data = _load_column(file_path, column)

    result = mean_confidence_interval(
        data,
        confidence=confidence,
    )

    _emit(result, json_output)


@stats_app.command("ci-proportion")
def ci_proportion(
    successes: int = typer.Option(..., "--successes"),
    trials: int = typer.Option(..., "--trials"),
    confidence: float = typer.Option(
        0.95, "--confidence", help="Confidence level (0-1)."
    ),
    json_output: bool = typer.Option(
        False, "--json", help="Output JSON."
    ),
):
    """Calculate a Wilson confidence interval for a proportion."""

    result = proportion_confidence_interval(
        successes,
        trials,
        confidence=confidence,
    )

    _emit(result, json_output)


@stats_app.command("effect-size")
def effect_size(
    file_path: str = typer.Argument(..., help="Dataset path."),
    group1: str = typer.Option(..., "--group1"),
    group2: str = typer.Option(..., "--group2"),
    method: str = typer.Option(
        "cohens-d",
        "--method",
        help="cohens-d or hedges-g.",
    ),
    equal_var: bool = typer.Option(
        True,
        "--equal-var/--unequal-var",
        help="Use pooled standard deviation for Cohen's d.",
    ),
    json_output: bool = typer.Option(
        False, "--json", help="Output JSON."
    ),
):
    """Calculate an effect size between two groups."""

    a = _load_column(file_path, group1)
    b = _load_column(file_path, group2)

    if method == "cohens-d":
        result = cohens_d(a, b, equal_var=equal_var)
    elif method == "hedges-g":
        result = hedges_g(a, b)
    else:
        raise typer.BadParameter(
            "Method must be 'cohens-d' or 'hedges-g'."
        )

    _emit(
        {
            "method": method,
            "group1": group1,
            "group2": group2,
            "result": result,
        },
        json_output,
    )


@stats_app.command("test-one")
def test_one(
    file_path: str = typer.Argument(..., help="Dataset path."),
    column: str = typer.Option(..., "--column", "-c"),
    population_mean: float = typer.Option(
        0.0, "--mean", help="Null hypothesis mean."
    ),
    test: str = typer.Option(
        "t", "--test", help="t or z."
    ),
    population_std: float | None = typer.Option(
        None, "--population-std", help="Required for z-test."
    ),
    alternative: str = typer.Option(
        "two-sided", "--alternative"
    ),
    confidence: float = typer.Option(
        0.95, "--confidence"
    ),
    json_output: bool = typer.Option(
        False, "--json", help="Output JSON."
    ),
):
    """Perform a one-sample t-test or z-test."""

    data = _load_column(file_path, column)

    if test == "t":
        result = one_sample_t_test(
            data,
            population_mean,
            alternative=alternative,
            confidence=confidence,
        )
    elif test == "z":
        if population_std is None:
            raise typer.BadParameter(
                "--population-std is required for a z-test."
            )

        result = one_sample_z_test(
            data,
            population_mean,
            population_std=population_std,
            alternative=alternative,
            confidence=confidence,
        )
    else:
        raise typer.BadParameter(
            "Test must be 't' or 'z'."
        )

    _emit(result, json_output)


@stats_app.command("test-independent")
def test_independent(
    file_path: str = typer.Argument(..., help="Dataset path."),
    group1: str = typer.Option(..., "--group1"),
    group2: str = typer.Option(..., "--group2"),
    equal_var: bool = typer.Option(
        False,
        "--equal-var/--unequal-var",
        help="Student's t-test or Welch's t-test.",
    ),
    alternative: str = typer.Option(
        "two-sided", "--alternative"
    ),
    confidence: float = typer.Option(
        0.95, "--confidence"
    ),
    json_output: bool = typer.Option(
        False, "--json", help="Output JSON."
    ),
):
    """Perform an independent-samples t-test."""

    a = _load_column(file_path, group1)
    b = _load_column(file_path, group2)

    result = independent_t_test(
        a,
        b,
        equal_var=equal_var,
        alternative=alternative,
        confidence=confidence,
    )

    _emit(result, json_output)


@stats_app.command("test-paired")
def test_paired(
    file_path: str = typer.Argument(..., help="Dataset path."),
    before: str = typer.Option(..., "--before"),
    after: str = typer.Option(..., "--after"),
    test: str = typer.Option(
        "t", "--test", help="t or wilcoxon."
    ),
    alternative: str = typer.Option(
        "two-sided", "--alternative"
    ),
    confidence: float = typer.Option(
        0.95, "--confidence"
    ),
    json_output: bool = typer.Option(
        False, "--json", help="Output JSON."
    ),
):
    """Perform a paired t-test or Wilcoxon signed-rank test."""

    a = _load_column(file_path, before)
    b = _load_column(file_path, after)

    if test == "t":
        result = paired_t_test(
            a,
            b,
            alternative=alternative,
            confidence=confidence,
        )
    elif test == "wilcoxon":
        result = wilcoxon_signed_rank_test(
            a,
            b,
            alternative=alternative,
            confidence=confidence,
        )
    else:
        raise typer.BadParameter(
            "Test must be 't' or 'wilcoxon'."
        )

    _emit(result, json_output)


@stats_app.command("mann-whitney")
def mann_whitney(
    file_path: str = typer.Argument(..., help="Dataset path."),
    group1: str = typer.Option(..., "--group1"),
    group2: str = typer.Option(..., "--group2"),
    alternative: str = typer.Option(
        "two-sided", "--alternative"
    ),
    confidence: float = typer.Option(
        0.95, "--confidence"
    ),
    method: str = typer.Option(
        "auto", "--method", help="SciPy calculation method."
    ),
    json_output: bool = typer.Option(
        False, "--json", help="Output JSON."
    ),
):
    """Perform a Mann-Whitney U test."""

    a = _load_column(file_path, group1)
    b = _load_column(file_path, group2)

    result = mann_whitney_u_test(
        a,
        b,
        alternative=alternative,
        confidence=confidence,
        method=method,
    )

    _emit(result, json_output)


@stats_app.command("kruskal")
def kruskal(
    file_path: str = typer.Argument(..., help="Dataset path."),
    columns: list[str] = typer.Option(
        ..., "--column", "-c", help="Group column. Repeat at least twice."
    ),
    json_output: bool = typer.Option(
        False, "--json", help="Output JSON."
    ),
):
    """Perform a Kruskal-Wallis test across multiple groups."""

    if len(columns) < 2:
        raise typer.BadParameter(
            "At least two group columns must be supplied."
        )

    df = _load_columns(file_path, columns)

    groups = {
        column: df[column]
        for column in columns
    }

    result = kruskal_wallis_test(groups)

    _emit(result, json_output)
