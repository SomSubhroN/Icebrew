
import pandas as pd
import pytest

from icebrew.data.datetime_utils import (
    convert_timezone,
    datetime_difference,
    extract_datetime,
    filter_datetime,
    parse_datetime,
    round_datetime,
)


@pytest.fixture
def sample_df():
    return pd.DataFrame(
        {
            "date": pd.to_datetime(
                ["2024-01-01", "2024-02-15", "2024-03-31"]
            ),
            "start": pd.to_datetime(
                ["2024-01-01", "2024-02-01", "2024-03-01"]
            ),
            "end": pd.to_datetime(
                ["2024-01-03", "2024-02-05", "2024-03-10"]
            ),
        }
    )


# --------------------------------------------------
# PARSING
# --------------------------------------------------

def test_parse_datetime():
    df = pd.DataFrame({"date": ["2024-01-01", "2024-02-01"]})

    result = parse_datetime(df, "date")

    assert pd.api.types.is_datetime64_any_dtype(result["date"])


def test_parse_multiple_columns():
    df = pd.DataFrame(
        {
            "a": ["2024-01-01"],
            "b": ["2024-02-01"],
        }
    )

    result = parse_datetime(df, ["a", "b"])

    assert pd.api.types.is_datetime64_any_dtype(result["a"])
    assert pd.api.types.is_datetime64_any_dtype(result["b"])


def test_parse_datetime_coerce():
    df = pd.DataFrame({"date": ["2024-01-01", "invalid"]})

    result = parse_datetime(df, "date", errors="coerce")

    assert result["date"].isna().sum() == 1


def test_parse_datetime_ignore():
    df = pd.DataFrame({"date": ["2024-01-01", "invalid"]})

    result = parse_datetime(df, "date", errors="ignore")

    assert result["date"].dtype == df["date"].dtype


def test_parse_datetime_dayfirst():
    df = pd.DataFrame({"date": ["31/01/2024"]})

    result = parse_datetime(df, "date", dayfirst=True)

    assert result["date"].iloc[0].month == 1
    assert result["date"].iloc[0].day == 31


def test_parse_datetime_invalid_errors_mode():
    df = pd.DataFrame({"date": ["invalid"]})

    with pytest.raises(ValueError):
        parse_datetime(df, "date", errors="invalid")


# --------------------------------------------------
# EXTRACTION
# --------------------------------------------------

def test_extract_components(sample_df):
    result = extract_datetime(
        sample_df,
        "date",
        components=["year", "month", "day"],
    )

    assert result["date_year"].iloc[0] == 2024
    assert result["date_month"].iloc[1] == 2
    assert result["date_day"].iloc[2] == 31


def test_extract_day_of_week(sample_df):
    result = extract_datetime(
        sample_df,
        "date",
        components="dayofweek",
    )

    assert "date_dayofweek" in result.columns


def test_extract_week_and_quarter(sample_df):
    result = extract_datetime(
        sample_df,
        "date",
        components=["week", "quarter"],
    )

    assert "date_week" in result.columns
    assert "date_quarter" in result.columns


def test_extract_month_boundaries(sample_df):
    result = extract_datetime(
        sample_df,
        "date",
        components=["is_month_start", "is_month_end"],
    )

    assert result["date_is_month_start"].iloc[0]
    assert result["date_is_month_end"].iloc[2]


def test_extract_invalid_component(sample_df):
    with pytest.raises(ValueError):
        extract_datetime(sample_df, "date", components=["invalid"])


def test_extract_non_datetime():
    df = pd.DataFrame({"date": ["2024-01-01"]})

    with pytest.raises(TypeError):
        extract_datetime(df, "date")


# --------------------------------------------------
# DIFFERENCES
# --------------------------------------------------

def test_datetime_difference_days(sample_df):
    result = datetime_difference(
        sample_df,
        "start",
        "end",
        unit="days",
    )

    assert result["end_minus_start"].iloc[0] == 2


def test_datetime_difference_hours():
    df = pd.DataFrame(
        {
            "start": pd.to_datetime(["2024-01-01 00:00"]),
            "end": pd.to_datetime(["2024-01-01 12:00"]),
        }
    )

    result = datetime_difference(df, "start", "end", unit="hours")

    assert result["end_minus_start"].iloc[0] == 12


def test_datetime_difference_custom_column(sample_df):
    result = datetime_difference(
        sample_df,
        "start",
        "end",
        output_column="duration",
    )

    assert "duration" in result.columns


def test_datetime_difference_invalid_unit(sample_df):
    with pytest.raises(ValueError):
        datetime_difference(
            sample_df,
            "start",
            "end",
            unit="invalid",
        )


# --------------------------------------------------
# FILTERING
# --------------------------------------------------

