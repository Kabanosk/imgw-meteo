# imgw-meteo

Download, **standardize** and query IMGW (Poland) meteorological measurement
data — with a clean Python API, a `imgw-meteo` CLI, and PyTorch dataloaders for
machine learning.

Data source: <https://dane.imgw.pl/data/dane_pomiarowo_obserwacyjne/dane_meteorologiczne/>

```{note}
This package covers the **meteorological** (`dane_meteorologiczne`) dataset
only — not hydrological data.
```

## Why it exists

IMGW publishes decades of weather observations as zipped CSVs, but the raw files
are painful to work with and their formatting drifts from year to year:

- files are **Windows-1250** encoded (you only ever see clean UTF-8);
- numbers appear as `-.4` / `.0` in some years and `-0.4` / `0.0` in others;
- empty cells are sometimes quoted (`""`), sometimes not;
- "no measurement" (`8`) and "no phenomenon" (`9`) markers leak in as if they
  were real readings;
- the same logical dataset is split across different file layouts by era;
- station names carry fixed-width padding.

`imgw-meteo` turns all of that into one tidy table with **stable, declared
dtypes** and proper missing values — the same columns and types regardless of
year — then hands it to you as a pandas DataFrame or ready-to-train PyTorch
dataloaders.

## Install

```bash
pip install imgw-meteo          # API only
pip install imgw-meteo[cli]     # + the `imgw-meteo` command
pip install imgw-meteo[torch]   # + PyTorch dataloaders
pip install imgw-meteo[all]     # everything
```

## 30-second example

```python
from imgw_meteo import IMGWClient

client = IMGWClient()
df = (
    client.select(frequency="daily", station_type="synop", years=2025, months=6)
    .get_dataframe()
)
print(df[["datetime", "POST", "TMAX", "TMIN", "SMDB"]].head())
```

```{toctree}
:maxdepth: 2
:caption: Contents

quickstart
guide/index
examples/index
api/index
```
