"""End-to-end pipeline/client tests with mocked HTTP (no real network)."""

import pytest

from imgw_meteo import ClientConfig, IMGWClient

BASE = "https://dane.imgw.pl/data/dane_pomiarowo_obserwacyjne/dane_meteorologiczne/dobowe"


def _index_html(entries: list[str]) -> str:
    links = "".join(f'<a href="{e}">{e}</a>' for e in entries)
    return f'<html><a href="../">Parent</a>{links}</html>'


@pytest.fixture
def client(tmp_path):
    # refresh="never" -> a single GET per file, no HEAD staleness check.
    return IMGWClient(config=ClientConfig(cache_dir=str(tmp_path), refresh="never"))


def test_klimat_end_to_end(httpx_mock, client, klimat_zip_bytes):
    httpx_mock.add_response(url=f"{BASE}/klimat/2025/", text=_index_html(["2025_06_k.zip"]))
    httpx_mock.add_response(url=f"{BASE}/klimat/2025/2025_06_k.zip", content=klimat_zip_bytes)

    df = client.select(frequency="daily", station_type="klimat", years=2025, months=6).get_dataframe()

    assert df.shape == (2, 13)
    assert df["TMAX"].dtype == "float32"
    assert df["POST"].iloc[0] == "JABŁONKA"
    assert str(df["datetime"].iloc[0].date()) == "2025-06-01"


def test_synop_merges_term_member(httpx_mock, tmp_path, synop_zip_bytes):
    httpx_mock.add_response(url=f"{BASE}/synop/2016/", text=_index_html(["2016_100_s.zip"]))
    httpx_mock.add_response(url=f"{BASE}/synop/2016/2016_100_s.zip", content=synop_zip_bytes)
    # include_term=True merges the term member onto the primary rows (wider),
    # not as extra rows.
    from imgw_meteo import StandardizationConfig

    client = IMGWClient(
        config=ClientConfig(cache_dir=str(tmp_path), refresh="never"),
        standardization=StandardizationConfig(include_term=True),
    )
    df = client.select(frequency="daily", station_type="synop", years=2016, stations="100").get_dataframe()

    # Still one row (merged, not stacked); term columns (e.g. CPW) now present.
    assert len(df) == 1
    assert float(df["TMAX"].iloc[0]) == pytest.approx(-0.4, abs=1e-4)
    assert "CPW" in df.columns  # from the s_d_t term member


def test_synop_excludes_term_by_default(httpx_mock, tmp_path, synop_zip_bytes):
    httpx_mock.add_response(url=f"{BASE}/synop/2016/", text=_index_html(["2016_100_s.zip"]))
    httpx_mock.add_response(url=f"{BASE}/synop/2016/2016_100_s.zip", content=synop_zip_bytes)
    client = IMGWClient(config=ClientConfig(cache_dir=str(tmp_path), refresh="never"))
    df = client.select(frequency="daily", station_type="synop", years=2016, stations="100").get_dataframe()
    assert len(df) == 1
    assert "CPW" not in df.columns  # term member not included


def test_available_years(httpx_mock, client):
    httpx_mock.add_response(
        url=f"{BASE}/synop/",
        text=_index_html(["2001/", "2025/", "2026/", "s_d_format.txt"]),
    )
    years = client.available_years("daily", "synop")
    assert years == ["2001", "2025", "2026"]


def test_no_match_raises_selection_error(httpx_mock, client):
    from imgw_meteo.exceptions import SelectionError

    httpx_mock.add_response(url=f"{BASE}/klimat/2025/", text=_index_html([]))
    with pytest.raises(SelectionError):
        client.select(frequency="daily", station_type="klimat", years=2025).get_dataframe()
