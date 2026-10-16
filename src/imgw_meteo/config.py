"""User-facing configuration objects (Pydantic v2, validated).

Only the *configuration* surface uses Pydantic — internal value objects
(:class:`~imgw_meteo.models.ColumnSpec`, ``Station``, ``FileSpec``) stay as
plain frozen dataclasses, since they carry trusted internal data and sit on hot
paths.
"""

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class Refresh(StrEnum):
    """When to re-download a file you've already fetched before.

    * ``"never"``    – always reuse the local copy; never re-download.
    * ``"if-stale"`` – re-download only if IMGW's file changed size (default).
                       IMGW sometimes republishes corrected data, so this keeps
                       you up to date without downloading everything every time.
    * ``"always"``   – re-download every time, ignoring the local copy.
    """

    NEVER = "never"
    IF_STALE = "if-stale"
    ALWAYS = "always"


class StandardizationConfig(BaseModel):
    """Options controlling how the raw IMGW files are cleaned up for you.

    IMGW publishes its measurements as text files whose formatting changes from
    year to year (missing-data markers, odd number formatting, extra technical
    columns, etc.). These options decide how that mess is tidied into a single,
    consistent table you can analyze directly. The defaults are sensible for
    most weather-data work — you usually don't need to change anything.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    status_to_nan: bool = Field(
        True,
        description=(
            "Treat IMGW's 'no measurement' and 'no phenomenon' markers as blank "
            "(missing) values, instead of leaving them as the raw numbers 8 and "
            "9. Strongly recommended — otherwise those codes look like real "
            "readings and can corrupt averages and statistics."
        ),
    )
    keep_status: bool = Field(
        False,
        description=(
            "Also keep IMGW's quality/status flag for each measurement, in an "
            "extra column named like 'TMAX_status'. Turn on if you want to see "
            "exactly why a value is missing or how it was recorded."
        ),
    )
    include_term: bool = Field(
        False,
        description=(
            "For synoptic stations, also include the extra set of sub-daily "
            "'term' observations (humidity, pressure, etc.). Off by default; "
            "this set is not available for every year."
        ),
    )
    add_datetime: bool = Field(
        True,
        description=(
            "Add a single calendar date column (combining the separate year, "
            "month and day columns) so you can plot and filter by date easily."
        ),
    )
    strip_strings: bool = Field(
        True,
        description=(
            "Remove the padding spaces IMGW adds around some station names, so "
            "'Jabłonka' isn't stored as 'Jabłonka           '."
        ),
    )
    normalize_decimals: bool = Field(
        True,
        description=(
            "Fix IMGW's shorthand numbers so they read normally: '-.4' becomes "
            "-0.4 and '.0' becomes 0.0. Needed because older and newer files "
            "write numbers differently."
        ),
    )
    english_aliases: bool = Field(
        False,
        description=(
            "Rename the Polish IMGW column codes (TMAX, SMDB, ...) to English "
            "names (max_temp, precip_sum, ...). Off by default, which keeps the "
            "original IMGW codes."
        ),
    )
    schema_version: str = Field(
        "1.0",
        description=(
            "Which version of this library's column layout to use. Pin it if you "
            "need your columns to stay identical across future library updates."
        ),
    )


class ClientConfig(BaseModel):
    """Where downloaded files are stored and how the download behaves."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    cache_dir: str | None = Field(
        None,
        description=(
            "Folder where downloaded IMGW files are saved and reused, so you "
            "don't re-download the same data. Leave as None for the default "
            "location (~/.cache/imgw-meteo)."
        ),
    )
    offline: bool = Field(
        False,
        description=(
            "Work only from already-downloaded files and never use the internet. "
            "Useful on a machine with no connection; errors if a file is missing."
        ),
    )
    refresh: Refresh = Field(
        Refresh.IF_STALE,
        description="When to re-download a file you already have (see Refresh).",
    )
    timeout: float = Field(
        30.0,
        gt=0,
        description="How many seconds to wait for a download before giving up.",
    )
