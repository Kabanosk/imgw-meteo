"""Enum parsing (English aliases + Polish directory names)."""

import pytest

from imgw_meteo.constants import Frequency, StationType


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("daily", Frequency.DAILY),
        ("dobowe", Frequency.DAILY),
        ("DAILY", Frequency.DAILY),
        ("monthly", Frequency.MONTHLY),
        ("miesieczne", Frequency.MONTHLY),
        ("term", Frequency.TERM),
        ("terminowe", Frequency.TERM),
        (Frequency.DAILY, Frequency.DAILY),
    ],
)
def test_frequency_parse(value, expected):
    assert Frequency.parse(value) is expected


def test_frequency_parse_invalid():
    with pytest.raises(ValueError, match="unknown frequency"):
        Frequency.parse("weekly")


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("synop", StationType.SYNOP),
        ("SYNOP", StationType.SYNOP),
        ("klimat", StationType.KLIMAT),
        ("opad", StationType.OPAD),
        (StationType.OPAD, StationType.OPAD),
    ],
)
def test_station_type_parse(value, expected):
    assert StationType.parse(value) is expected


def test_station_type_parse_invalid():
    with pytest.raises(ValueError, match="unknown station type"):
        StationType.parse("radar")


def test_enum_value_is_polish_dirname():
    # URLs depend on .value being the Polish directory name.
    assert Frequency.DAILY.value == "dobowe"
    assert StationType.SYNOP.value == "synop"
