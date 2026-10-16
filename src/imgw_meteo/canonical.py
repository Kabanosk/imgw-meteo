"""Frozen, versioned canonical schemas, keyed by IMGW *member* code.

A single ``(frequency, station_type)`` can map to more than one CSV member and
therefore more than one schema. For example a 2016 synop-daily archive contains
both ``s_d_100_2016.csv`` (code ``s_d``) and ``s_d_t_100_2016.csv`` (code
``s_d_t``); monthly archives contain ``*_m_d`` and ``*_m_t`` members. So schemas
are keyed by the member code (``s_d``, ``s_d_t``, ``o_d``, ``s_m_d`` ...), and a
member filename is mapped to its code with :func:`member_schema_code`.

Dtypes come from here, never from inference, because the source files drift
between years (``-.4`` vs ``-0.4``, quoted vs unquoted empties, etc.). The
standardizer coerces every file to these declarations.
"""

from .constants import FREQUENCY_CODE, STATION_TYPE_CODE, Frequency, StationType
from .models import ColumnSpec

SCHEMA_VERSION = "1.0"


# --- shared key-column groups -----------------------------------------------
def _keys(*, day: bool, hour: bool = False) -> list[ColumnSpec]:
    """Identity columns. ``day`` adds DZ (daily/term), ``hour`` adds GG (term)."""
    cols = [
        ColumnSpec("NSP", "string", "Kod stacji", "Station code", english_alias="station_code"),
        ColumnSpec("POST", "string", "Nazwa stacji", "Station name", english_alias="station_name"),
        ColumnSpec("ROK", "Int16", "Rok", "Year", english_alias="year"),
        ColumnSpec("MC", "Int8", "Miesiąc", "Month", english_alias="month"),
    ]
    if day:
        cols.append(ColumnSpec("DZ", "Int8", "Dzień", "Day", english_alias="day"))
    if hour:
        cols.append(ColumnSpec("GG", "Int8", "Godzina", "Hour", english_alias="hour"))
    return cols


def _m(code: str, pl: str, en: str, unit: str, status: str, dtype: str = "float32") -> list[ColumnSpec]:
    """A measurement column plus its paired status column."""
    return [
        ColumnSpec(code, dtype, pl, en, unit=unit, status_col=status),
        ColumnSpec(status, "string", f"Status pomiaru {code}", f"{code} status", is_status=True),
    ]


def _num(code: str, pl: str, en: str, unit: str = "") -> ColumnSpec:
    """A standalone numeric column with no paired status (e.g. day-counts)."""
    return ColumnSpec(code, "float32", pl, en, unit=unit)


def _cat(code: str, pl: str, en: str, unit: str = "", alias: str | None = None) -> ColumnSpec:
    return ColumnSpec(code, "category", pl, en, unit=unit, english_alias=alias)


def _str(code: str, pl: str, en: str) -> ColumnSpec:
    return ColumnSpec(code, "string", pl, en)


# ---------------------------------------------------------------------------
# DAILY (dobowe)
# ---------------------------------------------------------------------------

# klimat daily — k_d (18 cols)
_K_D: list[ColumnSpec] = [
    *_keys(day=True),
    *_m("TMAX", "Maksymalna dobowa temperatura", "Max daily air temp", "°C", "WTMAX"),
    *_m("TMIN", "Minimalna dobowa temperatura", "Min daily air temp", "°C", "WTMIN"),
    *_m("STD", "Średnia dobowa temperatura", "Mean daily air temp", "°C", "WSTD"),
    *_m("TMNG", "Min. temperatura przy gruncie", "Min ground-level temp", "°C", "WTMNG"),
    *_m("SMDB", "Suma dobowa opadów", "Daily precipitation sum", "mm", "WSMDB"),
    _cat("ROOP", "Rodzaj opadu", "Precipitation type", "S/W/ ", "precip_type"),
    *_m("PKSN", "Wysokość pokrywy śnieżnej", "Snow cover height", "cm", "WPKSN"),
]

