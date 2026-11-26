
from __future__ import annotations

import math
from collections.abc import Mapping, Sequence

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


def _numeric_group(data, *, name="group") -> np.ndarray:
    if isinstance(data, pd.DataFrame):
        raise TypeError(f"{name} must not be a DataFrame.")

    series = pd.Series(data)

    # Empty input is a missing-data condition, not a dtype error.
    if series.empty:
        raise ValueError(f"{name} must not be empty.")

    if not pd.api.types.is_numeric_dtype(series):
        raise TypeError(f"{name} must contain numeric data.")

    series = series.astype(float).replace([np.inf, -np.inf], np.nan)
    series = series.dropna()

    if len(series) == 0:
        raise ValueError(f"{name} has no valid observations.")

    return series.to_numpy(dtype=float)


def _validate_group_size(group, *, minimum=2, name="group"):
    if len(group) < minimum:
        raise ValueError(
            f"{name} must contain at least {minimum} valid observations."
        )


def mann_whitney_u_test(
    group1,
    group2,
    *,
    alternative: str = "two-sided",
    confidence: float = 0.95,
    method: str = "auto",
) -> dict:
    """
    Perform a Mann-Whitney U test for two independent samples.

    The directional interpretation is based on group1 relative to group2.

    Parameters
    ----------
    group1, group2:
        Numeric independent samples.
    alternative:
        'two-sided', 'greater', or 'less'.
        'greater' tests whether group1 tends to have larger values
        than group2.
    confidence:
        Confidence level included in the result metadata.
    method:
        'auto', 'exact', or 'asymptotic'.

    Returns
    -------
    dict
        Structured test result, rank-biserial effect size,
        assumptions, and warnings.
    """
    alternative = _validate_alternative(alternative)
    confidence = validate_confidence_level(confidence)

    valid_methods = {"auto", "exact", "asymptotic"}

    if method not in valid_methods:
        raise ValueError(
            "method must be 'auto', 'exact', or 'asymptotic'."
        )

    x = _numeric_group(group1, name="group1")
    y = _numeric_group(group2, name="group2")

    _validate_group_size(x, name="group1")
    _validate_group_size(y, name="group2")

    result = stats.mannwhitneyu(
        x,
        y,
        alternative=alternative,
        method=method,
    )

    n1, n2 = len(x), len(y)
    u1 = float(result.statistic)
    p_value = float(result.pvalue)

    # U1 counts the relative rank dominance of group1 over group2,
    # with ties contributing half.
    rank_biserial = (2 * u1 / (n1 * n2)) - 1

    warnings_list = [
        "Mann-Whitney U compares the distributions of two independent "
        "samples. Interpretation as a median comparison requires "
        "additional assumptions, such as comparable distribution shapes.",
        "Independent observations are required.",
    ]

    if method == "exact":
        warnings_list.append(
            "The exact method does not account for ties in the "
            "distribution of the test statistic."
        )

    return {
        "test": "Mann-Whitney U test",
        "statistic": u1,
        "p_value": p_value,
        "n1": int(n1),
        "n2": int(n2),
        "alternative": alternative,
        "method": method,
        "confidence": confidence,
        "rank_biserial": float(rank_biserial),
        "significant": bool(p_value < 1 - confidence),
        "alpha": float(1 - confidence),
        "median1": float(np.median(x)),
        "median2": float(np.median(y)),
        "mean1": float(np.mean(x)),
        "mean2": float(np.mean(y)),
        "warnings": warnings_list,
    }


def kruskal_wallis_test(
    groups,
    *,
    names=None,
    confidence: float = 0.95,
) -> dict:
    """
    Perform a Kruskal-Wallis H test on independent groups.

    Parameters
    ----------
    groups:
        Sequence of numeric groups, or a mapping of group names
        to numeric samples.
    names:
        Optional names for groups supplied as a sequence.
        Not used when groups is a mapping.
    confidence:
        Confidence level included in result metadata.

    Returns
    -------
    dict
        Structured test result, epsilon-squared effect size,
        group summaries, assumptions, and warnings.
    """
    confidence = validate_confidence_level(confidence)

    if isinstance(groups, Mapping):
        if names is not None:
            raise ValueError(
                "Do not supply names when groups is a mapping."
            )

        group_names = list(groups.keys())
        raw_groups = list(groups.values())
    else:
        if isinstance(groups, (str, bytes)) or not isinstance(
            groups, Sequence
        ):
            raise TypeError(
                "groups must be a mapping or a sequence of numeric groups."
            )

        raw_groups = list(groups)

        if names is None:
            group_names = [
                f"group_{i + 1}" for i in range(len(raw_groups))
            ]
        else:
            group_names = list(names)

            if len(group_names) != len(raw_groups):
                raise ValueError(
                    "names must have the same length as groups."
                )

    if len(raw_groups) < 2:
        raise ValueError(
            "Kruskal-Wallis requires at least two independent groups."
        )

    if len(set(group_names)) != len(group_names):
        raise ValueError("Group names must be unique.")

    numeric_groups = [
        _numeric_group(group, name=str(group_name))
        for group, group_name in zip(raw_groups, group_names)
    ]

    for group, group_name in zip(numeric_groups, group_names):
        _validate_group_size(group, minimum=1, name=str(group_name))

    result = stats.kruskal(*numeric_groups)

    h_statistic = float(result.statistic)
    p_value = float(result.pvalue)

    k = len(numeric_groups)
    total_n = sum(len(group) for group in numeric_groups)

    denominator = total_n - k

    if denominator <= 0:
        epsilon_squared = None
    else:
        epsilon_squared = max(
            0.0,
            (h_statistic - k + 1) / denominator,
        )

    summaries = {
        str(name): {
            "n": int(len(group)),
            "mean": float(np.mean(group)),
            "median": float(np.median(group)),
            "std": (
                float(np.std(group, ddof=1))
                if len(group) > 1
                else None
            ),
        }
        for name, group in zip(group_names, numeric_groups)
    }

    warnings_list = [
        "Kruskal-Wallis tests differences in rank distributions "
        "across independent groups. Interpretation as a median "
        "comparison requires additional assumptions about distribution "
        "shapes.",
        "Independent observations are required.",
        "A significant omnibus result does not identify which groups "
        "differ. Post-hoc comparisons are needed.",
    ]

    return {
        "test": "Kruskal-Wallis H test",
        "statistic": h_statistic,
        "p_value": p_value,
        "degrees_of_freedom": int(k - 1),
        "k": int(k),
        "total_n": int(total_n),
        "group_names": list(map(str, group_names)),
        "group_summaries": summaries,
        "epsilon_squared": (
            float(epsilon_squared)
            if epsilon_squared is not None
            else None
        ),
        "confidence": confidence,
        "significant": bool(p_value < 1 - confidence),
        "alpha": float(1 - confidence),
        "warnings": warnings_list,
    }
