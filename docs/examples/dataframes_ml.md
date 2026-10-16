# From data to dataloaders

How a standardized frame becomes training-ready tensors, step by step.

## The one-liner

```python
from imgw_meteo import IMGWClient

train, val, test = (
    IMGWClient()
    .select(frequency="daily", station_type="synop", years=range(2015, 2026))
    .get_dataloaders(
        features=["TMAX", "TMIN", "STD"],
        targets=["TMAX"],
        input_window=30,
        horizon=1,
        batch_size=64,
    )
)

x, y = next(iter(train))
print(x.shape, y.shape)   # (64, 30, 3)  (64, 1, 1)
```

## What the parameters mean

| parameter | meaning |
|---|---|
| `features` | input columns fed to the model |
| `targets` | columns to predict |
| `input_window` | number of past time steps per sample |
| `horizon` | number of future steps to predict |
| `stride` | step between consecutive windows (default 1) |
| `split` | train/val/test fractions, default `(0.7, 0.15, 0.15)` |
| `split_mode` | `"chronological"` (no leakage, default) or `"random"` |
| `normalize` | `"zscore"` (default), `"minmax"`, or `"none"` — features only |
| `fill_missing` | `"none"` (default), `"forward"`, `"mean"`, `"drop"` |
| `batch_size`, `shuffle_train`, `num_workers`, `dtype`, `seed` | passed through |

## No data leakage by default

Splitting is chronological: validation and test windows come strictly after
training windows in time, and normalization statistics are fit on the training
split only.

```python
loaders = IMGWClient().select(
    frequency="daily", station_type="synop", years=range(2010, 2026)
).get_dataloaders(features=["TMAX", "TMIN"], targets=["TMAX"], input_window=30)

print(loaders.scaler.method)         # "zscore"
print(loaders.feature_names)         # ['TMAX', 'TMIN']
```

## Windows never cross stations

When a selection spans multiple stations, each window is built within a single
station, so you never train on a sequence that jumps from one place to another.

## Multi-step forecasting

```python
loaders = IMGWClient().select(
    frequency="daily", station_type="synop", years=range(2015, 2026), stations=["250190390"]
).get_dataloaders(
    features=["TMAX", "TMIN", "STD", "SMDB"],
    targets=["TMAX", "TMIN"],
    input_window=60,
    horizon=7,          # predict a week ahead
    fill_missing="forward",
)
x, y = next(iter(loaders.train))
print(y.shape)          # (batch, 7, 2)
```

## Targets stay in physical units

Only features are scaled; targets are left in °C/mm/etc., so your loss and
predictions are directly interpretable. If you *do* scale something yourself,
the fitted scaler can invert it:

```python
import numpy as np

scaler = loaders.scaler
scaled = scaler.transform(np.zeros((1, len(scaler.feature_names))))
original = scaler.inverse_transform(scaled)
```

## Using the framework-agnostic core (numpy, no torch)

If you use JAX/sklearn/plain numpy, build windows directly:

```python
from imgw_meteo.ml.windowing import prepare_split

df = IMGWClient().select(
    frequency="daily", station_type="synop", years=range(2015, 2026)
).get_dataframe()

split = prepare_split(
    df, features=["TMAX", "TMIN"], targets=["TMAX"], input_window=30, horizon=1
)
print(split.train.x.shape, split.train.y.shape)   # numpy arrays
```
