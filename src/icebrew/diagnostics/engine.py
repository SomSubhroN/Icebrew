"""Basic Icebrew diagnostic engine."""

import importlib.util
import sys

from icebrew import __version__
from icebrew.diagnostics.result import DiagnosticResult


def check_python_version() -> DiagnosticResult:
    """Check whether the current Python version is supported."""

    major = sys.version_info.major
    minor = sys.version_info.minor

    if major == 3 and 12 <= minor < 15:
        return DiagnosticResult(
            name="Python version",
            status="PASS",
            message=f"Python {major}.{minor} is supported.",
        )

    return DiagnosticResult(
        name="Python version",
        status="FAIL",
        message=f"Unsupported Python version: {major}.{minor}.",
    )


def check_python_executable() -> DiagnosticResult:
    """Report the Python executable currently running Icebrew."""

    return DiagnosticResult(
        name="Python executable",
        status="INFO",
        message=sys.executable,
    )


def check_icebrew_import() -> DiagnosticResult:
    """Check whether Icebrew can be imported."""

    try:
        import icebrew

        version = icebrew.__version__

        return DiagnosticResult(
            name="Icebrew package",
            status="PASS",
            message=f"Icebrew {version} is importable.",
        )

    except Exception as exc:
        return DiagnosticResult(
            name="Icebrew package",
            status="FAIL",
            message=f"Import failed: {exc}",
        )


def check_core_dependencies() -> DiagnosticResult:
    """Check whether the core dependencies are importable."""

    dependencies = {
        "typer": "typer",
        "rich": "rich",
        "pydantic": "pydantic",
        "PyYAML": "yaml",
    }

    missing = []

    for package_name, module_name in dependencies.items():

        try:
            available = importlib.util.find_spec(module_name) is not None

        except (ImportError, ValueError):
            available = False

        if not available:
            missing.append(package_name)

    if missing:

        return DiagnosticResult(
            name="Core dependencies",
            status="FAIL",
            message=f"Missing dependencies: {', '.join(missing)}.",
        )

    return DiagnosticResult(
        name="Core dependencies",
        status="PASS",
        message="All core dependencies are available.",
    )


def check_version_consistency() -> DiagnosticResult:
    """Check whether the reported package version is accessible."""

    return DiagnosticResult(
        name="Version metadata",
        status="INFO",
        message=f"Icebrew version: {__version__}",
    )


def run_diagnostics() -> list[DiagnosticResult]:
    """Run all currently implemented diagnostic checks."""

    checks = [
        check_python_version,
        check_python_executable,
        check_icebrew_import,
        check_core_dependencies,
        check_version_consistency,
    ]

    results = []

    for check in checks:
        try:
            results.append(check())

        except Exception as exc:
            results.append(
                DiagnosticResult(
                    name=check.__name__,
                    status="FAIL",
                    message=f"Check failed unexpectedly: {exc}",
                )
            )

    return results
