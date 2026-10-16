"""Orchestration: resolve -> download -> read -> standardize -> combine.

A thin, testable sequence of named steps. Holds no state; the ``Dataset`` handle
calls :func:`load_selection`.
"""

import warnings

import pandas as pd

from . import catalog
from .canonical import column_names_for_code, is_term_code, member_schema_code
from .catalog import FileSpec
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


def _merge_members(members: dict[str, pd.DataFrame], config: StandardizationConfig) -> pd.DataFrame:
    """Merge the members of one zip into a single wide frame.

    The primary (non-term) member provides the base rows; term members are
    joined on the shared identity columns so their measurements become extra
    columns rather than extra rows. Overlapping measurement names from a term
    member are suffixed with ``_t`` to avoid collisions.
    """
    primary_code = next((c for c in members if not is_term_code(c)), None)
    if primary_code is None:
        # Only term member(s) present (rare); just concat them.
        return pd.concat(members.values(), ignore_index=True)

    base = members[primary_code]
    join_keys = [k for k in ("datetime", "NSP", "ROK", "MC", "DZ", "GG") if k in base.columns]
    for code, frame in members.items():
        if code == primary_code:
            continue
        value_cols = [c for c in frame.columns if c not in join_keys]
        right = frame[join_keys + value_cols]
        overlap = (set(value_cols) & set(base.columns)) - set(join_keys)
        if overlap:
            right = right.rename(columns={c: f"{c}_t" for c in overlap})
        base = base.merge(right, on=join_keys, how="left")
    return base


def _read_and_standardize(
    downloader: Downloader,
    spec: FileSpec,
    config: StandardizationConfig,
) -> pd.DataFrame:
    """Download one zip, standardize each member, and merge into one frame.

    Each member is matched to its own canonical schema by filename, so dual
    schemas (e.g. ``s_d`` + ``s_d_t``, or monthly ``*_m_d`` + ``*_m_t``) are
    both handled correctly. Term members are included only when
    ``config.include_term`` is set, and are merged onto the primary member's
    rows (wider rows), not stacked as extra rows.
    """
    zip_path = downloader.fetch_file(spec.url)
    members: dict[str, pd.DataFrame] = {}
    for member in list_members(zip_path):
        try:
            code = member_schema_code(member)
        except KeyError:
            warnings.warn(f"skipping member with unknown schema: {member}", stacklevel=2)
            continue
        if is_term_code(code) and not config.include_term:
            continue
        cols = column_names_for_code(code)
        raw = read_zip_member(zip_path, member, cols)
        members[code] = standardize(raw, code, config)
    if not members:
        return pd.DataFrame()
    return _merge_members(members, config)


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
        frame = _read_and_standardize(downloader, spec, config)
        if not frame.empty:
            frames.append(frame)
    if not frames:
        raise SelectionError("selection produced no data")
    df = pd.concat(frames, ignore_index=True)
    if stations:
        df = _filter_stations(df, stations)
    return df
