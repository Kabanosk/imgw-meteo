# Analysis recipes

These use plain pandas on the standardized frame — because dtypes and missing
values are already clean, the analysis is straightforward.

```python
from imgw_meteo import IMGWClient

client = IMGWClient()
df = client.select(
    frequency="daily", station_type="synop", years=2024, stations=["250190390"]
).get_dataframe()
```

## Monthly mean temperature

```python
monthly_mean = (
    df.set_index("datetime")["STD"].resample("MS").mean()
)
print(monthly_mean)
```

## Hottest and coldest day of the year

```python
hottest = df.loc[df["TMAX"].idxmax()]
coldest = df.loc[df["TMIN"].idxmin()]
print("hottest:", hottest["datetime"].date(), hottest["TMAX"], "°C")
print("coldest:", coldest["datetime"].date(), coldest["TMIN"], "°C")
```

## Total and rainy-day precipitation

```python
total_rain = df["SMDB"].sum()
rainy_days = (df["SMDB"] > 0).sum()
print(f"{total_rain:.1f} mm over {rainy_days} rainy days")
```

## Missing-data audit

```python
missing = df.isna().mean().sort_values(ascending=False)
print((missing[missing > 0] * 100).round(1).astype(str) + " %")
```

## Compare several stations

```python
multi = client.select(
    frequency="daily",
    station_type="synop",
    years=2024,
    stations=["250190390", "352200375", "254200200"],
).get_dataframe()

summary = multi.groupby("POST")["STD"].agg(["mean", "min", "max"]).round(1)
print(summary)
```

## Rolling 7-day average

```python
df = df.sort_values("datetime")
df["TMAX_7d"] = df["TMAX"].rolling(7, min_periods=1).mean()
print(df[["datetime", "TMAX", "TMAX_7d"]].tail())
```

## Growing-degree-days (base 10 °C)

```python
gdd = (df["STD"] - 10).clip(lower=0).sum()
print(f"Accumulated GDD (base 10 °C): {gdd:.0f}")
```