# klimat daily term — k_d_t (13 cols)
_K_D_T: list[ColumnSpec] = [
    *_keys(day=True),
    *_m("TEMP", "Średnia dobowa temperatura", "Mean daily air temp", "°C", "WTEMP"),
    *_m("WLGS", "Średnia dobowa wilgotność względna", "Mean daily rel. humidity", "%", "WWLGS"),
    *_m("FWS", "Średnia dobowa prędkość wiatru", "Mean daily wind speed", "m/s", "WFWS"),
    *_m("NOS", "Średnie dobowe zachmurzenie", "Mean daily cloud cover", "oktanty", "WNOS"),
]

# opad daily — o_d (16 cols)
_O_D: list[ColumnSpec] = [
    *_keys(day=True),
    *_m("SMDB", "Suma dobowa opadów", "Daily precipitation sum", "mm", "WSMDB"),
    _cat("ROOP", "Rodzaj opadu", "Precipitation type", "S/W/ ", "precip_type"),
    *_m("PKSN", "Wysokość pokrywy śnieżnej", "Snow cover height", "cm", "WPKSN"),
    *_m("HSS", "Wysokość świeżo spadłego śniegu", "Fresh snow height", "cm", "WHSS"),
    *_m("GATS", "Gatunek śniegu", "Snow type", "kod", "WGATS", dtype="string"),
    *_m("RPSN", "Rodzaj pokrywy śnieżnej", "Snow cover type", "kod", "WRPSN", dtype="string"),
]

# synop daily — s_d (65 cols)
_S_D: list[ColumnSpec] = [
    *_keys(day=True),
    *_m("TMAX", "Maksymalna dobowa temperatura", "Max daily air temp", "°C", "WTMAX"),
    *_m("TMIN", "Minimalna dobowa temperatura", "Min daily air temp", "°C", "WTMIN"),
    *_m("STD", "Średnia dobowa temperatura", "Mean daily air temp", "°C", "WSTD"),
    *_m("TMNG", "Min. temperatura przy gruncie", "Min ground-level temp", "°C", "WTMNG"),
    *_m("SMDB", "Suma dobowa opadu", "Daily precipitation sum", "mm", "WSMDB"),
    _cat("ROOP", "Rodzaj opadu", "Precipitation type", "S/W/ ", "precip_type"),
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
    _cat("SGR", "Stan gruntu", "Ground state", "Z/R", "ground_state"),
    *_m("IZD", "Izoterma dolna", "Lower isotherm", "cm", "WIZD"),
    *_m("IZG", "Izoterma górna", "Upper isotherm", "cm", "WIZG"),
    *_m("AKTN", "Aktynometria", "Actinometry", "J/cm2", "WAKTN"),
]

# synop daily term — s_d_t (23 cols)
_S_D_T: list[ColumnSpec] = [
    *_keys(day=True),
    *_m("NOS", "Średnie dobowe zachmurzenie", "Mean daily cloud cover", "oktanty", "WNOS"),
    *_m("FWS", "Średnia dobowa prędkość wiatru", "Mean daily wind speed", "m/s", "WFWS"),
    *_m("TEMP", "Średnia dobowa temperatura", "Mean daily air temp", "°C", "WTEMP"),
    *_m("CPW", "Średnie dobowe ciśnienie pary wodnej", "Mean daily vapour pressure", "hPa", "WCPW"),
    *_m("WLGS", "Średnia dobowa wilgotność względna", "Mean daily rel. humidity", "%", "WWLGS"),
    *_m("PPPS", "Średnie dobowe ciśnienie na st.", "Mean daily station pressure", "hPa", "WPPPS"),
    *_m("PPPM", "Średnie dobowe ciśnienie na morzu", "Mean daily sea-level pressure", "hPa", "WPPPM"),
    *_m("WODZ", "Suma opadu dzień", "Daytime precip sum", "mm", "WWODZ"),
    *_m("WONO", "Suma opadu noc", "Nighttime precip sum", "mm", "WWONO"),
]

