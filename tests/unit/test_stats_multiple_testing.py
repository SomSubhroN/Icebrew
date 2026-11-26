
import pytest

from icebrew.stats.multiple_testing import correct_pvalues


P = [0.001, 0.01, 0.04, 0.2]


def test_bonferroni():
    result = correct_pvalues(P, method="bonferroni")

    assert result["method"] == "bonferroni"
    assert result["number_of_tests"] == 4
    assert result["results"][0]["adjusted_p_value"] == pytest.approx(0.004)


def test_holm():
    result = correct_pvalues(P, method="holm")

    adjusted = [
        item["adjusted_p_value"]
        for item in result["results"]
    ]

    assert adjusted == pytest.approx([0.004, 0.03, 0.08, 0.2])


def test_bh():
    result = correct_pvalues(P, method="bh")

    adjusted = [
        item["adjusted_p_value"]
        for item in result["results"]
    ]

    assert adjusted == pytest.approx([0.004, 0.02, 0.0533333333, 0.2])


def test_adjusted_values_do_not_exceed_one():
    result = correct_pvalues([0.9, 0.95, 1], method="bonferroni")

    assert all(
        item["adjusted_p_value"] <= 1
        for item in result["results"]
    )


def test_invalid_method():
    with pytest.raises(ValueError):
        correct_pvalues(P, method="invalid")


def test_invalid_alpha():
    with pytest.raises(ValueError):
        correct_pvalues(P, alpha=1)


def test_empty_p_values():
    with pytest.raises(ValueError):
        correct_pvalues([])


def test_invalid_p_value():
    with pytest.raises(ValueError):
        correct_pvalues([-0.1, 0.5])


def test_nonfinite_p_values():
    with pytest.raises(ValueError):
        correct_pvalues([0.1, float("nan")])


def test_non_1d_p_values():
    with pytest.raises(ValueError):
        correct_pvalues([[0.1, 0.2]])
