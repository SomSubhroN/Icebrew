
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats

from icebrew.stats.utils import validate_numeric_series


def _prepare_groups(groups, names=None):
    if isinstance(groups, dict):
        group_names = list(groups.keys())
        values = list(groups.values())
    else:
        values = list(groups)
        group_names = (
            list(names)
            if names is not None
            else [f"group_{i + 1}" for i in range(len(values))]
        )

    if len(values) < 2:
        raise ValueError("At least two groups are required.")

    if len(group_names) != len(values):
        raise ValueError("Group names must match the number of groups.")

    if len(set(group_names)) != len(group_names):
        raise ValueError("Group names must be unique.")

    prepared = {}

    for name, data in zip(group_names, values):
        series = validate_numeric_series(data, name=str(name))
        prepared[str(name)] = series.to_numpy(dtype=float)

    return prepared


def one_way_anova(groups, *, names=None):
    """Perform classical one-way ANOVA."""

    prepared = _prepare_groups(groups, names)
    values = list(prepared.values())

    result = stats.f_oneway(*values)

    total_n = sum(len(group) for group in values)
    k = len(values)

    grand_mean = np.concatenate(values).mean()

    ss_between = sum(
        len(group) * (group.mean() - grand_mean) ** 2
        for group in values
    )

    ss_within = sum(
        ((group - group.mean()) ** 2).sum()
        for group in values
    )

    ss_total = ss_between + ss_within

    df_between = k - 1
    df_within = total_n - k

    eta_squared = (
        ss_between / ss_total
        if ss_total > 0
        else None
    )

    omega_squared = (
        max(
            0.0,
            (ss_between - df_between * (ss_within / df_within))
            / (ss_total + ss_within / df_within),
        )
        if df_within > 0 and ss_total > 0
        else None
    )

    return {
        "test": "one_way_anova",
        "statistic": float(result.statistic),
        "p_value": float(result.pvalue),
        "df_between": df_between,
        "df_within": df_within,
        "groups": k,
        "total_n": total_n,
        "group_summary": {
            name: {
                "n": int(len(group)),
                "mean": float(group.mean()),
                "std": float(group.std(ddof=1)) if len(group) > 1 else None,
            }
            for name, group in prepared.items()
        },
        "effect_size": {
            "eta_squared": float(eta_squared) if eta_squared is not None else None,
            "omega_squared": float(omega_squared) if omega_squared is not None else None,
        },
        "significant": bool(result.pvalue < 0.05),
        "alpha": 0.05,
        "assumptions": [
            "Independent observations.",
            "Approximately normal residuals within groups.",
            "Homogeneity of variance across groups.",
        ],
        "warnings": [],
    }


def welch_anova(groups, *, names=None):
    """Perform Welch's one-way ANOVA."""

    prepared = _prepare_groups(groups, names)

    k = len(prepared)

    if any(len(group) < 2 for group in prepared.values()):
        raise ValueError(
            "Welch ANOVA requires at least two observations per group."
        )

    ns = np.array([len(group) for group in prepared.values()], dtype=float)
    means = np.array([group.mean() for group in prepared.values()])
    variances = np.array([group.var(ddof=1) for group in prepared.values()])

    if np.any(variances == 0):
        raise ValueError(
            "Welch ANOVA requires non-zero variance in every group."
        )

    weights = ns / variances
    weighted_mean = np.sum(weights * means) / np.sum(weights)

    numerator = np.sum(weights * (means - weighted_mean) ** 2) / (k - 1)

    correction_terms = (
        (1 - weights / np.sum(weights)) ** 2
        / (ns - 1)
    )

    correction = 1 + (
        2 * (k - 2) / (k**2 - 1)
    ) * np.sum(correction_terms)

    statistic = numerator / correction

    df1 = k - 1

    df2 = (
        (k**2 - 1)
        / (3 * np.sum(correction_terms))
    )

    p_value = stats.f.sf(statistic, df1, df2)

    return {
        "test": "welch_anova",
        "statistic": float(statistic),
        "p_value": float(p_value),
        "df_between": float(df1),
        "df_within": float(df2),
        "groups": k,
        "total_n": int(ns.sum()),
        "group_summary": {
            name: {
                "n": int(len(group)),
                "mean": float(group.mean()),
                "std": float(group.std(ddof=1)),
            }
            for name, group in prepared.items()
        },
        "significant": bool(p_value < 0.05),
        "alpha": 0.05,
        "assumptions": [
            "Independent observations.",
            "Approximately normal distributions within groups.",
            "Equal variances are not assumed.",
        ],
        "warnings": [],
    }



