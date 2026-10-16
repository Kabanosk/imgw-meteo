"""PyTorch adapter: windows -> Dataset -> DataLoaders.

This is the only module that imports torch. Importing it without PyTorch
installed raises a clear, actionable error.
"""

from dataclasses import dataclass

import pandas as pd

from .windowing import Scaler, WindowArrays, prepare_split

try:
    import torch
    from torch.utils.data import DataLoader
    from torch.utils.data import Dataset as _TorchDataset
except ImportError as exc:  # pragma: no cover - exercised only without torch
    raise ImportError("PyTorch is not installed. Install the ML extra:\n    pip install imgw-meteo[torch]") from exc


_DTYPES = {"float32": torch.float32, "float64": torch.float64}


class IMGWWindowDataset(_TorchDataset):
    """Wrap :class:`~imgw_meteo.ml.windowing.WindowArrays` as a torch Dataset.

    Each item is ``(x, y)`` with ``x`` shaped ``(input_window, n_features)`` and
    ``y`` shaped ``(horizon, n_targets)``.
    """

    def __init__(self, windows: WindowArrays, dtype: str = "float32") -> None:
        if dtype not in _DTYPES:
            raise ValueError(f"dtype must be one of {sorted(_DTYPES)}")
        self._x = torch.as_tensor(windows.x, dtype=_DTYPES[dtype])
        self._y = torch.as_tensor(windows.y, dtype=_DTYPES[dtype])
        self.feature_names = windows.feature_names
        self.target_names = windows.target_names

    def __len__(self) -> int:
        return self._x.shape[0]

    def __getitem__(self, index: int) -> tuple[torch.Tensor, torch.Tensor]:
        return self._x[index], self._y[index]


@dataclass
class DataLoaders:
    """Bundle of the three loaders plus everything needed for inference.

    Unpackable as ``train, val, test = loaders`` for convenience, while still
    carrying the fitted :class:`~imgw_meteo.ml.windowing.Scaler` and column
    names.
    """

    train: DataLoader
    val: DataLoader
    test: DataLoader
    scaler: Scaler
    feature_names: list[str]
    target_names: list[str]

    def __iter__(self):
        yield self.train
        yield self.val
        yield self.test


def build_dataloaders(
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
    batch_size: int = 64,
    shuffle_train: bool = True,
    num_workers: int = 0,
    dtype: str = "float32",
    seed: int = 42,
    time_col: str = "datetime",
    station_col: str = "NSP",
) -> DataLoaders:
    """Turn a standardized IMGW frame into train/val/test PyTorch dataloaders.

    :param df: Standardized table (output of ``Dataset.get_dataframe``).
    :param features: Input feature columns.
    :param targets: Target columns to predict.
    :param input_window: Number of past steps per input window.
    :param horizon: Number of future steps to predict.
    :param stride: Step between consecutive window starts.
    :param split: Train/val/test fractions (must sum to 1.0).
    :param split_mode: ``"chronological"`` (no leakage) or ``"random"``.
    :param normalize: ``"zscore"``, ``"minmax"`` or ``"none"`` (features only).
    :param fill_missing: ``"none"``, ``"forward"``, ``"mean"`` or ``"drop"``.
    :param batch_size: DataLoader batch size.
    :param shuffle_train: Shuffle the training loader (val/test never shuffled).
    :param num_workers: DataLoader worker processes.
    :param dtype: Tensor dtype, ``"float32"`` or ``"float64"``.
    :param seed: Seed for random split.
    :returns: A :class:`DataLoaders` bundle.
    """
    data = prepare_split(
        df,
        features=features,
        targets=targets,
        input_window=input_window,
        horizon=horizon,
        stride=stride,
        split=split,
        split_mode=split_mode,
        normalize=normalize,
        fill_missing=fill_missing,
        seed=seed,
        time_col=time_col,
        station_col=station_col,
    )

    counts = {"train": len(data.train), "val": len(data.val), "test": len(data.test)}
    if min(counts.values()) == 0:
        raise ValueError(
            f"a split is empty (windows per split: {counts}). This usually means "
            "too few valid windows after dropping those containing missing values. "
            "Try: a longer year range, a smaller input_window, fewer/denser "
            "features, or fill_missing='forward'."
        )

    def loader(windows: WindowArrays, *, shuffle: bool) -> DataLoader:
        return DataLoader(
            IMGWWindowDataset(windows, dtype=dtype),
            batch_size=batch_size,
            shuffle=shuffle,
            num_workers=num_workers,
        )

    return DataLoaders(
        train=loader(data.train, shuffle=shuffle_train),
        val=loader(data.val, shuffle=False),
        test=loader(data.test, shuffle=False),
        scaler=data.scaler,
        feature_names=list(features),
        target_names=list(targets),
    )