# ---------------------------------------------------------------------------
# TERM (terminowe) — adds the GG hour column. (No opad term exists.)
# ---------------------------------------------------------------------------

# klimat term — k_t (22 cols)
_K_T: list[ColumnSpec] = [
    *_keys(day=True, hour=True),
    *_m("TEMP", "Temperatura powietrza", "Air temperature", "°C", "WTEMP"),
    *_m("TTZW", "Temperatura termometru zwilżonego", "Wet-bulb temperature", "°C", "WTTZW"),
    _cat("TWLW", "Wskaźnik lodu", "Ice indicator", "L/W"),
    _cat("WENT", "Wskaźnik wentylacji", "Ventilation indicator", "W/N"),
    *_m("WLGW", "Wilgotność względna", "Relative humidity", "%", "WWLGW"),
    *_m("DKDK", "Kod kierunku wiatru", "Wind direction code", "kod", "WDKDK", dtype="string"),
    *_m("FWR", "Prędkość wiatru", "Wind speed", "m/s", "WFWR"),
    *_m("ZOGK", "Zachmurzenie ogólne", "Total cloud cover", "oktanty", "WZOGK"),
    *_m("WID", "Widzialność", "Visibility", "kod", "WWID", dtype="string"),
]

# synop term — s_t (~113 cols). Many coded/text fields kept as string.
_S_T: list[ColumnSpec] = [
    *_keys(day=True, hour=True),
    *_m("HPOD", "Wysokość podstawy chmur CL CM", "Cloud base height (coded)", "kod", "WHPOD", dtype="string"),
    *_m("HPON", "Wysokość podstawy niższej", "Lower cloud base", "m", "WHPON"),
    *_m("HPOW", "Wysokość podstawy wyższej", "Upper cloud base", "m", "WHPOW"),
    _str("HTXT", "Wysokość podstawy tekstowy", "Cloud base (text)"),
    _str("POM1", "Pomiar przyrządem 1", "Instrument 1 reading"),
    _str("POM2", "Pomiar przyrządem 2", "Instrument 2 reading"),
    *_m("WID", "Widzialność", "Visibility", "kod", "WWID", dtype="string"),
    *_m("WIDO", "Widzialność operatora", "Operator visibility", "m", "WWIDO"),
    *_m("WIDA", "Widzialność automat", "Automatic visibility", "m", "WWIDA"),
    *_m("NOG", "Zachmurzenie ogólne", "Total cloud cover", "oktanty", "WNOG"),
    *_m("KRWR", "Kierunek wiatru", "Wind direction", "°", "WKRWR"),
    *_m("FWR", "Prędkość wiatru", "Wind speed", "m/s", "WFWR"),
    *_m("PORW", "Poryw wiatru", "Wind gust", "m/s", "WPORW"),
    *_m("TEMP", "Temperatura powietrza", "Air temperature", "°C", "WTEMP"),
    *_m("TTZW", "Temperatura termometru zwilżonego", "Wet-bulb temperature", "°C", "WTTZW"),
    _cat("WENT", "Wskaźnik wentylacji", "Ventilation indicator", "W/N"),
    _cat("TWLW", "Wskaźnik lodu", "Ice indicator", "L/W"),
    *_m("CPW", "Ciśnienie pary wodnej", "Vapour pressure", "hPa", "WCPW"),
    *_m("WLGW", "Wilgotność względna", "Relative humidity", "%", "WWLGW"),
    *_m("TPTR", "Temperatura punktu rosy", "Dew point temperature", "°C", "WTPTR"),
    *_m("PPPS", "Ciśnienie na poziomie stacji", "Station-level pressure", "hPa", "WPPPS"),
    *_m("PPPM", "Ciśnienie na poziomie morza", "Sea-level pressure", "hPa", "WPPPM"),
    _str("TECH", "Charakterystyka tendencji ciśnienia", "Pressure tendency char. (coded)"),
    *_m("APP", "Wartość tendencji ciśnienia", "Pressure tendency value", "", "WAPP"),
    *_m("WO6G", "Opad za 6 godzin", "6-hour precipitation", "mm", "WWO6G"),
    *_m("ROPT", "Rodzaj opadu za 6 godzin", "6-hour precip type", "kod", "WROPT", dtype="string"),
    _str("POGB", "Pogoda bieżąca", "Present weather (coded)"),
    _str("POGU", "Pogoda ubiegła", "Past weather (coded)"),
    *_m("CLCM", "Zachmurzenie niskie", "Low cloud cover", "oktanty", "WCLCM"),
    *_m("CHCL", "Chmury CL", "CL clouds (coded)", "kod", "WCHCL", dtype="string"),
    _str("CHLT", "Chmury CL tekstem", "CL clouds (text)"),
    *_m("CHCM", "Chmury CM", "CM clouds (coded)", "kod", "WCHCM", dtype="string"),
    _str("CHMT", "Chmury CM tekstem", "CM clouds (text)"),
    *_m("CHCH", "Chmury CH", "CH clouds (coded)", "kod", "WCHCH", dtype="string"),
    _str("CHHT", "Chmury CH tekstem", "CH clouds (text)"),
    *_m("SGRN", "Stan gruntu", "Ground state (coded)", "kod", "WSGRN", dtype="string"),
    *_m("DEFI", "Deficyt wilgotności", "Humidity deficit", "hPa", "WDEFI"),
    *_m("USLN", "Usłonecznienie", "Sunshine duration", "h", "WUSLN"),
    *_m("ROSW", "Rozmyta rosa/woda", "Dew/water", "", "WROSW"),
    *_m("PORK", "Poryw maksymalny", "Max gust", "m/s", "WPORK"),
    _str("GODP", "Godzina porywu", "Gust hour"),
    _str("MINP", "Minuta porywu", "Gust minute"),
    *_m("TG05", "Temperatura gruntu 5cm", "Ground temp 5cm", "°C", "WTG05"),
    *_m("TG10", "Temperatura gruntu 10cm", "Ground temp 10cm", "°C", "WTG10"),
    *_m("TG20", "Temperatura gruntu 20cm", "Ground temp 20cm", "°C", "WTG20"),
    *_m("TG50", "Temperatura gruntu 50cm", "Ground temp 50cm", "°C", "WTG50"),
    *_m("TG100", "Temperatura gruntu 100cm", "Ground temp 100cm", "°C", "WTG100"),
    *_m("TMIN", "Temperatura minimalna", "Minimum temperature", "°C", "WTMIN"),
    *_m("TMAX", "Temperatura maksymalna", "Maximum temperature", "°C", "WTMAX"),
    *_m("TGMI", "Minimalna temp. przy gruncie", "Min ground-level temp", "°C", "WTGMI"),
    *_m("RWSN", "Równoważnik wodny śniegu", "Snow water equivalent", "mm/cm", "WRWSN"),
    *_m("PKSN", "Wysokość pokrywy śnieżnej", "Snow cover height", "cm", "WPKSN"),
    *_m("HSS", "Wysokość świeżo spadłego śniegu", "Fresh snow height", "cm", "WHSS"),
    *_m("GRSN", "Grubość świeżego śniegu", "Fresh snow depth", "cm", "WGRSN"),
    _str("GATS", "Gatunek śniegu", "Snow type (coded)"),
    _str("UKPO", "Układ pokrywy", "Snow cover layout"),
    *_m("HPRO", "Wysokość progu", "Threshold height", "", "WHPRO"),
    *_m("CIPR", "Ciśnienie progu", "Threshold pressure", "", "WCIPR"),
]