def tukey_hsd(groups, *, names=None, alpha=0.05):
    """Perform Tukey's Honestly Significant Difference pairwise comparisons.

    Parameters
    ----------
    groups : dict or sequence
        Mapping of group names to numeric observations, or a sequence
        of numeric groups.
    names : sequence, optional
        Names for groups when groups is a sequence.
    alpha : float, default=0.05
        Significance level.

    Returns
    -------
    dict
        Structured pairwise comparison results including mean differences,
        adjusted p-values, confidence intervals, and significance decisions.
    """

    prepared = _prepare_groups(groups, names)

    if not 0 < alpha < 1:
        raise ValueError("alpha must be between 0 and 1.")

    if len(prepared) < 2:
        raise ValueError("At least two groups are required.")

    if any(len(group) < 2 for group in prepared.values()):
        raise ValueError(
            "Tukey HSD requires at least two observations per group."
        )

    group_names = list(prepared.keys())
    group_values = list(prepared.values())

    result = stats.tukey_hsd(
        *group_values,
        equal_var=True,
    )

    ci = result.confidence_interval(
        confidence_level=1 - alpha
    )

    comparisons = []

    for i in range(len(group_names)):
        for j in range(i + 1, len(group_names)):
            difference = float(
                group_values[i].mean() - group_values[j].mean()
            )

            p_value = float(result.pvalue[i, j])

            comparisons.append({
                "group1": group_names[i],
                "group2": group_names[j],
                "mean_difference": difference,
                "p_value": p_value,
                "confidence_interval": [
                    float(ci.low[i, j]),
                    float(ci.high[i, j]),
                ],
                "significant": bool(p_value < alpha),
            })

    return {
        "test": "tukey_hsd",
        "alpha": float(alpha),
        "groups": len(group_names),
        "total_n": int(sum(len(group) for group in group_values)),
        "comparisons": comparisons,
        "warnings": [
            "Tukey HSD assumes independent observations and equal population variances.",
            "The confidence intervals and p-values account for multiple pairwise comparisons.",
        ],
    }


def games_howell(groups, *, names=None, alpha=0.05):
    """Perform Games-Howell pairwise comparisons."""

    prepared = _prepare_groups(groups, names)

    if not 0 < alpha < 1:
        raise ValueError("alpha must be between 0 and 1.")

    if any(len(group) < 2 for group in prepared.values()):
        raise ValueError(
            "Games-Howell requires at least two observations per group."
        )

    group_names = list(prepared.keys())
    k = len(prepared)
    comparisons = []

    for i in range(k):
        for j in range(i + 1, k):
            a = prepared[group_names[i]]
            b = prepared[group_names[j]]

            n1, n2 = len(a), len(b)
            mean1, mean2 = a.mean(), b.mean()
            var1, var2 = a.var(ddof=1), b.var(ddof=1)

            if var1 == 0 and var2 == 0:
                raise ValueError(
                    "Games-Howell cannot compare groups with zero variance."
                )

            variance_component = var1 / n1 + var2 / n2

            if variance_component == 0:
                raise ValueError(
                    "Games-Howell encountered zero variance."
                )

            se = np.sqrt(variance_component)

            difference = mean1 - mean2

            t_stat = difference / se

            df = (
                variance_component**2
                / (
                    (var1 / n1) ** 2 / (n1 - 1)
                    + (var2 / n2) ** 2 / (n2 - 1)
                )
            )

            q_stat = np.sqrt(2) * abs(t_stat)

            p_value = stats.studentized_range.sf(
                q_stat,
                k,
                df,
            )

            critical_q = stats.studentized_range.ppf(
                1 - alpha,
                k,
                df,
            )

            margin = critical_q * se / np.sqrt(2)

            comparisons.append({
                "group1": group_names[i],
                "group2": group_names[j],
                "mean_difference": float(difference),
                "standard_error": float(se),
                "df": float(df),
                "statistic": float(t_stat),
                "p_value": float(p_value),
                "confidence_interval": [
                    float(difference - margin),
                    float(difference + margin),
                ],
                "significant": bool(p_value < alpha),
            })

    return {
        "test": "games_howell",
        "alpha": alpha,
        "comparisons": comparisons,
        "warnings": [
            "Games-Howell accommodates unequal variances and unequal group sizes.",
            "Observations are assumed to be independent.",
        ],
    }
