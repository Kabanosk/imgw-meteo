"""Framework-agnostic windowing: shapes, per-station grouping, no-leakage split."""

import numpy as np
import pandas as pd
import pytest

from imgw_meteo.ml.windowing import (
    apply_scaler,
    fit_scaler,
    make_windows,
    prepare_split,
    split_windows,
)


def _frame(n_per_station: int = 50, stations=("A", "B")) -> pd.DataFrame:
    rows = []
    for st in stations:
        dates = pd.date_range("2020-01-01", periods=n_per_station, freq="D")
        for i, d in enumerate(dates):
            rows.append({"datetime": d, "NSP": st, "f1": float(i), "f2": float(i * 2), "t": float(i)})
    return pd.DataFrame(rows)


def test_window_shapes():
    w = make_windows(_frame(), features=["f1", "f2"], targets=["t"], input_window=10, horizon=1)
    assert w.x.shape[1:] == (10, 2)
    assert w.y.shape[1:] == (1, 1)
    assert len(w) == w.x.shape[0] == w.y.shape[0]


def test_windows_do_not_cross_stations():
    # 50 rows/station, window 10 + horizon 1 -> 40 windows/station, 2 stations.
    w = make_windows(_frame(50, ("A", "B")), features=["f1"], targets=["t"], input_window=10, horizon=1)
    assert len(w) == 80
    # Every window's station code is a single real station, never a mix.
    assert set(np.unique(w.station_codes)) == {"A", "B"}


def test_horizon_and_stride():
    w = make_windows(_frame(30, ("A",)), features=["f1"], targets=["t"], input_window=5, horizon=3, stride=2)
    assert w.y.shape[1] == 3
    # starts at 0,2,4,... up to n - input - horizon = 30-5-3 = 22
    assert len(w) == len(range(0, 23, 2))


def test_nan_windows_dropped():
    df = _frame(20, ("A",))
    df.loc[5, "f1"] = np.nan  # corrupts any window covering row 5
    w_clean = make_windows(df, features=["f1"], targets=["t"], input_window=5, horizon=1)
    w_full = make_windows(_frame(20, ("A",)), features=["f1"], targets=["t"], input_window=5, horizon=1)
    assert len(w_clean) < len(w_full)
    assert not np.isnan(w_clean.x).any()


def test_chronological_split_no_leakage():
    w = make_windows(_frame(100, ("A",)), features=["f1"], targets=["t"], input_window=5, horizon=1)
    tr, va, te = split_windows(w, split=(0.6, 0.2, 0.2), mode="chronological")
    # Train end-times all precede val, which precede test.
    assert tr.end_times.max() <= va.end_times.min()
    assert va.end_times.max() <= te.end_times.min()


def test_split_fractions_must_sum_to_one():
    w = make_windows(_frame(20, ("A",)), features=["f1"], targets=["t"], input_window=5, horizon=1)
    with pytest.raises(ValueError):
        split_windows(w, split=(0.5, 0.2, 0.2))


def test_scaler_fit_and_inverse_roundtrip():
    w = make_windows(_frame(60, ("A",)), features=["f1", "f2"], targets=["t"], input_window=5, horizon=1)
    scaler = fit_scaler(w, "zscore")
    scaled = apply_scaler(w, scaler)
    # zscore -> mean ~0, std ~1 across the flattened feature axis
    flat = scaled.x.reshape(-1, 2)
    assert np.allclose(flat.mean(axis=0), 0, atol=1e-5)
    assert np.allclose(flat.std(axis=0), 1, atol=1e-5)
    # inverse recovers the originals
    assert np.allclose(scaler.inverse_transform(scaled.x), w.x, atol=1e-4)


def test_targets_not_scaled():
    data = prepare_split(
        _frame(60, ("A",)),
        features=["f1"],
        targets=["t"],
        input_window=5,
        horizon=1,
        normalize="zscore",
    )
    # y stays in physical units: equals the raw per-step target values.
    assert data.train.y.max() > 1.5  # would be ~<=~3 if scaled; raw goes up to ~59


def test_prepare_split_scaler_fit_on_train_only():
    data = prepare_split(
        _frame(100, ("A",)),
        features=["f1"],
        targets=["t"],
        input_window=5,
        horizon=1,
        split=(0.6, 0.2, 0.2),
        normalize="zscore",
    )
    # Train inputs are ~standardized; test inputs use train stats so they are not.
    assert abs(data.train.x.reshape(-1, 1).mean()) < 1e-5
    assert abs(data.test.x.reshape(-1, 1).mean()) > 0.1


def test_empty_when_window_too_long():
    w = make_windows(_frame(5, ("A",)), features=["f1"], targets=["t"], input_window=10, horizon=1)
    assert len(w) == 0
    assert w.x.shape == (0, 10, 1)


def test_forward_fill_recovers_windows():
    df = _frame(30, ("A",))
    df.loc[[3, 7, 15], "f1"] = np.nan
    none = make_windows(df, features=["f1"], targets=["t"], input_window=5, horizon=1, fill_missing="none")
    fwd = make_windows(df, features=["f1"], targets=["t"], input_window=5, horizon=1, fill_missing="forward")
    assert len(fwd) > len(none)
    assert not np.isnan(fwd.x).any()
