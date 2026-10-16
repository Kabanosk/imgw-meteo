# Basic queries

## Daily synop for one month

```python
from imgw_meteo import IMGWClient

client = IMGWClient()
df = client.select(
    frequency="daily", station_type="synop", years=2025, months=6
).get_dataframe()
print(df[["datetime", "POST", "TMAX", "TMIN", "STD", "SMDB"]].head())
```

## A full year, all stations

```python
df = client.select(frequency="daily", station_type="klimat", years=2024).get_dataframe()
print(df.shape)
print(df["NSP"].nunique(), "stations")
```

## Several specific months

```python
summer = client.select(
    frequency="daily", station_type="synop", years=2025, months=[6, 7, 8]
).get_dataframe()
```

## One station across many years

```python
df = client.select(
    frequency="daily",
    station_type="synop",
    years=range(2010, 2026),
    stations=["250190390"],   # Kraków-Balice
).get_dataframe()
print(df["datetime"].min(), "→", df["datetime"].max())
```

## Monthly aggregates

```python
monthly = client.select(frequency="monthly", station_type="synop", years=2024).get_dataframe()
print(monthly[["datetime", "POST", "TMXS", "TMNS", "SUMM"]].head())
```

## Sub-daily (term) observations

```python
term = client.select(
    frequency="term", station_type="klimat", years=2024, months=1
).get_dataframe()
print(term[["datetime", "POST", "TEMP", "WLGW"]].head())  # note the hour in datetime
```

## Precipitation-only (opad) stations

```python
opad = client.select(
    frequency="daily", station_type="opad", years=2025, months=6
).get_dataframe()
print(opad[["datetime", "POST", "SMDB", "PKSN"]].head())
```

## Include the term add-on columns

```python
from imgw_meteo import StandardizationConfig

client = IMGWClient(standardization=StandardizationConfig(include_term=True))
df = client.select(
    frequency="daily", station_type="synop", years=2016, stations=["100"]
).get_dataframe()
# df now also has term columns such as CPW, PPPS, PPPM
```

## Export

```python
sel = client.select(frequency="daily", station_type="synop", years=2025, months=6)
sel.export("synop_2025_06.parquet")   # Parquet
sel.export("synop_2025_06.csv")       # CSV (UTF-8)
```
