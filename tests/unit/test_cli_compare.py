
from typer.testing import CliRunner
import pandas as pd

from icebrew.cli.data import data_app

runner = CliRunner()


def test_compare_help():
    result = runner.invoke(data_app, ["compare", "--help"])
    assert result.exit_code == 0
    assert "Compare two datasets" in result.output


def test_compare_cli(tmp_path):
    a = pd.DataFrame({"x": [1, 2], "category": ["a", "b"]})
    b = pd.DataFrame({"x": [2, 3], "category": ["b", "c"]})

    file_a = tmp_path / "a.csv"
    file_b = tmp_path / "b.csv"

    a.to_csv(file_a, index=False)
    b.to_csv(file_b, index=False)

    result = runner.invoke(
        data_app,
        ["compare", str(file_a), str(file_b)],
    )

    assert result.exit_code == 0, result.output
    assert "Dataset Comparison Summary" in result.output
    assert "Schema Comparison" in result.output


def test_compare_with_rows(tmp_path):
    a = pd.DataFrame({"x": [1, 2]})
    b = pd.DataFrame({"x": [1, 3]})

    file_a = tmp_path / "a.csv"
    file_b = tmp_path / "b.csv"

    a.to_csv(file_a, index=False)
    b.to_csv(file_b, index=False)

    result = runner.invoke(
        data_app,
        ["compare", str(file_a), str(file_b), "--rows"],
    )

    assert result.exit_code == 0, result.output
    assert "Positional Row Comparison" in result.output


def test_compare_json_export(tmp_path):
    a = pd.DataFrame({"x": [1, 2]})
    b = pd.DataFrame({"x": [2, 3]})

    file_a = tmp_path / "a.csv"
    file_b = tmp_path / "b.csv"
    report_file = tmp_path / "report.json"

    a.to_csv(file_a, index=False)
    b.to_csv(file_b, index=False)

    result = runner.invoke(
        data_app,
        [
            "compare",
            str(file_a),
            str(file_b),
            "--json",
            str(report_file),
        ],
    )

    assert result.exit_code == 0, result.output
    assert report_file.exists()


def test_compare_json_no_overwrite(tmp_path):
    a = pd.DataFrame({"x": [1]})
    b = pd.DataFrame({"x": [2]})

    file_a = tmp_path / "a.csv"
    file_b = tmp_path / "b.csv"
    report_file = tmp_path / "report.json"

    a.to_csv(file_a, index=False)
    b.to_csv(file_b, index=False)

    report_file.write_text("existing", encoding="utf-8")

    result = runner.invoke(
        data_app,
        [
            "compare",
            str(file_a),
            str(file_b),
            "--json",
            str(report_file),
        ],
    )

    assert result.exit_code != 0
    assert report_file.read_text(encoding="utf-8") == "existing"
