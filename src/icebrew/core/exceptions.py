"""Structured exception hierarchy for Icebrew."""


class IcebrewError(Exception):
    """Base exception for all expected Icebrew errors."""

    code: str = "ICEBREW_ERROR"
    exit_code: int = 1

    def __init__(
        self,
        message: str,
        *,
        code: str | None = None,
    ) -> None:
        self.message = message
        self.code = code or type(self).code
        super().__init__(message)


class ConfigurationError(IcebrewError):
    """Raised when configuration is invalid or unavailable."""

    code = "CONFIG_ERROR"


class InstallationError(IcebrewError):
    """Raised when installation or setup fails."""

    code = "INSTALLATION_ERROR"


class DependencyError(IcebrewError):
    """Raised when a required dependency is missing or incompatible."""

    code = "DEPENDENCY_ERROR"


class DataError(IcebrewError):
    """Raised when data operations fail."""

    code = "DATA_ERROR"


class StatisticsError(IcebrewError):
    """Raised when a statistical operation fails."""

    code = "STATISTICS_ERROR"


class PlottingError(IcebrewError):
    """Raised when plotting operations fail."""

    code = "PLOTTING_ERROR"


class SentimentError(IcebrewError):
    """Raised when sentiment analysis fails."""

    code = "SENTIMENT_ERROR"


class AIError(IcebrewError):
    """Base exception for AI-related failures."""

    code = "AI_ERROR"


class ModelNotFoundError(AIError):
    """Raised when a requested model cannot be found."""

    code = "MODEL_NOT_FOUND"


class ModelDownloadError(AIError):
    """Raised when a model download fails."""

    code = "MODEL_DOWNLOAD_ERROR"


class ModelIntegrityError(AIError):
    """Raised when a model fails an integrity check."""

    code = "MODEL_INTEGRITY_ERROR"


class BackendUnavailableError(AIError):
    """Raised when an AI backend is unavailable."""

    code = "BACKEND_UNAVAILABLE"


class InferenceError(AIError):
    """Raised when model inference fails."""

    code = "INFERENCE_ERROR"


class MediaError(IcebrewError):
    """Raised when media processing fails."""

    code = "MEDIA_ERROR"


class ReportingError(IcebrewError):
    """Raised when report generation fails."""

    code = "REPORTING_ERROR"


class ExperimentError(IcebrewError):
    """Raised when experiment management fails."""

    code = "EXPERIMENT_ERROR"


class ExtensionError(IcebrewError):
    """Raised when extension operations fail."""

    code = "EXTENSION_ERROR"


class SecurityError(IcebrewError):
    """Raised when a security-related operation fails."""

    code = "SECURITY_ERROR"