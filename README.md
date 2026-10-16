# imgw-meteo

[![CI](https://github.com/Kabanosk/imgw-meteo/actions/workflows/ci.yml/badge.svg)](https://github.com/Kabanosk/imgw-meteo/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/imgw-meteo.svg)](https://pypi.org/project/imgw-meteo/)
[![Python](https://img.shields.io/pypi/pyversions/imgw-meteo.svg)](https://pypi.org/project/imgw-meteo/)
[![Docs](https://readthedocs.org/projects/imgw-meteo/badge/?version=latest)](https://imgw-meteo.readthedocs.io)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

Download, **standardize** and query IMGW (Poland) meteorological measurement
data — with a clean Python API, a `imgw-meteo` CLI, and PyTorch dataloaders for
machine learning.

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
- the same logical dataset is split across different file layouts by era;
- station names are space-padded to fixed width in some station types.

`imgw-meteo` resolves all of this into a tidy table with **stable, declared
dtypes** (from a frozen canonical schema, never inferred) and proper missing
values — then hands it to you as a pandas DataFrame or ready-to-train PyTorch
dataloaders.

## Install

```bash
pip install imgw-meteo          # API only
pip install imgw-meteo[cli]     # + the `imgw-meteo` command
pip install imgw-meteo[torch]   # + PyTorch dataloaders
pip install imgw-meteo[all]     # everything
```

## Quick start

```python
from imgw_meteo import IMGWClient

client = IMGWClient()

# describe a selection (nothing downloads until you ask for data)
df = (
    client.select(frequency="daily", station_type="synop", years=2025, months=6)
    .get_dataframe()
)
print(df[["datetime", "POST", "TMAX", "TMIN", "SMDB"]].head())

# find stations (diacritic-insensitive)
for s in client.stations().search("kraków"):
    print(s)
```

### PyTorch dataloaders

```python
train, val, test = (
    client.select(frequency="daily", station_type="synop", years=range(2015, 2026))
    .get_dataloaders(
        features=["TMAX", "TMIN", "STD"],
        targets=["TMAX"],
        input_window=30, horizon=1, batch_size=64,
    )
)
for x, y in train:        # x: (64, 30, 3)   y: (64, 1, 1)
    ...
    break
```

Chronological split (no leakage), train-only normalization, and per-station
windowing are the defaults. See the docs for a full LSTM training example.

## CLI

```bash
imgw-meteo stations --name "Kraków"
imgw-meteo years --freq daily --type synop
imgw-meteo fetch --freq daily --type synop --year 2025 --month 6 --output out.parquet
```

## Data coverage

| | synop | klimat | opad |
|---|---|---|---|
| daily | ✅ | ✅ | ✅ |
| monthly | ✅ | ✅ | ✅ |
| term | ✅ | ✅ | — (not published) |

## Documentation

Full guide, configuration reference, and examples:
<https://imgw-meteo.readthedocs.io>

## License

MIT