# ---------------------------------------------------------------------------
# MONTHLY (miesieczne) — no DZ. Zip is YYYY_m_<type>.zip.
# ---------------------------------------------------------------------------

# opad monthly — o_m (14 cols). DN1/DN2 and some counts are status-less.
_O_M: list[ColumnSpec] = [
    *_keys(day=False),
    *_m("SUMM", "Miesięczna suma opadów", "Monthly precipitation sum", "mm", "WSUMM"),
    *_m("LDS", "Liczba dni z opadem śniegu", "Days with snowfall", "dni", "WLDS"),
    *_m("MAXO", "Opad maksymalny", "Max precipitation", "mm", "WMAXO"),
    _num("DN1", "Dzień pierwszy opadu maks.", "First day of max precip"),
    _num("DN2", "Dzień ostatni opadu maks.", "Last day of max precip"),
    *_m("LDPS", "Liczba dni z pokrywą śnieżną", "Days with snow cover", "dni", "WLDPS"),
]

# klimat monthly aggregate — k_m_d (27 cols; trailing counts status-less)
_K_M_D: list[ColumnSpec] = [
    *_keys(day=False),
    *_m("TMAX", "Absolutna maks. temperatura", "Absolute max temp", "°C", "WTMAX"),
    *_m("TMXS", "Średnia maks. temperatura", "Mean max temp", "°C", "WTMXS"),
    *_m("TMIN", "Absolutna min. temperatura", "Absolute min temp", "°C", "WTMIN"),
    *_m("TMNS", "Średnia min. temperatura", "Mean min temp", "°C", "WWTMNS"),
    *_m("STM", "Średnia miesięczna temperatura", "Mean monthly temp", "°C", "WSTM"),
    *_m("TMNG", "Min. temperatura przy gruncie", "Min ground-level temp", "°C", "WTMNG"),
    *_m("SUMM", "Miesięczna suma opadów", "Monthly precip sum", "mm", "WSUMM"),
    *_m("OPMX", "Maks. dobowa suma opadów", "Max daily precip in month", "mm", "WOPMX"),
    _num("DN1", "Pierwszy dzień opadu maks.", "First day of max precip"),
    _num("DN2", "Ostatni dzień opadu maks.", "Last day of max precip"),
    *_m("PKSN", "Maks. wysokość pokrywy śnieżnej", "Max snow cover height", "cm", "WPKSN"),
    _num("PSDN", "Liczba dni z pokrywą śnieżną", "Days with snow cover", "dni"),
    _num("DESD", "Liczba dni z opadem deszczu", "Days with rain", "dni"),
    _num("SNID", "Liczba dni z opadem śniegu", "Days with snow", "dni"),
]

