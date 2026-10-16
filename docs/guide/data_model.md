# Data model

IMGW organizes its meteorological data along three axes. `imgw-meteo` mirrors
them in `select(...)`.

## Frequency

| `frequency` | aliases | meaning |
|---|---|---|
| `"daily"` | `"dobowe"` | one row per station per day |
| `"monthly"` | `"miesieczne"` | one row per station per month |
| `"term"` | `"terminowe"` | sub-daily observations (adds an hour column) |

## Station type

| `station_type` | meaning |
|---|---|
| `"synop"` | synoptic stations — the richest set (60+ columns daily) |
| `"klimat"` | climatological stations |
| `"opad"` | precipitation-only stations |

## Which combinations exist

Not every pairing is published by IMGW. `select(...)` validates eagerly and
raises `SelectionError` for the one gap:

| | synop | klimat | opad |
|---|---|---|---|
| daily | ✅ | ✅ | ✅ |
| monthly | ✅ | ✅ | ✅ |
| term | ✅ | ✅ | ❌ (does not exist) |

```python
from imgw_meteo import IMGWClient
from imgw_meteo.exceptions import SelectionError

try:
    IMGWClient().select(frequency="term", station_type="opad", years=2024)
except SelectionError as e:
    print(e)   # clear message: term/opad is not published
```

## Dual schemas (term add-ons)

Some archives bundle a second member alongside the primary one:

- **daily synop** ships `s_d` (aggregates) **and** `s_d_t` (sub-daily means);
- **daily klimat** ships `k_d` and `k_d_t`;
- **monthly synop/klimat** ship `*_m_d` (aggregates) and `*_m_t` (term means).

By default only the primary member is returned. Set `include_term=True` to merge
the term member's columns onto the same rows (wider table, not more rows):

```python
from imgw_meteo import IMGWClient, StandardizationConfig

client = IMGWClient(standardization=StandardizationConfig(include_term=True))
df = client.select(frequency="daily", station_type="synop", years=2016, stations=["100"]).get_dataframe()
# now includes term columns like CPW (vapour pressure), PPPM (sea-level pressure), ...
```

## Columns

Every table starts with identity columns, then measurements. Each measurement
code (e.g. `TMAX`) has a paired status code (`WTMAX`) in the source; by default
status is consumed to produce missing values and dropped (see
{doc}`standardization`).

Identity columns:

| code | meaning | present when |
|---|---|---|
| `NSP` | station code | always |
| `POST` | station name | always |
| `ROK` / `MC` / `DZ` | year / month / day | `DZ` on daily & term |
| `GG` | hour | term only |
| `datetime` | assembled timestamp | when `add_datetime=True` (default) |

Column codes keep their original IMGW names (e.g. `TMAX`, `SMDB`); set
`english_aliases=True` to rename them to English (`year`, `station_code`, ...).
```
