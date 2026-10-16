# Configuration

`IMGWClient` is configured with two Pydantic objects, both optional. A couple of
common fields are also accepted directly as convenience keyword arguments.

```python
from imgw_meteo import IMGWClient, ClientConfig, StandardizationConfig

client = IMGWClient(
    config=ClientConfig(cache_dir="./cache", refresh="if-stale", timeout=60),
    standardization=StandardizationConfig(status_to_nan=True, add_datetime=True),
)

# convenience overrides (merged onto `config`)
client = IMGWClient(cache_dir="./cache", offline=False)
```

## ClientConfig — where files go, how downloads behave

| field | default | meaning |
|---|---|---|
| `cache_dir` | `None` | folder for cached downloads (`None` → `~/.cache/imgw-meteo`) |
| `offline` | `False` | work only from cached files; never use the network |
| `refresh` | `"if-stale"` | when to re-download: `"never"`, `"if-stale"`, `"always"` |
| `timeout` | `30.0` | per-request timeout in seconds (must be > 0) |

```python
# Fully reproducible offline run from a pre-populated cache:
client = IMGWClient(config=ClientConfig(cache_dir="./cache", offline=True))
```

Values are validated — a bad option fails fast:

```python
from pydantic import ValidationError

try:
    ClientConfig(refresh="sometimes")
except ValidationError as e:
    print(e)   # refresh must be never / if-stale / always
```

## StandardizationConfig — how data is cleaned

| field | default | meaning |
|---|---|---|
| `status_to_nan` | `True` | treat `8`/`9` markers and empty cells as missing |
| `keep_status` | `False` | also keep raw status columns as `<CODE>_status` |
| `include_term` | `False` | merge the term add-on member's columns in |
| `add_datetime` | `True` | add a `datetime` column from the date parts |
| `strip_strings` | `True` | trim padded/quoted station names |
| `normalize_decimals` | `True` | fix `-.4` → `-0.4`, `.0` → `0.0` |
| `english_aliases` | `False` | rename IMGW codes to English names |
| `schema_version` | `"1.0"` | pin the frozen canonical column layout |

```python
# Keep the quality flags and English names, for auditing:
cfg = StandardizationConfig(keep_status=True, english_aliases=True)
df = IMGWClient(standardization=cfg).select(
    frequency="daily", station_type="klimat", years=2025, months=6
).get_dataframe()
print([c for c in df.columns if c.endswith("_status")])
```

## One client, many selections

A single configured client can produce many independent selections sharing the
same cache:

```python
client = IMGWClient(cache_dir="./cache")

synop = client.select(frequency="daily", station_type="synop", years=2025, months=6)
klimat = client.select(frequency="daily", station_type="klimat", years=2025, months=6)
opad = client.select(frequency="monthly", station_type="opad", years=2024)
```