# klimat monthly term-means — k_m_t (12 cols)
_K_M_T: list[ColumnSpec] = [
    *_keys(day=False),
    *_m("TEMP", "Średnia miesięczna temperatura", "Mean monthly temp", "°C", "WTEMP"),
    *_m("WLGS", "Średnia miesięczna wilgotność", "Mean monthly humidity", "%", "WWLGS"),
    *_m("FWS", "Średnia miesięczna prędkość wiatru", "Mean monthly wind speed", "m/s", "WFWS"),
    *_m("NOS", "Średnie miesięczne zachmurzenie", "Mean monthly cloud cover", "oktanty", "WNOS"),
]

# synop monthly aggregate — s_m_d (60 cols)
_S_M_D: list[ColumnSpec] = [
    *_keys(day=False),
    *_m("TMAX", "Absolutna maks. temperatura", "Absolute max temp", "°C", "WTMAX"),
    *_m("TMXS", "Średnia maks. temperatura", "Mean max temp", "°C", "WTMXS"),
    *_m("TMIN", "Absolutna min. temperatura", "Absolute min temp", "°C", "WTMIN"),
    *_m("TMNS", "Średnia min. temperatura", "Mean min temp", "°C", "WTMNS"),
    *_m("STM", "Średnia miesięczna temperatura", "Mean monthly temp", "°C", "WSTM"),
    *_m("TMNG", "Min. temperatura przy gruncie", "Min ground-level temp", "°C", "WTMNG"),
    *_m("SUMM", "Miesięczna suma opadów", "Monthly precip sum", "mm", "WSUMM"),
    *_m("OPMX", "Maks. dobowa suma opadów", "Max daily precip in month", "mm", "WOPMX"),
    _num("DN1", "Pierwszy dzień opadu maks.", "First day of max precip"),
    _num("DN2", "Ostatni dzień opadu maks.", "Last day of max precip"),
    *_m("SUUS", "Miesięczna suma usłonecznienia", "Monthly sunshine sum", "h", "WSUUS"),
    *_m("PKSN", "Maks. wysokość pokrywy śnieżnej", "Max snow cover height", "cm", "WPKSN"),
    *_m("PSDN", "Liczba dni z pokrywą śnieżną", "Days with snow cover", "dni", "WPSDN"),
    *_m("DESD", "Liczba dni z deszczem", "Days with rain", "dni", "WDESD"),
    *_m("SNID", "Liczba dni ze śniegiem", "Days with snow", "dni", "WSNID"),
    *_m("DSND", "Liczba dni z deszczem ze śniegiem", "Days with sleet", "dni", "WDSND"),
    *_m("GRDD", "Liczba dni z gradem", "Days with hail", "dni", "WGRDD"),
    *_m("MGLD", "Liczba dni z mgłą", "Days with fog", "dni", "WMGLD"),
    *_m("ZAMD", "Liczba dni z zamgleniem", "Days with mist", "dni", "WZAMD"),
    *_m("SADD", "Liczba dni z sadzią", "Days with rime", "dni", "WSADD"),
    *_m("GOLD", "Liczba dni z gołoledzią", "Days with glaze", "dni", "WGOLD"),
    *_m("ZAND", "Liczba dni z zamiecią niską", "Days with low blowing snow", "dni", "WZAND"),
    *_m("ZAWD", "Liczba dni z zamiecią wysoką", "Days with high blowing snow", "dni", "WZAWD"),
    *_m("ZMED", "Liczba dni ze zmętnieniem", "Days with haze", "dni", "WZMED"),
    *_m("W10D", "Liczba dni z wiatrem >=10m/s", "Days wind >=10m/s", "dni", "WW10D"),
    *_m("W15D", "Liczba dni z wiatrem >15m/s", "Days wind >15m/s", "dni", "WW15D"),
    *_m("BURD", "Liczba dni z burzą", "Days with thunderstorm", "dni", "WBURD"),
    *_m("ROSD", "Liczba dni z rosą", "Days with dew", "dni", "WROSD"),
    *_m("SZRD", "Liczba dni ze szronem", "Days with hoarfrost", "dni", "WSZRD"),
]

