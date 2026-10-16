"""Orchestration: resolve -> download -> read -> standardize -> combine.

A thin, testable sequence of named steps. Holds no state; the ``Dataset`` handle
calls :func:`load_selection`.
"""

import warnings

import pandas as pd

from . import catalog
from .canonical import column_names
from .catalog import FileSpec, is_term_member
from .config import StandardizationConfig
from .constants import Frequency, StationType
from .downloader import Downloader
from .exceptions import SelectionError
from .parser import list_members, read_zip_member
from .standardize import standardize


def resolve(
    downloader: Downloader,
    frequency: Frequency,
    station_type: StationType,
    years: list[int],
    months: list[int] | None,
    stations: list[str] | None,
) -> list[FileSpec]:
    """Discover the zip files matching a selection via the directory index.

    :param downloader: Downloader used to fetch directory index pages.
    :param frequency: Temporal resolution of the data.
    :param station_type: Station type to look under.
    :param years: Years to search.
    :param months: Months to restrict to, or ``None`` for all.
    :param stations: Station codes to restrict to, or ``None`` for all.
    :returns: One :class:`~imgw_meteo.catalog.FileSpec` per matching zip file.
    :rtype: list[imgw_meteo.catalog.FileSpec]
    :raises imgw_meteo.exceptions.SelectionError: If nothing matches.
    """
    specs: list[FileSpec] = []
    for year in years:
        dir_url = catalog.year_dir_url(frequency, station_type, year)
        names = catalog.parse_index(downloader.fetch_text(dir_url))
        specs.extend(catalog.resolve_files(names, year, dir_url, months=months, stations=stations))
    if not specs:
        raise SelectionError(f"no files matched selection {frequency.value}/{station_type.value} years={years}")
    return specs


def _read_and_standardize(
    downloader: Downloader,
    spec: FileSpec,
    frequency: Frequency,
    station_type: StationType,
    config: StandardizationConfig,
) -> list[pd.DataFrame]:
    """Download one zip and standardize each relevant CSV member."""
    cols = column_names(frequency, station_type)
    zip_path = downloader.fetch_file(spec.url)
    frames: list[pd.DataFrame] = []
    for member in list_members(zip_path):
        if is_term_member(member):
            # The synop term (s_d_t) schema is not defined yet. Honor the flag
            # honestly: warn when the user explicitly asked for it, never claim
            # success silently.
            if config.include_term:
                warnings.warn(
                    "include_term=True but the synop term (s_d_t) schema is not "
                    "implemented yet; term members are skipped.",
                    stacklevel=2,
                )
            continue
        raw = read_zip_member(zip_path, member, cols)
        frames.append(standardize(raw, frequency, station_type, config))
    return frames


def _filter_stations(df: pd.DataFrame, stations: list[str]) -> pd.DataFrame:
    """Post-filter per-station only when values match full NSP codes.

    Per-station files are selected by the short directory code (e.g. "100"),
    but NSP holds the full code (e.g. "354150100"); in that case file-level
    selection already did the work and we must not drop everything.
    """
    key = "NSP" if "NSP" in df.columns else "station_code"
    if key not in df.columns:
        return df
    present = set(df[key].dropna().astype(str))
    wanted = {s for s in stations if s in present}
    if not wanted:
        return df
    return df[df[key].astype(str).isin(wanted)].reset_index(drop=True)


def load_selection(
    downloader: Downloader,
    frequency: Frequency,
    station_type: StationType,
    years: list[int],
    months: list[int] | None,
    stations: list[str] | None,
    config: StandardizationConfig,
) -> pd.DataFrame:
    """Run the full pipeline for a selection into a single standardized frame.

    :param downloader: Downloader used for index pages and zip files.
    :param frequency: Temporal resolution of the data.
    :param station_type: Station type to load.
    :param years: Years to load.
    :param months: Months to restrict to, or ``None`` for all.
    :param stations: Station codes to restrict to, or ``None`` for all.
    :param config: Standardization options applied to every file.
    :returns: One combined, cleaned, typed table for the whole selection.
    :rtype: pandas.DataFrame
    :raises imgw_meteo.exceptions.SelectionError: If no files match or no data
        is produced.
    """
    specs = resolve(downloader, frequency, station_type, years, months, stations)
    frames: list[pd.DataFrame] = []
    for spec in specs:
        frames.extend(_read_and_standardize(downloader, spec, frequency, station_type, config))
    if not frames:
        raise SelectionError("selection produced no data")
    df = pd.concat(frames, ignore_index=True)
    if stations:
        df = _filter_stations(df, stations)
    return df
