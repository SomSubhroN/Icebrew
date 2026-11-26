
from __future__ import annotations

import math

import numpy as np
from scipy import stats

from icebrew.stats.utils import (
    validate_confidence_level,
    validate_numeric_series,
)


_SUPPORTED_ALTERNATIVES = {"two-sided", "greater", "less"}


def _validate_alternative(alternative: str) -> str:
    if alternative not in _SUPPORTED_ALTERNATIVES:
        raise ValueError(
            "alternative must be 'two-sided', 'greater', or 'less'."
        )
    return alternative


def _calculate_interval(
    difference: float,
    standard_error: float,
    degrees_of_freedom: float,
    confidence: float,
    alternative: str,
) -> tuple[float, float]:
    alpha = 1.0 - confidence

    if standard_error == 0:
        return difference, difference

    if alternative == "two-sided":
        critical = stats.t.ppf(1 - alpha / 2, degrees_of_freedom)
        margin = critical * standard_error
        return difference - margin, difference + margin

    critical = stats.t.ppf(confidence, degrees_of_freedom)

    if alternative == "greater":
        return difference - critical * standard_error, math.inf

    return -math.inf, difference + critical * standard_error


def independent_t_test(
    group1,
    group2,
    *,
    equal_var: bool = False,
    alternative: str = "two-sided",
    confidence: float = 0.95,
) -> dict:
    """
    Perform an independent two-sample t-test.

    Welch's t-test is used by default. Set equal_var=True to use
    Student's pooled-variance t-test.

    Parameters
    ----------
    group1, group2:
        Numeric array-like data or pandas Series.
    equal_var:
        If True, assumes equal population variances and uses Student's
        pooled-variance t-test. Otherwise, uses Welch's t-test.
    alternative:
        'two-sided', 'greater', or 'less'.
        'greater' tests whether group1 mean exceeds group2 mean.
    confidence:
        Confidence level between 0 and 1.

    Returns
    -------
    dict
        Structured statistical results, confidence interval,
        effect sizes, assumptions, and warnings.
    """
    alternative = _validate_alternative(alternative)
    confidence = validate_confidence_level(confidence)

    g1 = validate_numeric_series(group1, name="group1")
    g2 = validate_numeric_series(group2, name="group2")

    if len(g1) < 2 or len(g2) < 2:
        raise ValueError(
            "Each independent group must contain at least two "
            "valid observations."
        )

    x = g1.to_numpy(dtype=float)
    y = g2.to_numpy(dtype=float)

    n1, n2 = len(x), len(y)
    mean1, mean2 = float(np.mean(x)), float(np.mean(y))
    var1, var2 = float(np.var(x, ddof=1)), float(np.var(y, ddof=1))
    std1, std2 = math.sqrt(var1), math.sqrt(var2)

    difference = mean1 - mean2

    warnings_list: list[str] = []

    if equal_var:
        df = float(n1 + n2 - 2)

        pooled_variance = (
            ((n1 - 1) * var1 + (n2 - 1) * var2) / df
        )
        pooled_std = math.sqrt(pooled_variance)

        standard_error = pooled_std * math.sqrt(1 / n1 + 1 / n2)

        if standard_error == 0:
            if difference == 0:
                statistic = 0.0
                p_value = 1.0
            else:
                statistic = math.copysign(math.inf, difference)

                if alternative == "two-sided":
                    p_value = 0.0
                elif alternative == "greater":
                    p_value = 0.0 if difference > 0 else 1.0
                else:
                    p_value = 0.0 if difference < 0 else 1.0
        else:
            statistic = difference / standard_error

            p_value = float(
                stats.t.sf(statistic, df)
                if alternative == "greater"
                else stats.t.cdf(statistic, df)
                if alternative == "less"
                else 2 * stats.t.sf(abs(statistic), df)
            )

        method = "Student's independent t-test"
        variance_assumption = "Equal population variances assumed."

    else:
        variance_component1 = var1 / n1
        variance_component2 = var2 / n2

        standard_error = math.sqrt(
            variance_component1 + variance_component2
        )

        denominator = (
            variance_component1**2 / (n1 - 1)
            + variance_component2**2 / (n2 - 1)
        )

        if denominator == 0:
            df = float(n1 + n2 - 2)
        else:
            df = (
                (variance_component1 + variance_component2) ** 2
                / denominator
            )

        if standard_error == 0:
            if difference == 0:
                statistic = 0.0
                p_value = 1.0
            else:
                statistic = math.copysign(math.inf, difference)

                if alternative == "two-sided":
                    p_value = 0.0
                elif alternative == "greater":
                    p_value = 0.0 if difference > 0 else 1.0
                else:
                    p_value = 0.0 if difference < 0 else 1.0
        else:
            statistic = difference / standard_error

            p_value = float(
                stats.t.sf(statistic, df)
                if alternative == "greater"
                else stats.t.cdf(statistic, df)
                if alternative == "less"
                else 2 * stats.t.sf(abs(statistic), df)
            )

        method = "Welch's independent t-test"
        variance_assumption = (
            "Equal population variances are not assumed."
        )

    ci_low, ci_high = _calculate_interval(
        difference,
        standard_error,
        df,
        confidence,
        alternative,
    )

    # Conventional pooled standard deviation for standardized effect sizes.
    pooled_variance_effect = (
        ((n1 - 1) * var1 + (n2 - 1) * var2)
        / (n1 + n2 - 2)
    )
    pooled_std_effect = math.sqrt(pooled_variance_effect)

    if pooled_std_effect == 0:
        cohens_d = None
        hedges_g = None
        warnings_list.append(
            "Cohen's d and Hedges' g are undefined because "
            "the pooled standard deviation is zero."
        )
    else:
        cohens_d = difference / pooled_std_effect

        effect_df = n1 + n2 - 2

        # Small-sample correction for Hedges' g.
        correction = 1 - 3 / (4 * effect_df - 1)

        hedges_g = cohens_d * correction

    if equal_var:
        warnings_list.append(
            "The Student t-test assumes equal population variances."
        )
    else:
        warnings_list.append(
            "Welch's t-test does not require equal population variances."
        )

    warnings_list.append(
        "The test assumes independent observations and sufficiently "
        "appropriate sampling distributions. With small samples, "
        "strong departures from normality may affect validity."
    )

    return {
        "test": method,
        "statistic": float(statistic),
        "p_value": float(p_value),
        "degrees_of_freedom": float(df),
        "n1": int(n1),
        "n2": int(n2),
        "mean1": mean1,
        "mean2": mean2,
        "difference": float(difference),
        "variance1": var1,
        "variance2": var2,
        "std1": std1,
        "std2": std2,
        "standard_error": float(standard_error),
        "alternative": alternative,
        "confidence": confidence,
        "confidence_interval": (float(ci_low), float(ci_high)),
        "cohens_d": (
            float(cohens_d) if cohens_d is not None else None
        ),
        "hedges_g": (
            float(hedges_g) if hedges_g is not None else None
        ),
        "significant": bool(p_value < 1 - confidence),
        "alpha": float(1 - confidence),
        "equal_var": bool(equal_var),
        "variance_assumption": variance_assumption,
        "warnings": warnings_list,
    }
