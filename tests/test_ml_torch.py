"""PyTorch adapter tests (skipped if torch is not installed)."""

import pandas as pd
import pytest

torch = pytest.importorskip("torch")

from imgw_meteo.ml.torch import DataLoaders, IMGWWindowDataset, build_dataloaders  # noqa: E402
from imgw_meteo.ml.windowing import make_windows  # noqa: E402


def _frame(n: int = 120, stations=("A", "B")) -> pd.DataFrame:
    rows = []
    for st in stations:
        dates = pd.date_range("2020-01-01", periods=n, freq="D")
        for i, d in enumerate(dates):
            rows.append({"datetime": d, "NSP": st, "TMAX": float(i), "TMIN": float(-i), "STD": float(i / 2)})
    return pd.DataFrame(rows)


def test_dataset_item_shapes():
    w = make_windows(_frame(), features=["TMAX", "TMIN"], targets=["TMAX"], input_window=7, horizon=1)
    ds = IMGWWindowDataset(w)
    x, y = ds[0]
    assert tuple(x.shape) == (7, 2)
    assert tuple(y.shape) == (1, 1)
    assert x.dtype == torch.float32


def test_build_dataloaders_bundle_and_batch_shapes():
    loaders = build_dataloaders(
        _frame(),
        features=["TMAX", "TMIN", "STD"],
        targets=["TMAX"],
        input_window=10,
        horizon=1,
        batch_size=16,
    )
    assert isinstance(loaders, DataLoaders)
    xb, yb = next(iter(loaders.train))
    assert xb.shape[1:] == (10, 3)
    assert yb.shape[1:] == (1, 1)
    assert xb.shape[0] <= 16


def test_dataloaders_unpackable_as_tuple():
    loaders = build_dataloaders(_frame(), features=["TMAX"], targets=["TMAX"], input_window=5, batch_size=8)
    train, val, test = loaders  # bundle is iterable
    assert len(train.dataset) > 0
    assert len(val.dataset) > 0
    assert len(test.dataset) > 0


def test_scaler_carried_on_bundle():
    loaders = build_dataloaders(
        _frame(), features=["TMAX", "TMIN"], targets=["TMAX"], input_window=5, normalize="zscore"
    )
    assert loaders.scaler.method == "zscore"
    assert loaders.feature_names == ["TMAX", "TMIN"]
    assert loaders.target_names == ["TMAX"]


def test_horizon_multi_step():
    loaders = build_dataloaders(
        _frame(), features=["TMAX"], targets=["TMAX", "TMIN"], input_window=8, horizon=4, batch_size=4
    )
    xb, yb = next(iter(loaders.train))
    assert yb.shape[1:] == (4, 2)


def test_empty_split_raises_actionable_error():
    # Window longer than available data -> zero windows -> clear error.
    with pytest.raises(ValueError, match="split is empty"):
        build_dataloaders(_frame(n=20), features=["TMAX"], targets=["TMAX"], input_window=50, horizon=1)
