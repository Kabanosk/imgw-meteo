"""Canonical schema coverage and member-code resolution."""

import pytest

from imgw_meteo.canonical import (
    column_names_for_code,
    get_schema_by_code,
    is_term_code,
    member_schema_code,
    primary_code,
    schema_codes,
)
from imgw_meteo.constants import Frequency, StationType

ALL_CODES = ["k_d", "k_d_t", "o_d", "s_d", "s_d_t", "k_t", "s_t", "o_m", "k_m_d", "k_m_t", "s_m_d", "s_m_t"]

# Expected column counts, verified against real IMGW header files.
EXPECTED_COLS = {
    "k_d": 18,
    "k_d_t": 13,
    "o_d": 16,
    "s_d": 65,
    "s_d_t": 23,
    "k_t": 22,
    "s_t": 107,
    "o_m": 14,
    "k_m_d": 27,
    "k_m_t": 12,
    "s_m_d": 60,
    "s_m_t": 22,
}


@pytest.mark.parametrize("code", ALL_CODES)
def test_schema_column_count_matches_source(code):
    assert len(column_names_for_code(code)) == EXPECTED_COLS[code]


@pytest.mark.parametrize("code", ALL_CODES)
def test_every_schema_has_identity_keys(code):
    names = column_names_for_code(code)
    assert names[:4] == ["NSP", "POST", "ROK", "MC"]


def test_term_frequency_has_hour_column():
    assert "GG" in column_names_for_code("k_t")
    assert "GG" in column_names_for_code("s_t")


def test_monthly_has_no_day_column():
    assert "DZ" not in column_names_for_code("s_m_d")
    assert "DZ" not in column_names_for_code("o_m")


@pytest.mark.parametrize(
    ("freq", "stype", "expected"),
    [
        (Frequency.DAILY, StationType.SYNOP, ["s_d", "s_d_t"]),
        (Frequency.DAILY, StationType.KLIMAT, ["k_d", "k_d_t"]),
        (Frequency.DAILY, StationType.OPAD, ["o_d"]),
        (Frequency.MONTHLY, StationType.SYNOP, ["s_m_d", "s_m_t"]),
        (Frequency.MONTHLY, StationType.OPAD, ["o_m"]),
        (Frequency.TERM, StationType.SYNOP, ["s_t"]),
        (Frequency.TERM, StationType.KLIMAT, ["k_t"]),
    ],
)
def test_schema_codes(freq, stype, expected):
    assert schema_codes(freq, stype) == expected


def test_term_opad_does_not_exist():
    with pytest.raises(KeyError):
        schema_codes(Frequency.TERM, StationType.OPAD)


def test_primary_code():
    assert primary_code(Frequency.DAILY, StationType.SYNOP) == "s_d"
    assert primary_code(Frequency.MONTHLY, StationType.KLIMAT) == "k_m_d"


def test_is_term_code_distinguishes_addon_from_terminowe_primary():
    # daily/monthly term add-ons are gated:
    assert is_term_code("s_d_t") is True
    assert is_term_code("s_m_t") is True
    # terminowe primaries are NOT add-ons (always included):
    assert is_term_code("k_t") is False
    assert is_term_code("s_t") is False
    assert is_term_code("s_d") is False


@pytest.mark.parametrize(
    ("member", "code"),
    [
        ("s_d_100_2016.csv", "s_d"),
        ("s_d_t_100_2016.csv", "s_d_t"),
        ("o_d_06_2025.csv", "o_d"),
        ("k_t_01_2024.csv", "k_t"),
        ("s_m_d_2015.csv", "s_m_d"),
        ("s_m_t_2015.csv", "s_m_t"),
    ],
)
def test_member_schema_code(member, code):
    assert member_schema_code(member) == code


def test_member_schema_code_unknown():
    with pytest.raises(KeyError):
        member_schema_code("x_z_2020.csv")


def test_get_schema_by_code_unknown():
    with pytest.raises(KeyError):
        get_schema_by_code("nope")
