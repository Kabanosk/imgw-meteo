"""Framework-agnostic windowing for time-series ML (no torch/tf imports).

Turns a standardized IMGW table into sliding windows suitable for sequence
models, with per-station grouping, leakage-free splitting, and train-only
normalization. The torch/tf adapters build on :func:`prepare_split`.
"""

from dataclasses import dataclass

import numpy as np
import pandas as pd

_FILL_POLICIES = ("none", "forward", "mean", "drop")
_NORMALIZE = ("none", "zscore", "minmax")
_SPLIT_MODES = ("chronological", "random")


@dataclass(frozen=True)
class Scaler:
    """Fitted normalization statistics (fit on TRAIN windows only).

    :param method: ``"zscore"``, ``"minmax"`` or ``"none"``.
    :param center: Per-feature offset (mean for zscore, min for minmax).
    :param scale: Per-feature divisor (std for zscore, max-min for minmax).
    :param feature_names: Feature order the stats correspond to.
    """

    method: str
    center: np.ndarray
    scale: np.ndarray
    feature_names: list[str]

    def transform(self, x: np.ndarray) -> np.ndarray:
        """Normalize an array whose last axis is features."""
        if self.method == "none":
            return x
        return (x - self.center) / self.scale

    def inverse_transform(self, x: np.ndarray) -> np.ndarray:
        """Undo :meth:`transform` (last axis is features)."""
        if self.method == "none":
            return x
        return x * self.scale + self.center


@dataclass(frozen=True)
class WindowArrays:
    """Windowed arrays plus the metadata needed to interpret/split them.

    :param x: Inputs, shape ``(n_windows, input_window, n_features)``.
    :param y: Targets, shape ``(n_windows, horizon, n_targets)``.
    :param feature_names: Feature column order (last axis of ``x``).
    :param target_names: Target column order (last axis of ``y``).
    :param station_codes: ``(n_windows,)`` station code per window.
    :param end_times: ``(n_windows,)`` datetime64 of the last input step.
    """

    x: np.ndarray
    y: np.ndarray
    feature_names: list[str]
    target_names: list[str]
    station_codes: np.ndarray
    end_times: np.ndarray

    def __len__(self) -> int:
        return int(self.x.shape[0])


@dataclass(frozen=True)
class WindowSplit:
    """Train/val/test windows plus the scaler fit on train and applied to all."""

    train: WindowArrays
    val: WindowArrays
    test: WindowArrays
    scaler: Scaler


# --- helpers ---------------------------------------------------------------
def _fill(frame: pd.DataFrame, cols: list[str], policy: str) -> pd.DataFrame:
    if policy in ("none", "drop"):
        return frame
    if policy == "forward":
        for c in cols:
            frame[c] = frame[c].ffill()
    elif policy == "mean":
        for c in cols:
            frame[c] = frame[c].fillna(frame[c].mean())
    return frame


def _slice_station(
    values: np.ndarray,
    targets: np.ndarray,
    times: np.ndarray,
    *,
    input_window: int,
    horizon: int,
    stride: int,
) -> tuple[list[np.ndarray], list[np.ndarray], list[np.datetime64]]:
    xs: list[np.ndarray] = []
    ys: list[np.ndarray] = []
    ends: list[np.datetime64] = []
    n = len(values)
    last_start = n - input_window - horizon
    for start in range(0, last_start + 1, stride):
        in_end = start + input_window
        out_end = in_end + horizon
        x = values[start:in_end]
        y = targets[in_end:out_end]
        if np.isnan(x).any() or np.isnan(y).any():
            continue
        xs.append(x)
        ys.append(y)
        ends.append(times[in_end - 1])
    return xs, ys, ends


def make_windows(
    df: pd.DataFrame,
    *,
    features: list[str],
    targets: list[str],
    input_window: int,
    horizon: int = 1,
    stride: int = 1,
    time_col: str = "datetime",
    station_col: str = "NSP",
    fill_missing: str = "none",
) -> WindowArrays:
    """Build sliding windows, grouped per station so none spans two stations.

    Rows are sorted by ``(station, time)``. Windows still containing NaN after
    the fill policy are dropped.

    :raises ValueError: On bad parameters or missing columns.
    """
    if fill_missing not in _FILL_POLICIES:
        raise ValueError(f"fill_missing must be one of {_FILL_POLICIES}")
    if input_window < 1 or horizon < 1 or stride < 1:
        raise ValueError("input_window, horizon and stride must be >= 1")
    missing = [c for c in [*features, *targets] if c not in df.columns]
    if missing:
        raise ValueError(f"columns not in dataframe: {missing}")

    has_station = station_col in df.columns
    has_time = time_col in df.columns
    sort_cols = [c for c in (station_col, time_col) if c in df.columns]
    work = df.sort_values(sort_cols) if sort_cols else df.copy()

    xs: list[np.ndarray] = []
    ys: list[np.ndarray] = []
    ends: list[np.datetime64] = []
    codes: list[object] = []

    groups = work.groupby(station_col, sort=False) if has_station else [(None, work)]
    for code, g in groups:
        g = _fill(g.copy(), [*features, *targets], fill_missing)
        vals = g[features].to_numpy(dtype="float32", na_value=np.nan)
        tgts = g[targets].to_numpy(dtype="float32", na_value=np.nan)
        times = g[time_col].to_numpy() if has_time else np.arange(len(g), dtype="datetime64[s]")
        gx, gy, ge = _slice_station(vals, tgts, times, input_window=input_window, horizon=horizon, stride=stride)
        xs.extend(gx)
        ys.extend(gy)
        ends.extend(ge)
        codes.extend([code] * len(gx))

    if not xs:
        empty_x = np.empty((0, input_window, len(features)), dtype="float32")
        empty_y = np.empty((0, horizon, len(targets)), dtype="float32")
        return WindowArrays(
            empty_x,
            empty_y,
            list(features),
            list(targets),
            np.array([], dtype=object),
            np.array([], dtype="datetime64[ns]"),
        )

    return WindowArrays(
        x=np.stack(xs),
        y=np.stack(ys),
        feature_names=list(features),
        target_names=list(targets),
        station_codes=np.array(codes, dtype=object),
        end_times=np.array(ends, dtype="datetime64[ns]"),
    )


