"""Frozen, versioned canonical schemas per (frequency, station_type).

Dtypes come from here, never from inference, because the source files drift
between years (``-.4`` vs ``-0.4``, quoted vs unquoted empties, etc.). The
standardizer coerces every file to these declarations.

This first iteration covers daily (dobowe) synop and klimat. More schemas
(opad, terminowe, monthly, and the synop term ``s_d_t`` set) will be added
incrementally.
"""

from .constants import Frequency, StationType
from .models import ColumnSpec

SCHEMA_VERSION = "1.0"

# --- shared key columns ------------------------------------------------------
_KEYS = [
    ColumnSpec("NSP", "string", "Kod stacji", "Station code", english_alias="station_code"),
    ColumnSpec("POST", "string", "Nazwa stacji", "Station name", english_alias="station_name"),
    ColumnSpec("ROK", "Int16", "Rok", "Year", english_alias="year"),
    ColumnSpec("MC", "Int8", "Miesiąc", "Month", english_alias="month"),
    ColumnSpec("DZ", "Int8", "Dzień", "Day", english_alias="day"),
]


def _m(code: str, pl: str, en: str, unit: str, status: str) -> list[ColumnSpec]:
    """A measurement column plus its paired status column."""
    return [
        ColumnSpec(code, "float32", pl, en, unit=unit, status_col=status),
        ColumnSpec(status, "string", f"Status pomiaru {code}", f"{code} status", is_status=True),
    ]


# --- klimat daily (k_d, 18 cols) --------------------------------------------
_KLIMAT_DAILY: list[ColumnSpec] = [
    *_KEYS,
    *_m("TMAX", "Maksymalna dobowa temperatura powietrza", "Max daily air temp", "°C", "WTMAX"),
    *_m("TMIN", "Minimalna dobowa temperatura powietrza", "Min daily air temp", "°C", "WTMIN"),
    *_m("STD", "Średnia dobowa temperatura powietrza", "Mean daily air temp", "°C", "WSTD"),
    *_m("TMNG", "Min. temperatura przy gruncie", "Min ground-level temp", "°C", "WTMNG"),
    *_m("SMDB", "Suma dobowa opadów", "Daily precipitation sum", "mm", "WSMDB"),
    ColumnSpec(
        "ROOP",
        "category",
        "Rodzaj opadu",
        "Precipitation type",
        unit="S/W/ ",
        english_alias="precip_type",
    ),
    *_m("PKSN", "Wysokość pokrywy śnieżnej", "Snow cover height", "cm", "WPKSN"),
]

# --- synop daily (s_d, 65 cols) ---------------------------------------------
_SYNOP_DAILY: list[ColumnSpec] = [
    *_KEYS,
    *_m("TMAX", "Maksymalna dobowa temperatura powietrza", "Max daily air temp", "°C", "WTMAX"),
    *_m("TMIN", "Minimalna dobowa temperatura powietrza", "Min daily air temp", "°C", "WTMIN"),
    *_m("STD", "Średnia dobowa temperatura powietrza", "Mean daily air temp", "°C", "WSTD"),
    *_m("TMNG", "Min. temperatura przy gruncie", "Min ground-level temp", "°C", "WTMNG"),
    *_m("SMDB", "Suma dobowa opadu", "Daily precipitation sum", "mm", "WSMDB"),
    ColumnSpec(
        "ROOP",
        "category",
        "Rodzaj opadu",
        "Precipitation type",
        unit="S/W/ ",
        english_alias="precip_type",
    ),
    *_m("PKSN", "Wysokość pokrywy śnieżnej", "Snow cover height", "cm", "WPKSN"),
    *_m("RWSN", "Równoważnik wodny śniegu", "Snow water equivalent", "mm/cm", "WRWSN"),
    *_m("USL", "Usłonecznienie", "Sunshine duration", "h", "WUSL"),
    *_m("DESZ", "Czas trwania opadu deszczu", "Rain duration", "h", "WDESZ"),
    *_m("SNEG", "Czas trwania opadu śniegu", "Snowfall duration", "h", "WSNEG"),
    *_m("DISN", "Czas trwania deszczu ze śniegiem", "Sleet duration", "h", "WDISN"),
    *_m("GRAD", "Czas trwania gradu", "Hail duration", "h", "WGRAD"),
    *_m("MGLA", "Czas trwania mgły", "Fog duration", "h", "WMGLA"),
    *_m("ZMGL", "Czas trwania zamglenia", "Mist duration", "h", "WZMGL"),
    *_m("SADZ", "Czas trwania sadzi", "Rime duration", "h", "WSADZ"),
    *_m("GOLO", "Czas trwania gołoledzi", "Glaze duration", "h", "WGOLO"),
    *_m("ZMNI", "Czas trwania zamieci niskiej", "Low blowing snow duration", "h", "WZMNI"),
    *_m("ZMWS", "Czas trwania zamieci wysokiej", "High blowing snow duration", "h", "WZMWS"),
    *_m("ZMET", "Czas trwania zmętnienia", "Haze duration", "h", "WZMET"),
    *_m("FF10", "Czas trwania wiatru >=10m/s", "Wind >=10m/s duration", "h", "WFF10"),
    *_m("FF15", "Czas trwania wiatru >15m/s", "Wind >15m/s duration", "h", "WFF15"),
    *_m("BRZA", "Czas trwania burzy", "Thunderstorm duration", "h", "WBRZA"),
    *_m("ROSA", "Czas trwania rosy", "Dew duration", "h", "WROSA"),
    *_m("SZRO", "Czas trwania szronu", "Hoarfrost duration", "h", "WSZRO"),
    *_m("DZPS", "Wystąpienie pokrywy śnieżnej", "Snow cover occurrence", "0/1", "WDZPS"),
    *_m("DZBL", "Wystąpienie błyskawicy", "Lightning occurrence", "0/1", "WDZBL"),
    ColumnSpec("SGR", "category", "Stan gruntu", "Ground state", unit="Z/R", english_alias="ground_state"),
    *_m("IZD", "Izoterma dolna", "Lower isotherm", "cm", "WIZD"),
    *_m("IZG", "Izoterma górna", "Upper isotherm", "cm", "WIZG"),
    *_m("AKTN", "Aktynometria", "Actinometry", "J/cm2", "WAKTN"),
]


_SCHEMAS: dict[tuple[Frequency, StationType], list[ColumnSpec]] = {
    (Frequency.DAILY, StationType.KLIMAT): _KLIMAT_DAILY,
    (Frequency.DAILY, StationType.SYNOP): _SYNOP_DAILY,
}


def get_schema(frequency: Frequency, station_type: StationType) -> list[ColumnSpec]:
    """Return the canonical column specs for a (frequency, station_type)."""
    try:
        return _SCHEMAS[(frequency, station_type)]
    except KeyError as exc:
        raise KeyError(
            f"No canonical schema yet for {frequency.value}/{station_type.value}. "
            f"Available: {[f'{f.value}/{s.value}' for f, s in _SCHEMAS]}"
        ) from exc


def column_names(frequency: Frequency, station_type: StationType) -> list[str]:
    return [c.code for c in get_schema(frequency, station_type)]
