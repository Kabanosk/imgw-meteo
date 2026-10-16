"""Constants, enums and base configuration for the IMGW meteo data source."""

from __future__ import annotations

from enum import StrEnum

#: Root of the IMGW meteorological measurement data tree.
BASE_URL = "https://dane.imgw.pl/data/dane_pomiarowo_obserwacyjne/dane_meteorologiczne/"

#: Station registry (code, name, 5-char code), relative to BASE_URL.
STATIONS_FILE = "wykaz_stacji.csv"

#: Source files are Windows-1250 encoded. We decode once at the parser boundary;
#: everything downstream of the parser is UTF-8 / native Python str.
SOURCE_ENCODING = "cp1250"

#: Status codes used in IMGW measurement columns.
STATUS_NO_MEASUREMENT = "8"  # brak pomiaru
STATUS_NO_PHENOMENON = "9"  # brak zjawiska


class Frequency(StrEnum):
    """Temporal resolution of the data."""

    DAILY = "dobowe"
    MONTHLY = "miesieczne"
    TERM = "terminowe"

    @classmethod
    def parse(cls, value: str | Frequency) -> Frequency:
        """Resolve a Frequency from an enum, a Polish dir name, or an English alias."""
        if isinstance(value, cls):
            return value
        try:
            return _FREQUENCY_ALIASES[value.lower()]
        except KeyError:
            raise ValueError(f"unknown frequency {value!r}; expected one of {sorted(_FREQUENCY_ALIASES)}") from None


class StationType(StrEnum):
    """Type of meteorological station."""

    SYNOP = "synop"
    KLIMAT = "klimat"
    OPAD = "opad"

    @classmethod
    def parse(cls, value: str | StationType) -> StationType:
        """Resolve a StationType from an enum or its name (case-insensitive)."""
        if isinstance(value, cls):
            return value
        try:
            return cls(value.lower())
        except ValueError:
            raise ValueError(f"unknown station type {value!r}; expected one of {[t.value for t in cls]}") from None


#: Accepted string aliases for Frequency (Polish directory names + English).
_FREQUENCY_ALIASES: dict[str, Frequency] = {
    "daily": Frequency.DAILY,
    "dobowe": Frequency.DAILY,
    "monthly": Frequency.MONTHLY,
    "miesieczne": Frequency.MONTHLY,
    "term": Frequency.TERM,
    "terminowe": Frequency.TERM,
}


#: Short code embedded in file/member names per station type.
STATION_TYPE_CODE: dict[StationType, str] = {
    StationType.SYNOP: "s",
    StationType.KLIMAT: "k",
    StationType.OPAD: "o",
}

#: Short code embedded in file/member names per frequency.
FREQUENCY_CODE: dict[Frequency, str] = {
    Frequency.DAILY: "d",
    Frequency.MONTHLY: "m",
    Frequency.TERM: "t",
}

#: The year from which per-month, all-station grouping begins for non-synop
#: daily/term data. (Pre-2001 is grouped into 5-year folders.)
MULTI_STATION_START_YEAR = 2001
