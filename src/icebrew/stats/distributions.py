
from __future__ import annotations

import numpy as np

from icebrew.stats.utils import validate_numeric_series


def analyze_distribution(
    data,
    *,
    bins=10,
    density=False,
):
    """Compute histogram and distribution summary."""
    series = validate_numeric_series(data)
    values = series.to_numpy(dtype=float)

    if isinstance(bins, bool):
        raise TypeError("bins must not be boolean.")

    if isinstance(bins, int):
        if bins < 1:
            raise ValueError("bins must be at least 1.")
    elif isinstance(bins, (list, tuple, np.ndarray)):
        bins = np.asarray(bins, dtype=float)

        if bins.ndim != 1 or len(bins) < 2:
            raise ValueError("Explicit bins must be a 1D array of at least 2 edges.")

        if not np.all(np.isfinite(bins)):
            raise ValueError("Bin edges must be finite.")

        if np.any(np.diff(bins) <= 0):
            raise ValueError("Bin edges must be strictly increasing.")
    else:
        raise TypeError("bins must be an integer or an array of bin edges.")

    counts, edges = np.histogram(
        values,
        bins=bins,
        density=density,
    )

    return {
        "count": int(len(values)),
        "bins": edges.tolist(),
        "counts": counts.tolist(),
        "density": bool(density),
        "minimum": float(np.min(values)),
        "maximum": float(np.max(values)),
        "mean": float(np.mean(values)),
        "median": float(np.median(values)),
    }
