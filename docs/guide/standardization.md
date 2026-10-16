# Standardization

This is the core value of the library: raw IMGW CSVs become one tidy, typed
table with the same columns and dtypes every year. Here is exactly what each
cleaning step does, with before/after examples.

## Missing values from status codes

The source stores a status next to each measurement: `8` = no measurement,
`9` = no phenomenon. Left alone, those leak in as the numbers 8 and 9.

```python
from imgw_meteo import IMGWClient, StandardizationConfig

# default: status_to_nan=True
df = IMGWClient().select(
    frequency="daily", station_type="klimat", years=2025, months=6
).get_dataframe()
print(df["TMNG"].isna().sum(), "missing ground-temp readings (status 8 → NaN)")

# keep the raw flags too, for auditing
cfg = StandardizationConfig(keep_status=True)
df2 = IMGWClient(standardization=cfg).select(
    frequency="daily", station_type="klimat", years=2025, months=6
).get_dataframe()
print(df2[["TMNG", "WTMNG_status"]].head())
```

## Decimal normalization

Older files write `-.4` and `.0`; newer ones write `-0.4` and `0.0`. Without
fixing this, a column's dtype flips between `float` and `object` across years.

```python
df = IMGWClient().select(
    frequency="daily", station_type="synop", years=2016, stations=["100"]
).get_dataframe()
print(df["TMAX"].dtype)        # float32 every year
print(float(df["TMAX"].iloc[0]))  # a source value of "-.4" reads as -0.4
```

## Declared dtypes (never inferred)

Dtypes come from a frozen canonical schema, so they are stable regardless of the
file's quirks that year.

```python
df = IMGWClient().select(
    frequency="daily", station_type="synop", years=2025, months=1
).get_dataframe()
print(df.dtypes.head(8))
# ROK: Int16, MC/DZ: Int8, TMAX/TMIN/...: float32, ROOP: category, ...
```

## Assembled datetime

`ROK`/`MC`/`DZ` (and `GG` for term data) are combined into a single `datetime`
column so you can plot and slice by time directly.

```python
df = IMGWClient().select(frequency="term", station_type="klimat", years=2024, months=1).get_dataframe()
print(df["datetime"].iloc[0])   # includes the hour for term data

# monthly data uses the first of the month
m = IMGWClient().select(frequency="monthly", station_type="opad", years=2015).get_dataframe()
print(m["datetime"].iloc[0])    # 2015-01-01
```

## English aliases

```python
cfg = StandardizationConfig(english_aliases=True)
df = IMGWClient(standardization=cfg).select(
    frequency="daily", station_type="klimat", years=2025, months=6
).get_dataframe()
print(df.columns[:5].tolist())   # ['datetime', 'station_code', 'station_name', 'year', 'month']
```
