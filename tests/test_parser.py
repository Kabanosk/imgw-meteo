"""Parser: zip -> cp1250 decode -> raw string DataFrame."""

import pytest

from imgw_meteo.canonical import column_names
from imgw_meteo.constants import Frequency, StationType
from imgw_meteo.exceptions import ParseError
from imgw_meteo.parser import list_members, read_zip_member


def test_list_members(synop_zip_file):
    members = list_members(synop_zip_file)
    assert set(members) == {"s_d_100_2016.csv", "s_d_t_100_2016.csv"}


def test_read_zip_member_decodes_cp1250(klimat_zip_file):
    cols = column_names(Frequency.DAILY, StationType.KLIMAT)
    df = read_zip_member(klimat_zip_file, "k_d_06_2025.csv", cols)
    assert df.shape == (2, 18)
    # cp1250 'Ł' decoded correctly, not mojibake.
    assert df["POST"].iloc[0] == "JABŁONKA"
    # values are left as raw text at this stage (not yet numeric).
    assert df["TMAX"].iloc[0] == "26.5"
    assert df["TMAX"].map(type).eq(str).all()


def test_read_zip_member_missing_member_raises(klimat_zip_file):
    cols = column_names(Frequency.DAILY, StationType.KLIMAT)
    with pytest.raises(ParseError, match="not found"):
        read_zip_member(klimat_zip_file, "nope.csv", cols)
