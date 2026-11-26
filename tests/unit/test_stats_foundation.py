
import numpy as np
import pandas as pd
import pytest

from icebrew.stats import (
    describe_numeric,
    describe_dataframe,
    analyze_distribution,
    correlation,
    correlation_matrix,
    mean_confidence_interval,
    proportion_confidence_interval,
    cohens_d,
    hedges_g,
)


def test_descriptive_statistics():
    result = describe_numeric([1, 2, 3, 4, 5])

    assert result["count"] == 5
    assert result["mean"] == 3
    assert result["median"] == 3
    assert result["minimum"] == 1
    assert result["maximum"] == 5


def test_descriptive_quantiles():
    result = describe_numeric([1, 2, 3, 4])

    assert result["q0.25"] == pytest.approx(1.75)
    assert result["q0.5"] == pytest.approx(2.5)
    assert result["q0.75"] == pytest.approx(3.25)


def test_describe_dataframe():
    df = pd.DataFrame({
        "a": [1, 2, 3],
        "b": [4, 5, 6],
        "c": ["x", "y", "z"],
    })

    result = describe_dataframe(df)

    assert "a" in result
    assert "b" in result
    assert "c" not in result


def test_distribution():
    result = analyze_distribution([1, 2, 3, 4, 5], bins=3)

    assert result["count"] == 5
    assert len(result["counts"]) == 3
    assert len(result["bins"]) == 4


def test_pearson_correlation():
    result = correlation([1, 2, 3], [2, 4, 6])

    assert result["coefficient"] == pytest.approx(1)
    assert result["p_value"] < 1e-6
    assert result["n"] == 3

def test_spearman_correlation():
    result = correlation(
        [1, 2, 3, 4],
        [4, 3, 2, 1],
        method="spearman",
    )

    assert result["coefficient"] == pytest.approx(-1)


def test_correlation_matrix():
    df = pd.DataFrame({
        "a": [1, 2, 3],
        "b": [2, 4, 6],
    })

    result = correlation_matrix(df)

    assert result.loc["a", "b"] == pytest.approx(1)


def test_mean_ci():
    result = mean_confidence_interval([1, 2, 3, 4, 5])

    assert result["lower"] < result["mean"]
    assert result["upper"] > result["mean"]
    assert result["n"] == 5


def test_wilson_interval():
    result = proportion_confidence_interval(50, 100)

    assert result["lower"] < 0.5
    assert result["upper"] > 0.5
    assert result["method"] == "wilson"


def test_cohens_d():
    result = cohens_d([1, 2, 3], [4, 5, 6])

    assert result["cohens_d"] < 0


def test_hedges_g():
    result = hedges_g([1, 2, 3], [4, 5, 6])

    assert result["hedges_g"] < 0
    assert "correction_factor" in result


def test_invalid_confidence():
    with pytest.raises(ValueError):
        mean_confidence_interval([1, 2, 3], confidence=1.5)


def test_empty_data():
    with pytest.raises(ValueError):
        describe_numeric([])


def test_invalid_correlation():
    with pytest.raises(ValueError):
        correlation([1, 1, 1], [2, 3, 4])
