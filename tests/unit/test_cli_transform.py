
"""Tests for the Icebrew transform CLI."""

import pandas as pd
from typer.testing import CliRunner

from icebrew.cli.transform import transform_app

runner = CliRunner()


def create_csv(tmp_path, name, data):
    path = tmp_path / name
    pd.DataFrame(data).to_csv(path, index=False)
    return path


def test_select(tmp_path):
    path = create_csv(
        tmp_path,
        "data.csv",
        {"a": [1, 2], "b": [3, 4]},
    )

    result = runner.invoke(
        transform_app,
        ["select", str(path), "--columns", "a"],
    )

    assert result.exit_code == 0, result.output
    assert "a" in result.output
    assert "b" not in result.output


def test_drop(tmp_path):
    path = create_csv(
        tmp_path,
        "data.csv",
        {"a": [1], "b": [2]},
    )

    result = runner.invoke(
        transform_app,
        ["drop", str(path), "--columns", "b"],
    )

    assert result.exit_code == 0, result.output
    assert "a" in result.output
    assert "b" not in result.output


def test_filter(tmp_path):
    path = create_csv(
        tmp_path,
        "data.csv",
        {"age": [10, 20, 30]},
    )

    result = runner.invoke(
        transform_app,
        [
            "filter",
            str(path),
            "--condition",
            '{"column":"age","operator":">","value":18}',
        ],
    )

    assert result.exit_code == 0, result.output
    assert "20" in result.output
    assert "30" in result.output
    assert "10" not in result.output


def test_filter_invalid_json(tmp_path):
    path = create_csv(tmp_path, "data.csv", {"age": [10]})

    result = runner.invoke(
        transform_app,
        [
            "filter",
            str(path),
            "--condition",
            "invalid-json",
        ],
    )

    assert result.exit_code != 0


def test_sort(tmp_path):
    path = create_csv(
        tmp_path,
        "data.csv",
        {"value": [3, 1, 2]},
    )

    result = runner.invoke(
        transform_app,
        ["sort", str(path), "--columns", "value"],
    )

    assert result.exit_code == 0, result.output


def test_sort_descending(tmp_path):
    path = create_csv(
        tmp_path,
        "data.csv",
        {"value": [1, 2, 3]},
    )

    result = runner.invoke(
        transform_app,
        ["sort", str(path), "--columns", "value", "--descending"],
    )

    assert result.exit_code == 0, result.output


def test_add_column(tmp_path):
    path = create_csv(
        tmp_path,
        "data.csv",
        {"value": [1, 2, 3]},
    )

    result = runner.invoke(
        transform_app,
        [
            "add-column",
            str(path),
            "--column",
            "constant",
            "--value",
            "5",
        ],
    )

    assert result.exit_code == 0, result.output
    assert "constant" in result.output


def test_group(tmp_path):
    path = create_csv(
        tmp_path,
        "data.csv",
        {
            "category": ["A", "A", "B"],
            "value": [10, 20, 30],
        },
    )

    result = runner.invoke(
        transform_app,
        [
            "group",
            str(path),
            "--by",
            "category",
            "--aggregations",
            '{"value":"sum"}',
        ],
    )

    assert result.exit_code == 0, result.output


def test_merge(tmp_path):
    left = create_csv(
        tmp_path,
        "left.csv",
        {"id": [1, 2], "a": [10, 20]},
    )

    right = create_csv(
        tmp_path,
        "right.csv",
        {"id": [1, 2], "b": [30, 40]},
    )

    result = runner.invoke(
        transform_app,
        [
            "merge",
            str(left),
            str(right),
            "--keys",
            "id",
        ],
    )

    assert result.exit_code == 0, result.output


def test_concat(tmp_path):
    left = create_csv(
        tmp_path,
        "left.csv",
        {"value": [1, 2]},
    )

    right = create_csv(
        tmp_path,
        "right.csv",
        {"value": [3, 4]},
    )

    result = runner.invoke(
        transform_app,
        [
            "concat",
            str(left),
            str(right),
        ],
    )

    assert result.exit_code == 0, result.output


def test_concat_invalid_axis(tmp_path):
    left = create_csv(tmp_path, "left.csv", {"value": [1]})
    right = create_csv(tmp_path, "right.csv", {"value": [2]})

    result = runner.invoke(
        transform_app,
        [
            "concat",
            str(left),
            str(right),
            "--axis",
            "3",
        ],
    )

    assert result.exit_code != 0


def test_select_export(tmp_path):
    path = create_csv(
        tmp_path,
        "data.csv",
        {"a": [1, 2], "b": [3, 4]},
    )

    output = tmp_path / "selected.csv"

    result = runner.invoke(
        transform_app,
        [
            "select",
            str(path),
            "--columns",
            "a",
            "--output",
            str(output),
        ],
    )

    assert result.exit_code == 0, result.output
    assert output.exists()

    exported = pd.read_csv(output)
    assert list(exported.columns) == ["a"]


def test_select_missing_file(tmp_path):
    path = tmp_path / "does_not_exist.csv"

    result = runner.invoke(
        transform_app,
        ["select", str(path), "--columns", "a"],
    )

    assert result.exit_code != 0