# synop monthly term-means — s_m_t (22 cols)
_S_M_T: list[ColumnSpec] = [
    *_keys(day=False),
    *_m("NOS", "Średnie miesięczne zachmurzenie", "Mean monthly cloud cover", "oktanty", "WNOS"),
    *_m("FWS", "Średnia miesięczna prędkość wiatru", "Mean monthly wind speed", "m/s", "WFWS"),
    *_m("TEMP", "Średnia miesięczna temperatura", "Mean monthly temp", "°C", "WTEMP"),
    *_m("CPW", "Średnie miesięczne ciśnienie pary wodnej", "Mean monthly vapour pressure", "hPa", "WCPW"),
    *_m("WLGS", "Średnia miesięczna wilgotność", "Mean monthly humidity", "%", "WWLGS"),
    *_m("PPPS", "Średnie ciśnienie na st.", "Mean station pressure", "hPa", "WPPPS"),
    *_m("PPPM", "Średnie ciśnienie na morzu", "Mean sea-level pressure", "hPa", "WPPPM"),
    *_m("WODZ", "Suma opadu dzień", "Daytime precip sum", "mm", "WWODZ"),
    *_m("WONO", "Suma opadu noc", "Nighttime precip sum", "mm", "WWONO"),
]


#: Member code -> canonical schema.
_SCHEMAS: dict[str, list[ColumnSpec]] = {
    "k_d": _K_D,
    "k_d_t": _K_D_T,
    "o_d": _O_D,
    "s_d": _S_D,
    "s_d_t": _S_D_T,
    "k_t": _K_T,
    "s_t": _S_T,
    "o_m": _O_M,
    "k_m_d": _K_M_D,
    "k_m_t": _K_M_T,
    "s_m_d": _S_M_D,
    "s_m_t": _S_M_T,
}