def test_filter_datetime(sample_df):
    result = filter_datetime(
        sample_df,
        "date",
        start="2024-02-01",
        end="2024-03-01",
    )

    assert len(result) == 1
    assert result["date"].iloc[0] == pd.Timestamp("2024-02-15")


def test_filter_datetime_inclusive_left(sample_df):
    result = filter_datetime(
        sample_df,
        "date",
        start="2024-02-15",
        inclusive="left",
    )

    assert len(result) == 2
    assert result["date"].iloc[0] == pd.Timestamp("2024-02-15")


def test_filter_datetime_exclusive(sample_df):
    result = filter_datetime(
        sample_df,
        "date",
        start="2024-02-15",
        inclusive="neither",
    )

    assert len(result) == 1
    assert result["date"].iloc[0] == pd.Timestamp("2024-03-31")


def test_filter_datetime_right_inclusive():
    df = pd.DataFrame(
        {
            "date": pd.to_datetime(
                ["2024-01-01", "2024-01-02", "2024-01-03"]
            )
        }
    )

    result = filter_datetime(
        df,
        "date",
        end="2024-01-02",
        inclusive="right",
    )

    assert len(result) == 2


def test_filter_datetime_invalid_inclusive(sample_df):
    with pytest.raises(ValueError):
        filter_datetime(sample_df, "date", inclusive="invalid")


def test_filter_datetime_invalid_column():
    df = pd.DataFrame({"x": [1, 2]})

    with pytest.raises(KeyError):
        filter_datetime(df, "missing")


# --------------------------------------------------
# TIMEZONES
# --------------------------------------------------

def test_timezone_conversion():
    df = pd.DataFrame(
        {
            "date": pd.to_datetime(["2024-01-01 12:00"]),
        }
    )

    result = convert_timezone(
        df,
        "date",
        "Asia/Kolkata",
        assume_timezone="UTC",
    )

    assert str(result["date"].dt.tz) == "Asia/Kolkata"
    assert result["date"].iloc[0].hour == 17


def test_timezone_naive_requires_timezone():
    df = pd.DataFrame(
        {
            "date": pd.to_datetime(["2024-01-01"]),
        }
    )

    with pytest.raises(ValueError):
        convert_timezone(df, "date", "Asia/Kolkata")


def test_timezone_aware_conversion():
    df = pd.DataFrame(
        {
            "date": pd.to_datetime(["2024-01-01"]).tz_localize("UTC"),
        }
    )

    result = convert_timezone(df, "date", "Asia/Kolkata")

    assert str(result["date"].dt.tz) == "Asia/Kolkata"


# --------------------------------------------------
# ROUNDING
# --------------------------------------------------

def test_round_datetime_floor():
    df = pd.DataFrame(
        {
            "date": pd.to_datetime(
                [
                    "2024-01-01 12:35",
                    "2024-02-15 09:45",
                    "2024-03-31 18:20",
                ]
            )
        }
    )

    result = round_datetime(
        df,
        "date",
        frequency="h",
        method="floor",
    )

    assert result["date"].iloc[0] == pd.Timestamp("2024-01-01 12:00")
    assert result["date"].iloc[1] == pd.Timestamp("2024-02-15 09:00")
    assert result["date"].iloc[2] == pd.Timestamp("2024-03-31 18:00")


def test_round_datetime_ceil():
    df = pd.DataFrame(
        {
            "date": pd.to_datetime(["2024-01-01 12:35"]),
        }
    )

    result = round_datetime(
        df,
        "date",
        frequency="h",
        method="ceil",
    )

    assert result["date"].iloc[0] == pd.Timestamp("2024-01-01 13:00")


def test_round_datetime_round():
    df = pd.DataFrame(
        {
            "date": pd.to_datetime(["2024-01-01 12:35"]),
        }
    )

    result = round_datetime(
        df,
        "date",
        frequency="h",
        method="round",
    )

    assert result["date"].iloc[0] == pd.Timestamp("2024-01-01 13:00")


def test_round_datetime_output_column(sample_df):
    result = round_datetime(
        sample_df,
        "date",
        frequency="D",
        output_column="rounded",
    )

    assert "rounded" in result.columns


def test_round_invalid_method(sample_df):
    with pytest.raises(ValueError):
        round_datetime(
            sample_df,
            "date",
            frequency="D",
            method="invalid",
        )


# --------------------------------------------------
# NON-MUTATION
# --------------------------------------------------

def test_non_mutating(sample_df):
    original = sample_df.copy(deep=True)

    parse_datetime(sample_df, "date")
    extract_datetime(sample_df, "date")
    datetime_difference(sample_df, "start", "end")
    filter_datetime(sample_df, "date")
    round_datetime(sample_df, "date", frequency="D")

    pd.testing.assert_frame_equal(sample_df, original)
