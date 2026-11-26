
from __future__ import annotations

import numpy as np
from scipy import stats

from icebrew.stats.utils import (
    validate_confidence_level,
    validate_numeric_series,
)


def mean_confidence_interval(
    data,
    *,
    confidence=0.95,
):
    """Calculate a t-based confidence interval for a population mean."""
    confidence = validate_confidence_level(confidence)
    series = validate_numeric_series(data)

    values = series.to_numpy(dtype=float)
    n = len(values)

    if n < 2:
        raise ValueError("At least two observations are required.")

    mean = float(np.mean(values))
    std = float(np.std(values, ddof=1))
    sem = std / np.sqrt(n)

    alpha = 1 - confidence
    critical = stats.t.ppf(1 - alpha / 2, df=n - 1)

    margin = float(critical * sem)

    return {
        "mean": mean,
        "std": std,
        "sem": float(sem),
        "n": n,
        "confidence": confidence,
        "lower": float(mean - margin),
        "upper": float(mean + margin),
        "margin_of_error": margin,
        "method": "student_t",
    }


def proportion_confidence_interval(
    successes,
    trials,
    *,
    confidence=0.95,
):
    """Calculate a Wilson score interval for a binomial proportion."""
    confidence = validate_confidence_level(confidence)

    if isinstance(successes, bool) or not isinstance(successes, int):
        raise TypeError("successes must be an integer.")

    if isinstance(trials, bool) or not isinstance(trials, int):
        raise TypeError("trials must be an integer.")

    if trials < 1:
        raise ValueError("trials must be at least 1.")

    if not 0 <= successes <= trials:
        raise ValueError("successes must be between 0 and trials.")

    p = successes / trials
    z = stats.norm.ppf(1 - (1 - confidence) / 2)
    z2 = z * z

    denominator = 1 + z2 / trials

    center = (p + z2 / (2 * trials)) / denominator

    half_width = (
        z
        * np.sqrt(
            p * (1 - p) / trials
            + z2 / (4 * trials * trials)
        )
        / denominator
    )

    return {
        "proportion": float(p),
        "successes": successes,
        "trials": trials,
        "confidence": confidence,
        "lower": float(max(0.0, center - half_width)),
        "upper": float(min(1.0, center + half_width)),
        "method": "wilson",
    }
