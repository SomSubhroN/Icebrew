from typer.testing import CliRunner # type: ignore

from icebrew.cli.app import app

runner = CliRunner()


def test_version_command() -> None:
    result = runner.invoke(app, ["version"])

    assert result.exit_code == 0
    assert "Icebrew" in result.stdout
    assert "1.0.0" in result.stdout