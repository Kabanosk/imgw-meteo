"""Standardization: the data-cleaning heart. Dtypes, decimals, status->NaN."""

import pandas as pd

from imgw_meteo.canonical import column_names
from imgw_meteo.config import StandardizationConfig
from imgw_meteo.constants import Frequency, StationType
from imgw_meteo.standardize import _fix_decimal, standardize


def _raw_klimat() -> pd.DataFrame:
    cols = column_names(Frequency.DAILY, StationType.KLIMAT)
    # Two rows: row0 has a real TMNG-missing (status 8), row1 fine.
    row0 = [
        "249190560",
        "JABŁONKA",
        "2025",
        "06",
        "01",
        "26.5",
        "",
        "8.3",
        "",
        "16.6",
        "",
        "",
        "8",
        "1.5",
        "",
        "W",
        "",
        "9",
    ]
    row1 = [
        "249190560",
        "JABŁONKA",
        "2025",
        "06",
        "02",
        "26.6",
        "",
        "11.8",
        "",
        "19.1",
        "",
        "5.0",
        "",
        "14.4",
        "",
        "W",
        "",
        "9",
    ]
    return pd.DataFrame([row0, row1], columns=cols, dtype=str)


def test_fix_decimal():
    assert _fix_decimal("-.4") == "-0.4"
    assert _fix_decimal(".0") == "0.0"
    assert _fix_decimal("1.9") == "1.9"
    assert _fix_decimal("-12.3") == "-12.3"


def test_dtypes_are_canonical_not_inferred():
    df = standardize(_raw_klimat(), "k_d", StandardizationConfig())
    assert df["TMAX"].dtype == "float32"
    assert df["ROK"].dtype == "Int16"
    assert str(df["ROOP"].dtype) == "category"


def test_status_8_becomes_nan():
    df = standardize(_raw_klimat(), "k_d", StandardizationConfig())
    # row0 TMNG had status "8" -> missing; row1 had a value.
    assert pd.isna(df["TMNG"].iloc[0])
    assert df["TMNG"].iloc[1] == 5.0


def test_status_to_nan_disabled_keeps_value():
    cfg = StandardizationConfig(status_to_nan=False)
    df = standardize(_raw_klimat(), "k_d", cfg)
    # With conversion off, the empty TMNG cell stays NaN but is not forced by status.
    # row1 value remains.
    assert df["TMNG"].iloc[1] == 5.0


def test_datetime_assembled():
    df = standardize(_raw_klimat(), "k_d", StandardizationConfig())
    assert "datetime" in df.columns
    assert str(df["datetime"].iloc[0].date()) == "2025-06-01"


def test_add_datetime_disabled():
    cfg = StandardizationConfig(add_datetime=False)
    df = standardize(_raw_klimat(), "k_d", cfg)
    assert "datetime" not in df.columns


def test_keep_status_adds_columns():
    cfg = StandardizationConfig(keep_status=True)
    df = standardize(_raw_klimat(), "k_d", cfg)
    assert "WTMNG_status" in df.columns
    assert df["WTMNG_status"].iloc[0] == "8"


def test_english_aliases():
    cfg = StandardizationConfig(english_aliases=True)
    df = standardize(_raw_klimat(), "k_d", cfg)
    assert "year" in df.columns  # ROK -> year
    assert "ROK" not in df.columns


def test_string_padding_stripped():
    cols = column_names(Frequency.DAILY, StationType.KLIMAT)
    row = [
        "249190560",
        "JABŁONKA        ",
        "2025",
        "06",
        "01",
        "26.5",
        "",
        "8.3",
        "",
        "16.6",
        "",
        "5.0",
        "",
        "1.5",
        "",
        "W",
        "",
        "9",
    ]
    raw = pd.DataFrame([row], columns=cols, dtype=str)
    df = standardize(raw, "k_d", StandardizationConfig())
    assert df["POST"].iloc[0] == "JABŁONKA"
