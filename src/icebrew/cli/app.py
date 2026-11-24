"""Icebrew command-line application."""

import platform
import sys
from icebrew.diagnostics.engine import run_diagnostics

import typer
from rich.console import Console

from icebrew import __version__

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

    console.print(
        f"[bold cyan]Icebrew[/bold cyan] [green]{__version__}[/green]"
    )

@app.command()
def doctor() -> None:
    """Diagnose the Icebrew environment."""

    results = run_diagnostics()

    console.print()
    console.print("[bold cyan]Icebrew Doctor[/bold cyan]")
    console.print()

    status_styles = {
        "PASS": "green",
        "WARN": "yellow",
        "FAIL": "red",
        "SKIP": "dim",
        "INFO": "blue",
    }

    failures = 0
    warnings = 0

    for result in results:

        style = status_styles.get(result.status, "white")

        console.print(
            f"[{style}]{result.status}[/{style}] "
            f"[bold]{result.name}[/bold]: {result.message}"
        )

        if result.status == "FAIL":
            failures += 1

        elif result.status == "WARN":
            warnings += 1

    console.print()

    if failures:

        console.print(
            f"[bold red]Diagnostics failed: "
            f"{failures} failure(s), {warnings} warning(s).[/bold red]"
        )

        raise typer.Exit(code=1)

    if warnings:

        console.print(
            f"[bold yellow]Diagnostics completed with "
            f"{warnings} warning(s).[/bold yellow]"
        )

    else:

        console.print(
            "[bold green]Diagnostics completed successfully.[/bold green]"
        )

    console.print()


@app.command()
def info() -> None:
    """Display information about Icebrew and the runtime."""

    console.print()
    console.print("[bold cyan]Icebrew[/bold cyan]")
    console.print("Brew your experiments.")
    console.print()

    console.print(f"[bold]Version:[/bold] {__version__}")
    console.print(f"[bold]Python:[/bold] {sys.version.split()[0]}")
    console.print(f"[bold]Python executable:[/bold] {sys.executable}")
    console.print(f"[bold]Operating system:[/bold] {platform.system()}")
    console.print(f"[bold]OS release:[/bold] {platform.release()}")
    console.print(f"[bold]Architecture:[/bold] {platform.machine()}")

    console.print()
    console.print("[dim]Local-first computational research toolkit.[/dim]")
    console.print()


if __name__ == "__main__":
    app()
