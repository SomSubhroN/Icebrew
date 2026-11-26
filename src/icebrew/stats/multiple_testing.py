
from __future__ import annotations

import numpy as np
from scipy.stats import false_discovery_control


_SUPPORTED_METHODS = {
    "bonferroni",
    "holm",
    "bh",
}


def correct_pvalues(p_values, *, method="holm", alpha=0.05):
    """Adjust a collection of p-values for multiple testing."""

    if method not in _SUPPORTED_METHODS:
        raise ValueError(
            f"Unsupported method '{method}'. "
            f"Choose from {sorted(_SUPPORTED_METHODS)}."
        )

    if not 0 < alpha < 1:
        raise ValueError("alpha must be between 0 and 1.")

    values = np.asarray(p_values, dtype=float)

    if values.ndim != 1:
        raise ValueError("p_values must be a one-dimensional sequence.")

    if values.size == 0:
        raise ValueError("At least one p-value is required.")

    if not np.all(np.isfinite(values)):
        raise ValueError("P-values must be finite.")

    if np.any((values < 0) | (values > 1)):
        raise ValueError("P-values must be between 0 and 1.")

    m = len(values)

    if method == "bonferroni":
        adjusted = np.minimum(values * m, 1.0)

    elif method == "holm":
        order = np.argsort(values)
        sorted_values = values[order]

        adjusted_sorted = np.empty(m, dtype=float)

        adjusted_sorted[:] = (
            (m - np.arange(m)) * sorted_values
        )

        adjusted_sorted = np.maximum.accumulate(
            adjusted_sorted
        )

        adjusted_sorted = np.minimum(
            adjusted_sorted,
            1.0,
        )

        adjusted = np.empty(m, dtype=float)
        adjusted[order] = adjusted_sorted

    elif method == "bh":
        adjusted = false_discovery_control(
            values,
            method="bh",
        )

    return {
        "method": method,
        "alpha": alpha,
        "number_of_tests": m,
        "results": [
            {
                "index": int(i),
                "p_value": float(values[i]),
                "adjusted_p_value": float(adjusted[i]),
                "reject_null": bool(adjusted[i] < alpha),
            }
            for i in range(m)
        ],
        "warnings": [],
    }
