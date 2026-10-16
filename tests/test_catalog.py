"""Catalog: URL building, index parsing, and the grouping-rule resolver."""

from imgw_meteo import catalog
from imgw_meteo.constants import Frequency, StationType


def test_type_dir_url():
    url = catalog.type_dir_url(Frequency.DAILY, StationType.SYNOP)
    assert url.endswith("/dobowe/synop/")


def test_year_dir_url_modern():
    url = catalog.year_dir_url(Frequency.DAILY, StationType.KLIMAT, 2025)
    assert url.endswith("/dobowe/klimat/2025/")


def test_year_dir_url_pre_2001_five_year_folder():
    # 1998 falls in the 1996_2000 bucket.
    url = catalog.year_dir_url(Frequency.DAILY, StationType.SYNOP, 1998)
    assert url.endswith("/1996_2000/")


def test_parse_index_filters_parent_and_queries():
    html = '<a href="../">Parent</a><a href="2025/">2025/</a><a href="2026_01_s.zip">x</a><a href="?C=N;O=D">sort</a>'
    names = catalog.parse_index(html)
    assert "2025/" in names
    assert "2026_01_s.zip" in names
    assert not any(n.startswith(("..", "?")) for n in names)


def test_is_term_member():
    assert catalog.is_term_member("s_d_t_100_2016.csv") is True
    assert catalog.is_term_member("s_d_100_2016.csv") is False
    assert catalog.is_term_member("k_d_06_2025.csv") is False


def test_resolve_per_month_file():
    specs = catalog.resolve_files(["2026_01_s.zip", "2026_02_s.zip"], 2026, "http://x/")
    months = {s.month for s in specs}
    assert months == {1, 2}
    assert all(s.station_key is None for s in specs)
    assert specs[0].url == "http://x/2026_01_s.zip"


def test_resolve_per_month_with_month_filter():
    specs = catalog.resolve_files(["2026_01_s.zip", "2026_02_s.zip"], 2026, "http://x/", months=[2])
    assert [s.month for s in specs] == [2]


def test_resolve_per_station_file():
    specs = catalog.resolve_files(["2016_100_s.zip", "2016_105_s.zip"], 2016, "http://x/")
    keys = {s.station_key for s in specs}
    assert keys == {"100", "105"}
    assert all(s.month is None for s in specs)


def test_resolve_per_station_filter_handles_leading_zeros():
    # Selecting "100" must match "100"; also tolerate zero-stripped forms.
    specs = catalog.resolve_files(["2016_100_s.zip", "2016_105_s.zip"], 2016, "http://x/", stations=["100"])
    assert [s.station_key for s in specs] == ["100"]


def test_resolve_ignores_wrong_year_and_non_zip():
    specs = catalog.resolve_files(["2025_01_s.zip", "2026_01_s.zip", "s_d_format.txt"], 2026, "http://x/")
    assert [s.name for s in specs] == ["2026_01_s.zip"]
