
"""Icebrew command-line application."""

import typer # type: ignore
from rich.console import Console

app = typer.Typer(
    name="icebrew",
    help="Brew your experiments.",
    no_args_is_help=True,
)

console = Console()


@app.callback()
def main() -> None:
    """Icebrew: a local-first computational research toolkit."""


@app.command()
def version() -> None:
    """Display the Icebrew version."""

    from icebrew import __version__

    console.print(f"[bold cyan]Icebrew[/bold cyan] [green]{__version__}[/green]")


if __name__ == "__main__":
    app()