def _code(frequency: Frequency, station_type: StationType) -> str:
    """Base ``<type><freq>`` code, e.g. ('daily','synop') -> 's_d'."""
    return f"{STATION_TYPE_CODE[station_type]}_{FREQUENCY_CODE[frequency]}"


#: Which member schema codes exist for each (frequency, station_type).
def schema_codes(frequency: Frequency, station_type: StationType) -> list[str]:
    """List the member schema codes for a selection (primary first).

    :raises KeyError: If the combination has no data on the IMGW server
        (e.g. term/opad does not exist).
    """
    base = _code(frequency, station_type)
    if frequency is Frequency.MONTHLY:
        if station_type is StationType.OPAD:
            codes = ["o_m"]  # opad monthly is a single schema (no d/t split)
        else:
            # synop/klimat monthly use dual aggregate/term members.
            codes = [f"{base}_d", f"{base}_t"]
    elif frequency is Frequency.DAILY and station_type is StationType.SYNOP:
        codes = ["s_d", "s_d_t"]
    elif frequency is Frequency.DAILY and station_type is StationType.KLIMAT:
        codes = ["k_d", "k_d_t"]
    else:
        codes = [base]
    present = [c for c in codes if c in _SCHEMAS]
    if not present:
        raise KeyError(f"No data available for {frequency.value}/{station_type.value} on the IMGW server.")
    return present


def primary_code(frequency: Frequency, station_type: StationType) -> str:
    """The main (non-term) member code for a selection."""
    return schema_codes(frequency, station_type)[0]


def is_term_code(code: str) -> bool:
    """True if a code is an optional *term add-on* member of a daily/monthly set.

    These are the extra sub-daily/term-means members bundled alongside a primary
    member, e.g. ``s_d_t`` (next to ``s_d``) or ``s_m_t`` (next to ``s_m_d``).
    They are gated behind ``include_term``.

    This is distinct from the *terminowe* primary datasets ``k_t`` / ``s_t``,
    which are the main data for that frequency and are always included — even
    though their code also ends in ``_t``.
    """
    return code.endswith("_t") and code not in ("k_t", "s_t")


def member_schema_code(member_filename: str) -> str:
    """Map a CSV member filename to its schema code.

    e.g. ``s_d_t_100_2016.csv`` -> ``s_d_t``; ``o_d_06_2025.csv`` -> ``o_d``;
    ``s_m_d_2015.csv`` -> ``s_m_d``.
    """
    name = member_filename.rsplit("/", 1)[-1]
    name = name[:-4] if name.lower().endswith(".csv") else name
    parts = name.split("_")
    # The schema code is the leading alphabetic tokens (single letters / 'd','t','m').
    code_tokens: list[str] = []
    for tok in parts:
        if tok.isalpha():
            code_tokens.append(tok)
        else:
            break
    code = "_".join(code_tokens)
    if code not in _SCHEMAS:
        raise KeyError(f"unrecognized member schema for {member_filename!r} (code {code!r})")
    return code


def get_schema_by_code(code: str) -> list[ColumnSpec]:
    """Return the canonical column specs for a member schema code."""
    try:
        return _SCHEMAS[code]
    except KeyError as exc:
        raise KeyError(f"No canonical schema for member code {code!r}. Available: {sorted(_SCHEMAS)}") from exc


def get_schema(frequency: Frequency, station_type: StationType) -> list[ColumnSpec]:
    """Return the canonical column specs for a selection's primary member."""
    return get_schema_by_code(primary_code(frequency, station_type))


def column_names(frequency: Frequency, station_type: StationType) -> list[str]:
    """Column names of the selection's primary member schema."""
    return [c.code for c in get_schema(frequency, station_type)]


def column_names_for_code(code: str) -> list[str]:
    return [c.code for c in get_schema_by_code(code)]
