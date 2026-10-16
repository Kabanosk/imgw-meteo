"""Station registry parsing, normalization, and diacritic-insensitive search."""

from imgw_meteo.models import Station
from imgw_meteo.stations import StationRegistry, parse_stations

CSV = (
    '"252230120","BIAŁOWIEŻA"," 3902"\n"354180135","HEL","135"\n"249190560","JABŁONKA                      ","96510"\n'
)


def test_station_strips_all_fields_on_construction():
    s = Station(code=" 252200080 ", name="  BIAŁOWIEŻA ", code5=" 3902")
    assert s.code == "252200080"
    assert s.name == "BIAŁOWIEŻA"
    assert s.code5 == "3902"


def test_parse_stations_counts_and_strips_padding():
    stations = parse_stations(CSV)
    assert len(stations) == 3
    jablonka = next(s for s in stations if s.code == "249190560")
    assert jablonka.name == "JABŁONKA"  # fixed-width padding removed
    assert all(" " not in s.code5 for s in stations)


def test_registry_by_code():
    reg = StationRegistry(parse_stations(CSV))
    assert reg.by_code("354180135").name == "HEL"
    assert reg.by_code("  354180135  ").name == "HEL"
    assert reg.by_code("000000") is None


def test_registry_search_is_diacritic_and_case_insensitive():
    reg = StationRegistry(parse_stations(CSV))
    # 'bialowieza' (no diacritics, lowercase) should find 'BIAŁOWIEŻA'.
    found = reg.search("bialowieza")
    assert len(found) == 1
    assert found[0].code == "252230120"


def test_registry_search_substring():
    reg = StationRegistry(parse_stations(CSV))
    assert {s.name for s in reg.search("a")} >= {"BIAŁOWIEŻA", "JABŁONKA"}