def _subset(w: WindowArrays, idx: np.ndarray) -> WindowArrays:
    return WindowArrays(
        x=w.x[idx],
        y=w.y[idx],
        feature_names=w.feature_names,
        target_names=w.target_names,
        station_codes=w.station_codes[idx],
        end_times=w.end_times[idx],
    )


def split_windows(
    w: WindowArrays,
    *,
    split: tuple[float, float, float] = (0.7, 0.15, 0.15),
    mode: str = "chronological",
    seed: int = 42,
) -> tuple[WindowArrays, WindowArrays, WindowArrays]:
    """Split windows into train/val/test.

    ``chronological`` orders by each window's end time so val/test fall strictly
    after train (no temporal leakage). ``random`` shuffles with ``seed``.
    """
    if mode not in _SPLIT_MODES:
        raise ValueError(f"mode must be one of {_SPLIT_MODES}")
    if not np.isclose(sum(split), 1.0):
        raise ValueError("split fractions must sum to 1.0")

    n = len(w)
    if mode == "chronological":
        order = np.argsort(w.end_times, kind="stable")
    else:
        rng = np.random.default_rng(seed)
        order = rng.permutation(n)

    n_train = int(n * split[0])
    n_val = int(n * split[1])
    tr = order[:n_train]
    va = order[n_train : n_train + n_val]
    te = order[n_train + n_val :]
    return _subset(w, tr), _subset(w, va), _subset(w, te)


def fit_scaler(w: WindowArrays, method: str) -> Scaler:
    """Fit normalization on these (train) windows only."""
    if method not in _NORMALIZE:
        raise ValueError(f"normalize must be one of {_NORMALIZE}")
    n_features = w.x.shape[-1]
    if method == "none" or len(w) == 0:
        return Scaler("none", np.zeros(n_features), np.ones(n_features), w.feature_names)
    flat = w.x.reshape(-1, n_features)
    if method == "zscore":
        center = np.nanmean(flat, axis=0)
        scale = np.nanstd(flat, axis=0)
    else:  # minmax
        center = np.nanmin(flat, axis=0)
        scale = np.nanmax(flat, axis=0) - center
    scale = np.where(scale == 0, 1.0, scale)  # avoid divide-by-zero
    return Scaler(method, center.astype("float32"), scale.astype("float32"), w.feature_names)


def apply_scaler(w: WindowArrays, scaler: Scaler) -> WindowArrays:
    """Return a copy of ``w`` with inputs normalized (targets left untouched)."""
    return WindowArrays(
        x=scaler.transform(w.x),
        y=w.y,
        feature_names=w.feature_names,
        target_names=w.target_names,
        station_codes=w.station_codes,
        end_times=w.end_times,
    )


def prepare_split(
    df: pd.DataFrame,
    *,
    features: list[str],
    targets: list[str],
    input_window: int,
    horizon: int = 1,
    stride: int = 1,
    split: tuple[float, float, float] = (0.7, 0.15, 0.15),
    split_mode: str = "chronological",
    normalize: str = "zscore",
    fill_missing: str = "none",
    seed: int = 42,
    time_col: str = "datetime",
    station_col: str = "NSP",
) -> WindowSplit:
    """End-to-end: window -> split -> fit scaler on train -> apply to all.

    Only inputs (``x``) are scaled; targets (``y``) stay in physical units so
    losses and predictions are directly interpretable.
    """
    windows = make_windows(
        df,
        features=features,
        targets=targets,
        input_window=input_window,
        horizon=horizon,
        stride=stride,
        time_col=time_col,
        station_col=station_col,
        fill_missing=fill_missing,
    )
    train, val, test = split_windows(windows, split=split, mode=split_mode, seed=seed)
    scaler = fit_scaler(train, normalize)
    return WindowSplit(
        train=apply_scaler(train, scaler),
        val=apply_scaler(val, scaler),
        test=apply_scaler(test, scaler),
        scaler=scaler,
    )
