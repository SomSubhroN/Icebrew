import pandas as pd
import pytest

from icebrew.data.inspector import inspect_data


def test_inspect_data():
    df = pd.DataFrame({
        "name": ["Alice", "Bob", "Bob"],
        "age": [21, 22, 22],
    })

    result = inspect_data(df)

    assert result["shape"] == (3, 2)
    assert result["columns"] == ["name", "age"]
    assert result["duplicates"] == 1
    assert result["missing_values"]["name"] == 0
    assert len(result["preview"]) == 3


def test_inspect_preview_limit():
    df = pd.DataFrame({"value": range(10)})

    result = inspect_data(df, preview_rows=3)

    assert len(result["preview"]) == 3


def test_inspect_invalid_input():
    with pytest.raises(TypeError):
        inspect_data("not a dataframe")


def test_inspect_negative_preview():
    df = pd.DataFrame({"value": [1]})

    with pytest.raises(ValueError):
        inspect_data(df, preview_rows=-1)