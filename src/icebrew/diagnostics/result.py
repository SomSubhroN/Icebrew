"""Structured diagnostic results."""

from dataclasses import dataclass


@dataclass
class DiagnosticResult:
    """Represents the result of a diagnostic check."""

    name: str
    status: str
    message: str

    def __post_init__(self) -> None:
        allowed_statuses = {"PASS", "WARN", "FAIL", "SKIP", "INFO"}

        if self.status not in allowed_statuses:
            raise ValueError(f"Invalid diagnostic status: {self.status}")
