
from __future__ import annotations

import math

import numpy as np
import pandas as pd
from scipy import stats

from icebrew.stats.utils import validate_confidence_level


_SUPPORTED_ALTERNATIVES = {"two-sided", "greater", "less"}


def _validate_alternative(alternative: str) -> str:
    if alternative not in _SUPPORTED_ALTERNATIVES:
        raise ValueError(
            "alternative must be 'two-sided', 'greater', or 'less'."
        )
    return alternative


def _paired_numeric_data(before, after) -> tuple[np.ndarray, np.ndarray]:
    """Validate and pair numeric observations positionally."""
    if isinstance(before, pd.DataFrame) or isinstance(after, pd.DataFrame):
        raise TypeError("Paired inputs must not be DataFrames.")

    x = pd.Series(before)
    y = pd.Series(after)

    if len(x) != len(y):
        raise ValueError(
            "Paired inputs must have the same original length."
        )

    if len(x) == 0:
        raise ValueError("Paired inputs must not be empty.")

    if not pd.api.types.is_numeric_dtype(x):
        raise TypeError("The first paired input must be numeric.")

    if not pd.api.types.is_numeric_dtype(y):
        raise TypeError("The second paired input must be numeric.")

    x = x.astype(float).replace([np.inf, -np.inf], np.nan)
    y = y.astype(float).replace([np.inf, -np.inf], np.nan)

    # Pairwise deletion: discard a pair if either observation is missing.
    paired = pd.DataFrame({"x": x, "y": y}).dropna()

    if paired.empty:
        raise ValueError("No valid paired observations remain.")

    return (
        paired["x"].to_numpy(dtype=float),
        paired["y"].to_numpy(dtype=float),
    )


def _mean_difference_interval(
    differences: np.ndarray,
    confidence: float,
    alternative: str,
) -> tuple[float, float]:
    n = len(differences)
    mean_difference = float(np.mean(differences))

    if n < 2:
        return (mean_difference, mean_difference)

    standard_deviation = float(np.std(differences, ddof=1))
    standard_error = standard_deviation / math.sqrt(n)

    if standard_error == 0:
        return mean_difference, mean_difference

    alpha = 1 - confidence
    degrees_of_freedom = n - 1

    if alternative == "two-sided":
        critical = stats.t.ppf(1 - alpha / 2, degrees_of_freedom)
        margin = critical * standard_error
        return mean_difference - margin, mean_difference + margin

    critical = stats.t.ppf(confidence, degrees_of_freedom)

    if alternative == "greater":
        return mean_difference - critical * standard_error, math.inf

    return -math.inf, mean_difference + critical * standard_error


