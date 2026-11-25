import pandas as pd
import pytest

from icebrew.data.profiler import profile_data


def test_profile_numeric_column():
    df = pd.DataFrame({"score": [10, 20, 30, None]})

    result = profile_data(df)

    assert result["score"]["count"] == 3
    assert result["score"]["missing"] == 1
    assert result["score"]["missing_percent"] == 25.0
    assert result["score"]["mean"] == 20.0
    assert result["score"]["median"] == 20.0


def test_profile_categorical_column():
    df = pd.DataFrame({"city": ["Kolkata", "Delhi", "Kolkata"]})

    result = profile_data(df)

    assert result["city"]["unique"] == 2
    assert result["city"]["top_values"]["Kolkata"] == 2


def test_profile_empty_numeric_column():
    df = pd.DataFrame({
        "score": pd.Series([None, None], dtype="float64")
    })

    result = profile_data(df)

    assert result["score"]["mean"] is None
    assert result["score"]["missing"] == 2


def test_profile_invalid_input():
    with pytest.raises(TypeError):
        profile_data("invalid")