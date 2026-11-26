
import numpy as np
import pytest

from icebrew.stats.paired import (
    paired_t_test,
    wilcoxon_signed_rank_test,
)


# ---------------------------
# Paired t-test
# ---------------------------

def test_paired_t_test_basic():
    result = paired_t_test(
        [10, 12, 14, 16, 18],
        [8, 10, 11, 12, 14],
    )

    assert result["test"] == "Paired t-test"
    assert result["n_pairs"] == 5
    assert result["mean_difference"] == pytest.approx(3.0)
    assert result["p_value"] < 0.05


def test_paired_t_test_direction_greater():
    result = paired_t_test(
        [10, 12, 14, 16],
        [2, 3, 4, 5],
        alternative="greater",
    )

    assert result["p_value"] < 0.05
    assert result["confidence_interval"][1] == float("inf")


def test_paired_t_test_direction_less():
    result = paired_t_test(
        [2, 3, 4, 5],
        [10, 12, 14, 16],
        alternative="less",
    )

    assert result["p_value"] < 0.05
    assert result["confidence_interval"][0] == float("-inf")


def test_paired_t_test_confidence_interval():
    result = paired_t_test(
        [10, 12, 14, 16, 18],
        [8, 10, 11, 12, 14],
    )

    low, high = result["confidence_interval"]

    assert low < result["mean_difference"] < high
    assert np.isfinite(low)
    assert np.isfinite(high)


def test_paired_t_test_effect_sizes():
    result = paired_t_test(
        [10, 12, 14, 16],
        [2, 3, 4, 5],
    )

    assert result["cohens_dz"] is not None
    assert result["hedges_gz"] is not None
    assert result["cohens_dz"] > 0
    assert result["hedges_gz"] > 0


def test_paired_t_test_missing_pairs():
    result = paired_t_test(
        [10, 12, np.nan, 14, 16],
        [8, 10, 11, np.nan, 14],
    )

    assert result["n_pairs"] == 3


def test_paired_t_test_zero_variance_differences():
    result = paired_t_test(
        [5, 6, 7],
        [2, 3, 4],
    )

    assert result["statistic"] == float("inf")
    assert result["p_value"] == 0.0
    assert result["cohens_dz"] is None
    assert result["hedges_gz"] is None


def test_paired_t_test_zero_difference():
    result = paired_t_test(
        [5, 5, 5],
        [5, 5, 5],
    )

    assert result["statistic"] == 0.0
    assert result["p_value"] == 1.0


def test_paired_t_test_invalid_alternative():
    with pytest.raises(ValueError):
        paired_t_test(
            [1, 2, 3],
            [4, 5, 6],
            alternative="invalid",
        )


def test_paired_t_test_mismatched_lengths():
    with pytest.raises(ValueError):
        paired_t_test([1, 2, 3], [4, 5])


def test_paired_t_test_insufficient_pairs():
    with pytest.raises(ValueError):
        paired_t_test([1], [2])


def test_paired_t_test_empty():
    with pytest.raises(ValueError):
        paired_t_test([], [])


def test_paired_t_test_invalid_confidence():
    with pytest.raises(ValueError):
        paired_t_test(
            [1, 2, 3],
            [4, 5, 6],
            confidence=1.0,
        )


# ---------------------------
# Wilcoxon signed-rank test
# ---------------------------

def test_wilcoxon_basic():
    result = wilcoxon_signed_rank_test(
        [10, 12, 14, 16, 18, 20],
        [8, 10, 11, 12, 14, 15],
    )

    assert result["test"] == "Wilcoxon signed-rank test"
    assert result["n_pairs"] == 6
    assert result["p_value"] < 0.05


def test_wilcoxon_greater():
    result = wilcoxon_signed_rank_test(
        [10, 12, 14, 16, 18, 20],
        [2, 3, 4, 5, 6, 7],
        alternative="greater",
    )

    assert result["p_value"] < 0.05


def test_wilcoxon_less():
    result = wilcoxon_signed_rank_test(
        [2, 3, 4, 5, 6, 7],
        [10, 12, 14, 16, 18, 20],
        alternative="less",
    )

    assert result["p_value"] < 0.05

def test_wilcoxon_all_zero_differences():
    result = wilcoxon_signed_rank_test(
        [5, 5, 5],
        [5, 5, 5],
    )

    assert result["statistic"] == 0.0
    assert result["p_value"] == 1.0


def test_wilcoxon_missing_pairs():
    result = wilcoxon_signed_rank_test(
        [10, 12, np.nan, 14],
        [8, 10, 11, 12],
    )

    assert result["n_pairs"] == 3


def test_wilcoxon_mismatched_lengths():
    with pytest.raises(ValueError):
        wilcoxon_signed_rank_test(
            [1, 2, 3],
            [4, 5],
        )


def test_wilcoxon_invalid_alternative():
    with pytest.raises(ValueError):
        wilcoxon_signed_rank_test(
            [1, 2, 3],
            [4, 5, 6],
            alternative="invalid",
        )


def test_wilcoxon_invalid_zero_method():
    with pytest.raises(ValueError):
        wilcoxon_signed_rank_test(
            [1, 2, 3],
            [4, 5, 6],
            zero_method="invalid",
        )


def test_wilcoxon_invalid_confidence():
    with pytest.raises(ValueError):
        wilcoxon_signed_rank_test(
            [1, 2, 3],
            [4, 5, 6],
            confidence=1.0,
        )


def test_wilcoxon_zero_method_pratt():
    result = wilcoxon_signed_rank_test(
        [5, 7, 9, 10],
        [5, 6, 7, 8],
        zero_method="pratt",
    )

    assert result["zero_method"] == "pratt"
    assert 0 <= result["p_value"] <= 1


def test_wilcoxon_zero_method_zsplit():
    result = wilcoxon_signed_rank_test(
        [5, 7, 9, 10],
        [5, 6, 7, 8],
        zero_method="zsplit",
    )

    assert result["zero_method"] == "zsplit"
    assert 0 <= result["p_value"] <= 1
