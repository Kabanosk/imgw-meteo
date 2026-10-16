"""Machine-learning adapters (PyTorch-first). Lazily import frameworks.

This iteration ships the public surface; ``get_dataloaders`` is implemented in
the next iteration.
"""


def get_dataloaders(*args: object, **kwargs: object):  # pragma: no cover - stub
    raise NotImplementedError("get_dataloaders arrives in the next iteration (ml.torch).")


__all__ = ["get_dataloaders"]
