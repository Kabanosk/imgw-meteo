"""Catalog: resolve IMGW remote paths and list directory indexes.

This module encodes the (quirky) IMGW grouping rules and also parses the
Apache-style HTML directory index so discovery stays robust if the layout
drifts. It owns *all* knowledge of how IMGW names its files — both building
expected names and recognizing/classifying names found in a listing.
"""

import re
from dataclasses import dataclass

from .constants import (
    BASE_URL,
    FREQUENCY_CODE,
    MULTI_STATION_START_YEAR,
    STATION_TYPE_CODE,
    Frequency,
    StationType,
)

# Matches hrefs in the Apache autoindex pages, e.g. href="2025/" or
# href="2026_01_s.zip".
_HREF_RE = re.compile(r'href="([^"?/][^"]*)"', re.IGNORECASE)


def type_dir_url(frequency: Frequency, station_type: StationType) -> str:
    """URL of the station-type directory, e.g. .../dobowe/synop/."""
    return f"{BASE_URL}{frequency.value}/{station_type.value}/"


def _five_year_folder(year: int) -> str:
    """Pre-2001 data lives in 5-year folders like 1996_2000."""
    start = year - ((year - 1) % 5)
    return f"{start}_{start + 4}"


def year_dir_url(frequency: Frequency, station_type: StationType, year: int) -> str:
    """URL of the directory containing a year's zip files."""
    base = type_dir_url(frequency, station_type)
    if year < MULTI_STATION_START_YEAR:
        return f"{base}{_five_year_folder(year)}/"
    return f"{base}{year}/"


def parse_index(html: str) -> list[str]:
    """Extract entry names (files and subdirectories) from an autoindex page.

    Returns names as they appear, e.g. ['2025/', '2026_01_s.zip', ...],
    excluding the 'Parent Directory' link.
    """
    names: list[str] = []
    for match in _HREF_RE.finditer(html):
        name = match.group(1)
        if name.startswith(("..", "/")):
            continue
        names.append(name)
    return names


def zip_name(
    frequency: Frequency,
    station_type: StationType,
    year: int,
    *,
    month: int | None = None,
    station_code: str | None = None,
) -> str:
    """Build the expected zip filename for a selection.

    IMGW grouping rules (meteo):

    * Current year and 2001..last-year, daily/term, non-synop OR monthly:
      one zip per MONTH, all stations -> ``YYYY_MM_<typecode>.zip``.
    * synop daily/term, 2001..last-year: one zip per STATION per year ->
      ``YYYY_<station5>_s.zip`` (uses the 3-digit short station code found in
      the directory listing).
    * Pre-2001: grouped into 5-year folders; synop is per-station-per-5-years,
      others are per-year all-stations.

    Because the exact per-station codes are only knowable from the directory
    listing, callers that need per-station files should discover names via
    :func:`parse_index` rather than relying solely on this builder.
    """
    tcode = STATION_TYPE_CODE[station_type]

    if station_code is not None:
        return f"{year}_{station_code}_{tcode}.zip"
    if month is not None:
        return f"{year}_{month:02d}_{tcode}.zip"
    # Monthly frequency: one zip per year, all stations, e.g. 2015_m_s.zip.
    if frequency is Frequency.MONTHLY:
        return f"{year}_m_{tcode}.zip"
    raise ValueError(
        "Daily/term selection requires either a month (all-station file) or a station_code (per-station file)."
    )


def member_name(
    frequency: Frequency,
    station_type: StationType,
    year: int,
    *,
    month: int | None,
    station_code: str | None,
    term: bool = False,
) -> str:
    """Expected CSV member name inside a zip.

    e.g. ``s_d_01_2026.csv`` (per-month) or ``s_d_100_2016.csv`` /
    ``s_d_t_100_2016.csv`` (per-station).
    """
    tcode = STATION_TYPE_CODE[station_type]
    fcode = FREQUENCY_CODE[frequency]
    prefix = f"{tcode}_{fcode}_t" if term else f"{tcode}_{fcode}"
    key = f"{month:02d}" if month is not None else str(station_code)
    return f"{prefix}_{key}_{year}.csv"


@dataclass(frozen=True)
class FileSpec:
    """A single zip file in the catalog that matches a selection.

    This is the typed hand-off between discovery (catalog) and the pipeline.
    ``key`` is the middle token of the filename: a 2-digit month for per-month
    files, or a station short-code for per-station files.
    """

    url: str
    name: str
    year: int
    month: int | None  # set for per-month files
    station_key: str | None  # set for per-station files


def _classify_zip(name: str, year: int) -> FileSpec | None:
    """Turn a listing entry into a FileSpec if it matches ``year``, else None.

    Recognizes the three IMGW zip layouts::

        YYYY_MM_<type>.zip     per-month, all-station  (daily/term current era)
        YYYY_<code>_<type>.zip per-station per-year    (synop daily/term)
        YYYY_m_<type>.zip      monthly, all-station    (miesieczne)
    """
    if not name.endswith(".zip"):
        return None
    stem = name[: -len(".zip")]
    parts = stem.split("_")
    if not parts or parts[0] != str(year):
        return None

    month: int | None = None
    station_key: str | None = None
    if len(parts) == 3:
        middle = parts[1]
        if middle == "m":
            pass  # monthly file: no month/station key
        elif middle.isdigit() and len(middle) == 2:
            month = int(middle)  # per-month, all-station file
        else:
            station_key = middle  # per-station file
    return FileSpec(url="", name=name, year=year, month=month, station_key=station_key)


def resolve_files(
    index_names: list[str],
    year: int,
    dir_url: str,
    *,
    months: list[int] | None = None,
    stations: list[str] | None = None,
) -> list[FileSpec]:
    """Select the zip FileSpecs in one year's listing matching the selection.

    ``index_names`` is the raw output of :func:`parse_index` for ``dir_url``.
    Filtering by month/station is done here so the pipeline never parses
    filenames itself.
    """
    station_keys: set[str] | None = None
    if stations is not None:
        station_keys = set(stations) | {s.lstrip("0") for s in stations}

    specs: list[FileSpec] = []
    for name in index_names:
        spec = _classify_zip(name, year)
        if spec is None:
            continue
        if months is not None and spec.month is not None and spec.month not in months:
            continue
        if station_keys is not None and spec.station_key is not None and spec.station_key not in station_keys:
            continue
        specs.append(
            FileSpec(
                url=dir_url + name,
                name=name,
                year=spec.year,
                month=spec.month,
                station_key=spec.station_key,
            )
        )
    return specs