def paired_t_test(
    before,
    after,
    *,
    alternative: str = "two-sided",
    confidence: float = 0.95,
) -> dict:
    """
    Perform a paired-samples t-test.

    The test operates on positional pairs and tests whether the mean
    difference (before - after) equals zero.

    Parameters
    ----------
    before, after:
        Equal-length numeric array-like paired observations.
    alternative:
        'two-sided', 'greater', or 'less'.
        'greater' tests whether mean(before - after) > 0.
    confidence:
        Confidence level between 0 and 1.

    Returns
    -------
    dict
        Structured test results, confidence interval, paired effect
        sizes, assumptions, and warnings.
    """
    alternative = _validate_alternative(alternative)
    confidence = validate_confidence_level(confidence)

    x, y = _paired_numeric_data(before, after)

    if len(x) < 2:
        raise ValueError(
            "At least two valid pairs are required for a paired t-test."
        )

    differences = x - y
    n = len(differences)

    mean_difference = float(np.mean(differences))
    sd_difference = float(np.std(differences, ddof=1))
    standard_error = sd_difference / math.sqrt(n)
    df = n - 1

    warnings_list: list[str] = []

    if sd_difference == 0:
        if mean_difference == 0:
            statistic = 0.0
            p_value = 1.0
        else:
            statistic = math.copysign(math.inf, mean_difference)

            if alternative == "two-sided":
                p_value = 0.0
            elif alternative == "greater":
                p_value = 0.0 if mean_difference > 0 else 1.0
            else:
                p_value = 0.0 if mean_difference < 0 else 1.0

        warnings_list.append(
            "The paired differences have zero variance; "
            "the t-statistic is degenerate."
        )
    else:
        statistic = mean_difference / standard_error

        p_value = float(
            stats.t.sf(statistic, df)
            if alternative == "greater"
            else stats.t.cdf(statistic, df)
            if alternative == "less"
            else 2 * stats.t.sf(abs(statistic), df)
        )

    ci_low, ci_high = _mean_difference_interval(
        differences, confidence, alternative
    )

    if sd_difference == 0:
        cohens_dz = None
        hedges_gz = None
        warnings_list.append(
            "Cohen's dz and Hedges' gz are undefined because "
            "the standard deviation of paired differences is zero."
        )
    else:
        cohens_dz = mean_difference / sd_difference

        # Small-sample correction for standardized paired differences.
        correction = 1 - 3 / (4 * df - 1)
        hedges_gz = cohens_dz * correction

    warnings_list.append(
        "The paired t-test assumes that the paired differences are "
        "independent across pairs and approximately normally distributed "
        "for small samples."
    )

    return {
        "test": "Paired t-test",
        "statistic": float(statistic),
        "p_value": float(p_value),
        "degrees_of_freedom": int(df),
        "n_pairs": int(n),
        "mean_before": float(np.mean(x)),
        "mean_after": float(np.mean(y)),
        "mean_difference": mean_difference,
        "std_difference": sd_difference,
        "standard_error": float(standard_error),
        "alternative": alternative,
        "confidence": confidence,
        "confidence_interval": (float(ci_low), float(ci_high)),
        "cohens_dz": (
            float(cohens_dz) if cohens_dz is not None else None
        ),
        "hedges_gz": (
            float(hedges_gz) if hedges_gz is not None else None
        ),
        "significant": bool(p_value < 1 - confidence),
        "alpha": float(1 - confidence),
        "warnings": warnings_list,
    }


def wilcoxon_signed_rank_test(
    before,
    after,
    *,
    alternative: str = "two-sided",
    confidence: float = 0.95,
    zero_method: str = "wilcox",
) -> dict:
    """
    Perform a Wilcoxon signed-rank test on paired observations.

    Parameters
    ----------
    before, after:
        Equal-length numeric array-like paired observations.
    alternative:
        'two-sided', 'greater', or 'less'.
        'greater' tests whether before - after tends to be positive.
    confidence:
        Confidence level included in the structured result.
        Note that this implementation does not calculate a confidence
        interval for the Wilcoxon location parameter.
    zero_method:
        SciPy Wilcoxon zero-difference handling:
        'wilcox', 'pratt', or 'zsplit'.

    Returns
    -------
    dict
        Structured nonparametric test results and assumptions.
    """
    alternative = _validate_alternative(alternative)
    confidence = validate_confidence_level(confidence)

    valid_zero_methods = {"wilcox", "pratt", "zsplit"}

    if zero_method not in valid_zero_methods:
        raise ValueError(
            "zero_method must be 'wilcox', 'pratt', or 'zsplit'."
        )

    x, y = _paired_numeric_data(before, after)

    differences = x - y
    n = len(differences)

    if n < 1:
        raise ValueError("At least one valid pair is required.")

    warnings_list: list[str] = []

    if np.all(differences == 0):
        statistic = 0.0
        p_value = 1.0

        warnings_list.append(
            "All paired differences are zero. The Wilcoxon test "
            "is degenerate and the p-value is set to 1."
        )
    else:
        result = stats.wilcoxon(
            x,
            y,
            alternative=alternative,
            zero_method=zero_method,
            method="auto",
        )

        statistic = float(result.statistic)
        p_value = float(result.pvalue)

    warnings_list.append(
        "The Wilcoxon signed-rank test evaluates paired differences "
        "using ranks. Interpretation as a test of median difference "
        "requires appropriate symmetry assumptions."
    )

    warnings_list.append(
        "A confidence interval for the Wilcoxon location parameter "
        "is not calculated by this implementation."
    )

    return {
        "test": "Wilcoxon signed-rank test",
        "statistic": float(statistic),
        "p_value": float(p_value),
        "n_pairs": int(n),
        "mean_difference": float(np.mean(differences)),
        "median_difference": float(np.median(differences)),
        "alternative": alternative,
        "confidence": confidence,
        "zero_method": zero_method,
        "significant": bool(p_value < 1 - confidence),
        "alpha": float(1 - confidence),
        "warnings": warnings_list,
    }
