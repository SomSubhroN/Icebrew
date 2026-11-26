
import numpy as np
import pytest

from icebrew.stats.independent import independent_t_test


def test_welch_default():
    result = independent_t_test(
        [12, 14, 15, 16, 18],
        [8, 9, 10, 11, 12],
    )

    assert result["equal_var"] is False
    assert "Welch" in result["test"]
    assert result["n1"] == 5
    assert result["n2"] == 5
    assert result["difference"] == pytest.approx(5.0)
    assert result["statistic"] > 0
    assert result["p_value"] < 0.05


def test_student_t_test():
    result = independent_t_test(
        [12, 14, 15, 16, 18],
        [8, 9, 10, 11, 12],
        equal_var=True,
    )

    assert result["equal_var"] is True
    assert "Student" in result["test"]
    assert result["degrees_of_freedom"] == 8


def test_greater_alternative():
    result = independent_t_test(
        [10, 12, 14, 15],
        [2, 3, 4, 5],
        alternative="greater",
    )

    assert result["p_value"] < 0.05
    assert result["confidence_interval"][1] == float("inf")


def test_less_alternative():
    result = independent_t_test(
        [2, 3, 4, 5],
        [10, 12, 14, 15],
        alternative="less",
    )

    assert result["p_value"] < 0.05
    assert result["confidence_interval"][0] == float("-inf")


def test_two_sided_confidence_interval():
    result = independent_t_test(
        [12, 14, 15, 16, 18],
        [8, 9, 10, 11, 12],
    )

    low, high = result["confidence_interval"]

    assert low < result["difference"] < high
    assert np.isfinite(low)
    assert np.isfinite(high)


def test_effect_sizes():
    result = independent_t_test(
        [10, 12, 14, 15],
        [2, 3, 4, 5],
    )

    assert result["cohens_d"] is not None
    assert result["hedges_g"] is not None
    assert result["cohens_d"] > 0
    assert result["hedges_g"] > 0


def test_missing_values_are_dropped():
    result = independent_t_test(
        [10, 12, np.nan, 14],
        [2, 3, 4, np.nan],
    )

    assert result["n1"] == 3
    assert result["n2"] == 3


def test_zero_variance_groups_with_different_means():
    result = independent_t_test(
        [5, 5, 5],
        [2, 2, 2],
    )

    assert result["statistic"] == float("inf")
    assert result["p_value"] == 0.0
    assert result["cohens_d"] is None
    assert result["hedges_g"] is None


def test_zero_variance_groups_with_equal_means():
    result = independent_t_test(
        [5, 5, 5],
        [5, 5, 5],
    )

    assert result["statistic"] == 0.0
    assert result["p_value"] == 1.0


def test_invalid_alternative():
    with pytest.raises(ValueError):
        independent_t_test(
            [1, 2, 3],
            [4, 5, 6],
            alternative="invalid",
        )


def test_insufficient_group_size():
    with pytest.raises(ValueError):
        independent_t_test([1], [2, 3])


def test_empty_group():
    with pytest.raises(ValueError):
        independent_t_test([], [2, 3, 4])


def test_invalid_confidence():
    with pytest.raises(ValueError):
        independent_t_test(
            [1, 2, 3],
            [4, 5, 6],
            confidence=1.0,
        )


def test_unequal_sample_sizes():
    result = independent_t_test(
        [10, 11, 12, 13],
        [1, 2, 3],
    )

    assert result["n1"] == 4
    assert result["n2"] == 3
    assert result["degrees_of_freedom"] > 0


def test_directional_p_values():
    group1 = [10, 11, 12, 13]
    group2 = [1, 2, 3, 4]

    two_sided = independent_t_test(group1, group2)
    greater = independent_t_test(
        group1, group2, alternative="greater"
    )
    less = independent_t_test(
        group1, group2, alternative="less"
    )

    assert greater["p_value"] < two_sided["p_value"]
    assert less["p_value"] > 0.5
