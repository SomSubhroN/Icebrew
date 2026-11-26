
from __future__ import annotations

import numpy as np

from icebrew.stats.utils import validate_numeric_series


def cohens_d(
    group1,
    group2,
    *,
    equal_var=True,
):
    """Calculate Cohen's d for two independent groups."""
    a = validate_numeric_series(group1, name="group1").to_numpy(dtype=float)
    b = validate_numeric_series(group2, name="group2").to_numpy(dtype=float)

    if len(a) < 2 or len(b) < 2:
        raise ValueError("Both groups must contain at least two observations.")

    mean_a = float(np.mean(a))
    mean_b = float(np.mean(b))

    var_a = float(np.var(a, ddof=1))
    var_b = float(np.var(b, ddof=1))

    if equal_var:
        pooled_var = (
            ((len(a) - 1) * var_a + (len(b) - 1) * var_b)
            / (len(a) + len(b) - 2)
        )

        pooled_std = float(np.sqrt(pooled_var))

        if pooled_std == 0:
            raise ValueError("Pooled standard deviation is zero.")

        denominator = pooled_std
        method = "pooled_standard_deviation"
    else:
        denominator = float(np.sqrt((var_a + var_b) / 2))

        if denominator == 0:
            raise ValueError("Average standard deviation is zero.")

        method = "average_standard_deviation"

    d = (mean_a - mean_b) / denominator

    return {
        "cohens_d": float(d),
        "mean_group1": mean_a,
        "mean_group2": mean_b,
        "n_group1": int(len(a)),
        "n_group2": int(len(b)),
        "standardizer": method,
    }


def hedges_g(
    group1,
    group2,
):
    """Calculate Hedges' g with a small-sample correction."""
    result = cohens_d(group1, group2, equal_var=True)

    n1 = result["n_group1"]
    n2 = result["n_group2"]

    degrees_of_freedom = n1 + n2 - 2

    correction = 1 - (3 / (4 * degrees_of_freedom - 1))

    return {
        **result,
        "hedges_g": float(result["cohens_d"] * correction),
        "correction_factor": float(correction),
    }
