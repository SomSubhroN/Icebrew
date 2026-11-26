
import numpy as np
import pytest

from icebrew.stats.hypothesis import (
    one_sample_t_test,
    one_sample_z_test,
)


def test_one_sample_t_test():
    result = one_sample_t_test([2, 3, 4, 5, 6], population_mean=3)

    assert result["test"] == "one_sample_t_test"
    assert result["n"] == 5
    assert result["df"] == 4
    assert result["sample_mean"] == pytest.approx(4)
    assert result["p_value"] < 1
    assert "confidence_interval" in result


def test_one_sample_t_test_greater():
    result = one_sample_t_test(
        [5, 6, 7, 8, 9],
        population_mean=4,
        alternative="greater",
    )

    assert result["statistic"] > 0
    assert result["p_value"] < 0.05
    assert result["confidence_interval"]["upper"] == float("inf")


def test_one_sample_t_test_less():
    result = one_sample_t_test(
        [1, 2, 3, 4, 5],
        population_mean=10,
        alternative="less",
    )

    assert result["statistic"] < 0
    assert result["p_value"] < 0.05
    assert result["confidence_interval"]["lower"] == -float("inf")


def test_one_sample_t_test_effect_size():
    result = one_sample_t_test(
        [2, 3, 4, 5, 6],
        population_mean=3,
    )

    assert result["cohens_d"] is not None


def test_one_sample_t_test_zero_variance():
    result = one_sample_t_test(
        [5, 5, 5, 5],
        population_mean=3,
    )

    assert result["sample_std"] == 0
    assert result["cohens_d"] is None
    assert result["warnings"]


def test_one_sample_t_test_invalid_alternative():
    with pytest.raises(ValueError):
        one_sample_t_test(
            [1, 2, 3],
            alternative="invalid",
        )


def test_one_sample_t_test_insufficient_data():
    with pytest.raises(ValueError):
        one_sample_t_test([1])


def test_one_sample_z_test():
    result = one_sample_z_test(
        [10, 12, 14, 16, 18],
        population_mean=10,
        population_std=4,
    )

    assert result["test"] == "one_sample_z_test"
    assert result["n"] == 5
    assert result["statistic"] == pytest.approx(
        (14 - 10) / (4 / np.sqrt(5))
    )


def test_one_sample_z_test_greater():
    result = one_sample_z_test(
        [10, 12, 14, 16, 18],
        population_mean=10,
        population_std=4,
        alternative="greater",
    )

    assert result["p_value"] < 0.05
    assert result["confidence_interval"]["upper"] == float("inf")


def test_one_sample_z_test_less():
    result = one_sample_z_test(
        [1, 2, 3, 4, 5],
        population_mean=10,
        population_std=3,
        alternative="less",
    )

    assert result["p_value"] < 0.05
    assert result["confidence_interval"]["lower"] == -float("inf")


def test_one_sample_z_test_missing_population_std():
    with pytest.raises(ValueError):
        one_sample_z_test([1, 2, 3])


def test_one_sample_z_test_invalid_population_std():
    with pytest.raises(ValueError):
        one_sample_z_test(
            [1, 2, 3],
            population_std=0,
        )


def test_one_sample_z_test_invalid_confidence():
    with pytest.raises(ValueError):
        one_sample_z_test(
            [1, 2, 3],
            population_std=2,
            confidence=1.5,
        )
