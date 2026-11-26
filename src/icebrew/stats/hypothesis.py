
from __future__ import annotations

import numpy as np
from scipy import stats

from icebrew.stats.utils import (
    validate_confidence_level,
    validate_numeric_series,
)


_SUPPORTED_ALTERNATIVES = {"two-sided", "greater", "less"}


def _validate_alternative(alternative: str) -> str:
    """Validate the alternative hypothesis specification."""
    if alternative not in _SUPPORTED_ALTERNATIVES:
        raise ValueError(
            "alternative must be 'two-sided', 'greater', or 'less'."
        )

    return alternative


def _validate_null_value(population_mean: float) -> float:
    """Validate the hypothesized population mean."""
    if isinstance(population_mean, bool) or not isinstance(
        population_mean, (int, float)
    ):
        raise TypeError("population_mean must be numeric.")

    if not np.isfinite(population_mean):
        raise ValueError("population_mean must be finite.")

    return float(population_mean)


def _calculate_interval(
    estimate: float,
    standard_error: float,
    critical_value: float,
    *,
    alternative: str,
) -> tuple[float, float]:
    """Calculate a confidence interval appropriate to the alternative."""
    margin = critical_value * standard_error

    if alternative == "two-sided":
        return estimate - margin, estimate + margin

    if alternative == "greater":
        return estimate - margin, np.inf

    return -np.inf, estimate + margin


def one_sample_t_test(
    data,
    population_mean: float = 0.0,
    *,
    alternative: str = "two-sided",
    confidence: float = 0.95,
):
    """Perform a one-sample Student's t-test.

    Tests whether the population mean differs from a specified
    hypothesized mean using the sample standard deviation.

    Parameters
    ----------
    data : array-like
        Sample observations.
    population_mean : float, default=0.0
        Hypothesized population mean under the null hypothesis.
    alternative : {"two-sided", "greater", "less"}
        Alternative hypothesis direction.
    confidence : float, default=0.95
        Confidence level for the confidence interval.

    Returns
    -------
    dict
        Structured statistical test results.
    """
    alternative = _validate_alternative(alternative)
    population_mean = _validate_null_value(population_mean)
    confidence = validate_confidence_level(confidence)

    series = validate_numeric_series(data)
    values = series.to_numpy(dtype=float)

    n = len(values)

    if n < 2:
        raise ValueError("At least two observations are required.")

    mean = float(np.mean(values))
    std = float(np.std(values, ddof=1))
    standard_error = float(std / np.sqrt(n))
    df = n - 1

    result = stats.ttest_1samp(
        values,
        popmean=population_mean,
        alternative=alternative,
    )

    statistic = float(result.statistic)
    p_value = float(result.pvalue)

    alpha = 1 - confidence

    if alternative == "two-sided":
        critical_value = float(
            stats.t.ppf(1 - alpha / 2, df=df)
        )
    else:
        critical_value = float(
            stats.t.ppf(1 - alpha, df=df)
        )

    lower, upper = _calculate_interval(
        mean,
        standard_error,
        critical_value,
        alternative=alternative,
    )

    cohens_d = None

    if std > 0:
        cohens_d = float((mean - population_mean) / std)

    return {
        "test": "one_sample_t_test",
        "statistic": statistic,
        "p_value": p_value,
        "df": int(df),
        "n": int(n),
        "sample_mean": mean,
        "population_mean": population_mean,
        "mean_difference": float(mean - population_mean),
        "sample_std": std,
        "standard_error": standard_error,
        "alternative": alternative,
        "confidence": confidence,
        "confidence_interval": {
            "lower": float(lower),
            "upper": float(upper),
        },
        "cohens_d": cohens_d,
        "significant": bool(p_value < alpha),
        "alpha": float(alpha),
        "assumptions": [
            "Observations are independent.",
            "The sample is representative of the target population.",
            "The population is approximately normal for small samples.",
        ],
        "warnings": (
            [
                "Sample standard deviation is zero; "
                "Cohen's d is undefined."
            ]
            if std == 0
            else []
        ),
    }


def one_sample_z_test(
    data,
    population_mean: float = 0.0,
    population_std: float | None = None,
    *,
    alternative: str = "two-sided",
    confidence: float = 0.95,
):
    """Perform a one-sample z-test with known population standard deviation.

    The population standard deviation must be supplied. This function
    does not estimate it from the sample.

    Parameters
    ----------
    data : array-like
        Sample observations.
    population_mean : float, default=0.0
        Hypothesized population mean.
    population_std : float
        Known population standard deviation.
    alternative : {"two-sided", "greater", "less"}
        Alternative hypothesis direction.
    confidence : float, default=0.95
        Confidence level for the confidence interval.

    Returns
    -------
    dict
        Structured statistical test results.
    """
    alternative = _validate_alternative(alternative)
    population_mean = _validate_null_value(population_mean)
    confidence = validate_confidence_level(confidence)

    if population_std is None:
        raise ValueError(
            "population_std must be supplied for a z-test."
        )

    if isinstance(population_std, bool) or not isinstance(
        population_std, (int, float)
    ):
        raise TypeError("population_std must be numeric.")

    if not np.isfinite(population_std) or population_std <= 0:
        raise ValueError(
            "population_std must be finite and strictly positive."
        )

    population_std = float(population_std)

    series = validate_numeric_series(data)
    values = series.to_numpy(dtype=float)

    n = len(values)

    if n < 1:
        raise ValueError("At least one observation is required.")

    mean = float(np.mean(values))
    standard_error = population_std / np.sqrt(n)

    z_statistic = (mean - population_mean) / standard_error

    if alternative == "two-sided":
        p_value = 2 * stats.norm.sf(abs(z_statistic))
        critical_value = stats.norm.ppf(1 - (1 - confidence) / 2)
    elif alternative == "greater":
        p_value = stats.norm.sf(z_statistic)
        critical_value = stats.norm.ppf(confidence)
    else:
        p_value = stats.norm.cdf(z_statistic)
        critical_value = stats.norm.ppf(confidence)

    lower, upper = _calculate_interval(
        mean,
        standard_error,
        float(critical_value),
        alternative=alternative,
    )

    alpha = 1 - confidence

    return {
        "test": "one_sample_z_test",
        "statistic": float(z_statistic),
        "p_value": float(p_value),
        "n": int(n),
        "sample_mean": mean,
        "population_mean": population_mean,
        "population_std": population_std,
        "mean_difference": float(mean - population_mean),
        "standard_error": float(standard_error),
        "alternative": alternative,
        "confidence": confidence,
        "confidence_interval": {
            "lower": float(lower),
            "upper": float(upper),
        },
        "significant": bool(p_value < alpha),
        "alpha": float(alpha),
        "assumptions": [
            "Observations are independent.",
            "The population standard deviation is known.",
            "The population is normal or the sample is sufficiently large "
            "for the sampling distribution of the mean to be approximately normal.",
        ],
        "warnings": [],
    }
