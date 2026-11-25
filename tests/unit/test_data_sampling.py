import pandas as pd
import pytest

from icebrew.data.sampling import sample_data, stratified_sample, split_data


@pytest.fixture
def sample_df():
    return pd.DataFrame({
        "group": ["A", "A", "A", "B", "B", "B", "B", "B"],
        "score": range(8),
    })


def test_sample_n(sample_df):
    result = sample_data(sample_df, n=3, random_state=42)

    assert len(result) == 3


def test_sample_fraction(sample_df):
    result = sample_data(sample_df, fraction=0.5, random_state=42)

    assert len(result) == 4


def test_sample_reproducibility(sample_df):
    a = sample_data(sample_df, n=3, random_state=42)
    b = sample_data(sample_df, n=3, random_state=42)

    assert a.equals(b)


def test_sample_without_replacement(sample_df):
    result = sample_data(sample_df, n=5, random_state=42)

    assert len(result) == 5
    assert result.index.nunique() == 5


def test_sample_with_replacement(sample_df):
    result = sample_data(sample_df, n=20, replace=True, random_state=42)

    assert len(result) == 20


def test_sample_invalid_arguments(sample_df):
    with pytest.raises(ValueError):
        sample_data(sample_df)

    with pytest.raises(ValueError):
        sample_data(sample_df, n=2, fraction=0.5)

    with pytest.raises(ValueError):
        sample_data(sample_df, fraction=1.5)


def test_stratified_sample(sample_df):
    result = stratified_sample(
        sample_df,
        "group",
        fraction=0.5,
        random_state=42,
    )

    assert "A" in result["group"].values
    assert "B" in result["group"].values


def test_stratified_missing_column(sample_df):
    with pytest.raises(KeyError):
        stratified_sample(sample_df, "missing", fraction=0.5)


def test_stratified_missing_values():
    df = pd.DataFrame({"group": ["A", None, "B"]})

    with pytest.raises(ValueError):
        stratified_sample(df, "group", fraction=0.5)


def test_split_data(sample_df):
    train, test = split_data(sample_df, test_size=0.25, random_state=42)

    assert len(train) + len(test) == len(sample_df)
    assert len(test) == 2


def test_split_reproducibility(sample_df):
    train1, test1 = split_data(sample_df, random_state=42)
    train2, test2 = split_data(sample_df, random_state=42)

    assert train1.equals(train2)
    assert test1.equals(test2)


def test_split_no_shuffle(sample_df):
    train, test = split_data(sample_df, shuffle=False)

    assert train.index.tolist() == list(range(2, 8))
    assert test.index.tolist() == [0, 1]


def test_split_invalid():
    df = pd.DataFrame({"x": [1]})

    with pytest.raises(ValueError):
        split_data(df)


def test_sample_does_not_mutate(sample_df):
    original = sample_df.copy(deep=True)

    sample_data(sample_df, n=2, random_state=42)

    assert sample_df.equals(original)