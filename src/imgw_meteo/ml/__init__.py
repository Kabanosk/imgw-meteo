"""Machine-learning adapters.

The framework-agnostic windowing lives in :mod:`imgw_meteo.ml.windowing` and
has no heavy dependencies. The PyTorch adapter lives in
:mod:`imgw_meteo.ml.torch` and imports torch lazily (install the ``[torch]``
extra). The public entry point for most users is ``Dataset.get_dataloaders``.
"""
