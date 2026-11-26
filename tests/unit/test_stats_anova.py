
import numpy as np
import pytest

from icebrew.stats.anova import (
    one_way_anova,
    welch_anova,
    tukey_hsd,
    games_howell,
)


A = [10, 12, 13, 11, 14, 12]
B = [20, 22, 21, 23, 19, 24]
C = [30, 29, 31, 32, 28, 30]


def test_one_way_anova():
    result = one_way_anova({"A": A, "B": B, "C": C})

    assert result["test"] == "one_way_anova"
    assert result["p_value"] < 0.05
    assert result["groups"] == 3
    assert result["total_n"] == 18
    assert "eta_squared" in result["effect_size"]


def test_one_way_anova_names():
    result = one_way_anova([A, B], names=["Control", "Treatment"])

    assert result["group_summary"]["Control"]["n"] == 6
    assert result["group_summary"]["Treatment"]["n"] == 6


def test_one_way_anova_invalid_group_count():
    with pytest.raises(ValueError):
        one_way_anova([A])


def test_one_way_anova_empty_group():
    with pytest.raises(ValueError):
        one_way_anova([[], B])


def test_welch_anova():
    result = welch_anova({"A": A, "B": B, "C": C})

    assert result["test"] == "welch_anova"
    assert result["p_value"] < 0.05
    assert result["groups"] == 3


def test_welch_anova_small_group():
    with pytest.raises(ValueError):
        welch_anova({"A": [1], "B": B})


def test_welch_anova_zero_variance():
    with pytest.raises(ValueError):
        welch_anova({"A": [1, 1, 1], "B": B})


def test_tukey_hsd():
    result = tukey_hsd({"A": A, "B": B, "C": C})

    assert result["test"] == "tukey_hsd"
    assert len(result["comparisons"]) == 3
    assert all(
        comparison["p_value"] < 0.05
        for comparison in result["comparisons"]
    )


def test_tukey_invalid_alpha():
    with pytest.raises(ValueError):
        tukey_hsd({"A": A, "B": B}, alpha=1)


def test_games_howell():
    result = games_howell({"A": A, "B": B, "C": C})

    assert result["test"] == "games_howell"
    assert len(result["comparisons"]) == 3
    assert all(
        comparison["p_value"] < 0.05
        for comparison in result["comparisons"]
    )


def test_games_howell_small_group():
    with pytest.raises(ValueError):
        games_howell({"A": [1], "B": B})


def test_games_howell_invalid_alpha():
    with pytest.raises(ValueError):
        games_howell({"A": A, "B": B}, alpha=0)
