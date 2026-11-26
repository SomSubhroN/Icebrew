
import numpy as np
import pytest

from icebrew.stats.nonparametric import (
    mann_whitney_u_test,
    kruskal_wallis_test,
)


# ===========================
# Mann-Whitney U
# ===========================

def test_mann_whitney_basic():
    result = mann_whitney_u_test(
        [10, 12, 14, 16, 18, 20],
        [2, 3, 4, 5, 6, 7],
    )

    assert result["test"] == "Mann-Whitney U test"
    assert result["n1"] == 6
    assert result["n2"] == 6
    assert result["p_value"] < 0.05
    assert result["rank_biserial"] > 0


def test_mann_whitney_greater():
    result = mann_whitney_u_test(
        [10, 12, 14, 16, 18, 20],
        [2, 3, 4, 5, 6, 7],
        alternative="greater",
    )

    assert result["p_value"] < 0.05
    assert result["rank_biserial"] > 0


def test_mann_whitney_less():
    result = mann_whitney_u_test(
        [2, 3, 4, 5, 6, 7],
        [10, 12, 14, 16, 18, 20],
        alternative="less",
    )

    assert result["p_value"] < 0.05
    assert result["rank_biserial"] < 0


def test_mann_whitney_two_sided():
    result = mann_whitney_u_test(
        [10, 12, 14, 16, 18, 20],
        [2, 3, 4, 5, 6, 7],
        alternative="two-sided",
    )

    assert 0 <= result["p_value"] <= 1


def test_mann_whitney_ties():
    result = mann_whitney_u_test(
        [1, 2, 2, 3],
        [2, 3, 3, 4],
    )

    assert 0 <= result["p_value"] <= 1
    assert -1 <= result["rank_biserial"] <= 1


def test_mann_whitney_exact_method():
    result = mann_whitney_u_test(
        [1, 3, 5],
        [2, 4, 6],
        method="exact",
    )

    assert 0 <= result["p_value"] <= 1
    assert result["method"] == "exact"


def test_mann_whitney_asymptotic_method():
    result = mann_whitney_u_test(
        [1, 3, 5, 7],
        [2, 4, 6, 8],
        method="asymptotic",
    )

    assert 0 <= result["p_value"] <= 1


def test_mann_whitney_missing_values():
    result = mann_whitney_u_test(
        [1, 2, np.nan, 4],
        [5, 6, 7, np.nan],
    )

    assert result["n1"] == 3
    assert result["n2"] == 3


def test_mann_whitney_invalid_alternative():
    with pytest.raises(ValueError):
        mann_whitney_u_test(
            [1, 2, 3],
            [4, 5, 6],
            alternative="invalid",
        )


def test_mann_whitney_invalid_method():
    with pytest.raises(ValueError):
        mann_whitney_u_test(
            [1, 2, 3],
            [4, 5, 6],
            method="invalid",
        )


def test_mann_whitney_insufficient_group():
    with pytest.raises(ValueError):
        mann_whitney_u_test([1], [2, 3])


def test_mann_whitney_empty_group():
    with pytest.raises(ValueError):
        mann_whitney_u_test([], [2, 3, 4])


def test_mann_whitney_invalid_confidence():
    with pytest.raises(ValueError):
        mann_whitney_u_test(
            [1, 2, 3],
            [4, 5, 6],
            confidence=1.0,
        )


# ===========================
# Kruskal-Wallis
# ===========================

def test_kruskal_wallis_basic():
    result = kruskal_wallis_test(
        [
            [1, 2, 3, 4],
            [5, 6, 7, 8],
            [9, 10, 11, 12],
        ]
    )

    assert result["test"] == "Kruskal-Wallis H test"
    assert result["k"] == 3
    assert result["total_n"] == 12
    assert result["p_value"] < 0.05
    assert result["epsilon_squared"] >= 0


def test_kruskal_wallis_named_groups():
    result = kruskal_wallis_test(
        {
            "control": [1, 2, 3, 4],
            "treatment_a": [5, 6, 7, 8],
            "treatment_b": [9, 10, 11, 12],
        }
    )

    assert result["group_names"] == [
        "control",
        "treatment_a",
        "treatment_b",
    ]
    assert "control" in result["group_summaries"]


def test_kruskal_wallis_custom_names():
    result = kruskal_wallis_test(
        [
            [1, 2, 3],
            [4, 5, 6],
        ],
        names=["A", "B"],
    )

    assert result["group_names"] == ["A", "B"]


def test_kruskal_wallis_ties():
    result = kruskal_wallis_test(
        [
            [1, 1, 2, 2],
            [2, 3, 3, 3],
            [4, 4, 5, 5],
        ]
    )

    assert 0 <= result["p_value"] <= 1
    assert result["epsilon_squared"] >= 0


def test_kruskal_wallis_missing_values():
    result = kruskal_wallis_test(
        [
            [1, 2, np.nan, 4],
            [5, 6, 7, np.nan],
            [8, 9, 10, 11],
        ]
    )

    assert result["total_n"] == 10


def test_kruskal_wallis_group_summaries():
    result = kruskal_wallis_test(
        [
            [1, 2, 3],
            [4, 5, 6],
        ],
        names=["first", "second"],
    )

    assert result["group_summaries"]["first"]["n"] == 3
    assert result["group_summaries"]["second"]["median"] == 5


def test_kruskal_wallis_single_group():
    with pytest.raises(ValueError):
        kruskal_wallis_test([[1, 2, 3]])


def test_kruskal_wallis_empty_group():
    with pytest.raises(ValueError):
        kruskal_wallis_test(
            [
                [],
                [1, 2, 3],
            ]
        )


def test_kruskal_wallis_mismatched_names():
    with pytest.raises(ValueError):
        kruskal_wallis_test(
            [
                [1, 2, 3],
                [4, 5, 6],
            ],
            names=["only_one"],
        )


def test_kruskal_wallis_duplicate_names():
    with pytest.raises(ValueError):
        kruskal_wallis_test(
            [
                [1, 2, 3],
                [4, 5, 6],
            ],
            names=["group", "group"],
        )


def test_kruskal_wallis_mapping_with_names():
    with pytest.raises(ValueError):
        kruskal_wallis_test(
            {
                "a": [1, 2, 3],
                "b": [4, 5, 6],
            },
            names=["a", "b"],
        )


def test_kruskal_wallis_invalid_confidence():
    with pytest.raises(ValueError):
        kruskal_wallis_test(
            [
                [1, 2, 3],
                [4, 5, 6],
            ],
            confidence=1.0,
        )


def test_kruskal_wallis_epsilon_squared():
    result = kruskal_wallis_test(
        [
            [1, 2, 3, 4],
            [5, 6, 7, 8],
            [9, 10, 11, 12],
        ]
    )

    assert result["epsilon_squared"] is not None
    assert 0 <= result["epsilon_squared"] <= 1
