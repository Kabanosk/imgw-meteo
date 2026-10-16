# Quickstart

Every snippet below is self-contained. Downloads are cached, so re-running is
fast and offline-friendly after the first call.

## 1. Create a client

```python
from imgw_meteo import IMGWClient

client = IMGWClient()  # uses ~/.cache/imgw-meteo for downloads
```

Need a custom cache location or offline mode? Pass config objects (see
{doc}`guide/configuration`):

```python
from imgw_meteo import IMGWClient, ClientConfig

client = IMGWClient(config=ClientConfig(cache_dir="./imgw_cache", timeout=60))
```

## 2. Find a station

```python
reg = client.stations()

# diacritic- and case-insensitive search
for s in reg.search("krakow"):
    print(s)                       # e.g. "KRAKÓW-BALICE (250190390)"

# or look one up by code
print(reg.by_code("250190390"))
```

## 3. Select and fetch data

`select(...)` only *describes* what you want; nothing is downloaded until you
call `get_dataframe()` or `export()`.

```python
synop = client.select(
    frequency="daily",      # "daily" | "monthly" | "term"
    station_type="synop",   # "synop" | "klimat" | "opad"
    years=2025,
    months=6,               # optional
)
df = synop.get_dataframe()
print(df.shape)
print(df.dtypes)            # stable, declared dtypes — not inferred
```

## 4. A whole decade, one station

```python
krakow = client.select(
    frequency="daily",
    station_type="synop",
    years=range(2015, 2026),
    stations=["250190390"],
)
df = krakow.get_dataframe()
print(df["datetime"].min(), "→", df["datetime"].max())
```

## 5. Export to a file

```python
# format chosen by extension: .parquet or .csv (UTF-8)
synop.export("synop_2025_06.parquet")
synop.export("synop_2025_06.csv")
```

## 6. Build PyTorch dataloaders

```python
train, val, test = (
    client.select(frequency="daily", station_type="synop", years=range(2015, 2026))
    .get_dataloaders(
        features=["TMAX", "TMIN", "STD"],
        targets=["TMAX"],
        input_window=30,   # 30 past days
        horizon=1,         # predict 1 day ahead
        batch_size=64,
    )
)

for x, y in train:          # x: (64, 30, 3)   y: (64, 1, 1)
    ...
    break
```

See {doc}`examples/index` for complete, copy-pasteable programs including a full
LSTM training loop.

## From the command line

```bash
imgw-meteo stations --name "Kraków"
imgw-meteo years --freq daily --type synop
imgw-meteo fetch --freq daily --type synop --year 2025 --month 6 --output out.parquet
```
