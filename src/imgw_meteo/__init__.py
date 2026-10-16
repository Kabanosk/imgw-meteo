"""imgw_meteo — download, standardize and query IMGW meteorological data."""

from .client import Dataset, IMGWClient
from .config import ClientConfig, Refresh, StandardizationConfig
from .constants import Frequency, StationType
from .models import ColumnSpec, Station
from .stations import StationRegistry

__all__ = [
    "IMGWClient",
    "Dataset",
    "Frequency",
    "StationType",
    "Station",
    "StationRegistry",
    "ColumnSpec",
    "ClientConfig",
    "StandardizationConfig",
    "Refresh",
]

__version__ = "0.1.0"
