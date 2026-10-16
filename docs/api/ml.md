# Machine learning

The framework-agnostic windowing core (no heavy dependencies):

```{eval-rst}
.. automodule:: imgw_meteo.ml.windowing
   :members:
```

The PyTorch adapter (requires the ``[torch]`` extra):

```{eval-rst}
.. autoclass:: imgw_meteo.ml.torch.IMGWWindowDataset
   :members:

.. autoclass:: imgw_meteo.ml.torch.DataLoaders
   :members:

.. autofunction:: imgw_meteo.ml.torch.build_dataloaders
```
