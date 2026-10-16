# Installation

`imgw-meteo` requires **Python 3.12+**.

## Choose what you need

```bash
pip install imgw-meteo          # core API only (httpx, pandas, numpy, pydantic)
pip install imgw-meteo[cli]     # + the `imgw-meteo` command-line tool
pip install imgw-meteo[torch]   # + PyTorch dataloaders
pip install imgw-meteo[all]     # CLI + PyTorch
```

| extra | adds | needed for |
|---|---|---|
| *(none)* | core | the Python API, DataFrames, exports |
| `cli` | typer, rich | the `imgw-meteo` command |
| `torch` | torch | `Dataset.get_dataloaders(...)` |
| `all` | the above | everything |

The core install is deliberately light — importing `IMGWClient` never pulls in
PyTorch or a CLI framework. If you call `get_dataloaders` without the `torch`
extra, you get a clear error telling you to install it.

## With uv

```bash
uv add imgw-meteo          # or: uv add "imgw-meteo[torch]"
```

## Verify

```bash
python -c "import imgw_meteo; print(imgw_meteo.__version__)"
imgw-meteo --help          # if you installed the [cli] extra
```

## Where downloads are cached

By default, downloaded IMGW files are cached under `~/.cache/imgw-meteo` so you
never re-download the same data. Change it with
`IMGWClient(cache_dir="...")` — see {doc}`guide/configuration`.
```
