# imgw-meteo

Download, **standardize** and query IMGW (Poland) meteorological measurement
data — with a Python API and a `imgw-meteo` CLI. PyTorch dataloaders are on the
roadmap.

Data source: <https://dane.imgw.pl/data/dane_pomiarowo_obserwacyjne/dane_meteorologiczne/>

> Scope: this package covers the **meteorological** (`dane_meteorologiczne`)
> dataset only, not hydrological data.

## Why standardize?

The raw IMGW files drift year to year, which breaks naive pipelines:

- source files are **Windows-1250** encoded (decoded once internally; everything
  you touch is UTF-8);
- decimals appear as `-.4` / `.0` in some years and `-0.4` / `0.0` in others;
- empty cells are sometimes quoted (`""`), sometimes not;
- status codes `8` (no measurement) and `9` (no phenomenon) leak in as real
  values unless converted to missing;
- the synoptic term set (`s_d_t`) exists in older per-station archives but **not**
  in the current-year per-month archive;
- station names are space-padded to fixed width in some station types.

`imgw-meteo` resolves all of this into a tidy table with **stable, declared
dtypes** (taken from a frozen canonical schema, never inferred) and proper
missing values.

## Install

```bash
pip install imgw-meteo          # API only
pip install imgw-meteo[cli]     # + the `imgw-meteo` command
pip install imgw-meteo[torch]   # + PyTorch (dataloaders, roadmap)
pip install imgw-meteo[all]
```

## Python API

```python
from imgw_meteo import IMGWClient

# One configured client (cache + network + standardization policy)...
client = IMGWClient(cache_dir="~/.cache/imgw-meteo", status_to_nan=True)

# ...produces lightweight, reusable selection handles.
synop = client.select(
    frequency="daily",  # "daily" | "monthly" | "term"
    station_type="synop",  # "synop" | "klimat" | "opad"
    years=range(2016, 2027),
    stations=["100"],  # optional
)

df = synop.get_dataframe()  # standardized pandas DataFrame
synop.export("synop.parquet")

# station registry (diacritic-insensitive search)
for s in client.stations().search("warszawa"):
    print(s)
```

## CLI

```bash
imgw-meteo stations --name "Kołobrzeg"
imgw-meteo years --freq daily --type synop
imgw-meteo fetch --freq daily --type klimat --year 2025 --month 6
imgw-meteo fetch --freq daily --type synop --year 2016 --station 100 --output out.parquet
```

## Standardization options (`IMGWClient(...)`)

| option | default | meaning |
|---|---|---|
| `status_to_nan` | `True` | status `8`/`9` and empty cells → missing |
| `keep_status` | `False` | keep raw status columns as `<CODE>_status` |
| `include_term` | `False` | surface synop term (`s_d_t`) columns |
| `add_datetime` | `True` | build a `datetime` column from `ROK/MC/DZ` |
| `strip_strings` | `True` | trim padded/quoted station names |
| `normalize_decimals` | `True` | fix `-.4` → `-0.4`, `.0` → `0.0` |
| `english_aliases` | `False` | add English column aliases |
| `schema_version` | `"1.0"` | pin the frozen canonical schema |

Network/cache: `cache_dir`, `offline`, `refresh` (`never` / `if-stale` /
`always`), `timeout`.

## Status

First iteration — working end-to-end for **daily** `synop` and `klimat`.
Roadmap: `opad`, `terminowe`, monthly, the synop term schema, and
`get_dataloaders(...)` (PyTorch-first).

## License

MIT
