"""High-level API: IMGWClient (configured) and Dataset (a selection handle)."""

from collections.abc import Iterable
from pathlib import Path

import pandas as pd

from . import catalog, pipeline
from .config import ClientConfig, StandardizationConfig
from .constants import BASE_URL, SOURCE_ENCODING, STATIONS_FILE, Frequency, StationType
from .downloader import Downloader
from .exceptions import SelectionError
from .stations import StationRegistry, parse_stations


def _as_list(value: object | None) -> list | None:
    """Normalize a scalar / iterable / None into a list (or None)."""
    if value is None:
        return None
    if isinstance(value, (str, int)):
        return [value]
    return list(value)  # type: ignore[arg-type]


class IMGWClient:
    """Configured entry point: holds cache/network/standardization settings.

    Data selection is done via :meth:`select`, which returns a lightweight,
    reusable :class:`Dataset` handle. One client can produce many datasets while
    sharing the same cache.

    Configuration is supplied via Pydantic config objects
    (:class:`~imgw_meteo.config.ClientConfig`,
    :class:`~imgw_meteo.config.StandardizationConfig`). A few common fields are
    also accepted as convenience keyword arguments.
    """

    def __init__(
        self,
        *,
        config: ClientConfig | None = None,
        standardization: StandardizationConfig | None = None,
        # convenience overrides (merged onto the config objects)
        cache_dir: str | Path | None = None,
        offline: bool | None = None,
    ) -> None:
        """Create a configured client.

        :param config: Cache and network settings. Defaults to
            :class:`~imgw_meteo.config.ClientConfig` with its defaults.
        :param standardization: Data-cleaning options applied to every dataset
            this client produces. Defaults to
            :class:`~imgw_meteo.config.StandardizationConfig` defaults.
        :param cache_dir: Convenience override for ``config.cache_dir``: the
            folder where downloads are cached. ``None`` leaves ``config`` as is.
        :param offline: Convenience override for ``config.offline``: when
            ``True``, work only from cached files. ``None`` leaves ``config`` as is.
        """
        base = config or ClientConfig()
        overrides: dict[str, object] = {}
        if cache_dir is not None:
            overrides["cache_dir"] = str(cache_dir)
        if offline is not None:
            overrides["offline"] = offline
        self.config = base.model_copy(update=overrides) if overrides else base

        self.standardization = standardization or StandardizationConfig()
        self.downloader = Downloader(
            self.config.cache_dir,
            offline=self.config.offline,
            refresh=self.config.refresh.value,
            timeout=self.config.timeout,
        )
        self._registry: StationRegistry | None = None

    # --- stations ---------------------------------------------------------
    def stations(self) -> StationRegistry:
        """Load (and cache) the station registry.

        :returns: A searchable registry of all meteorological stations.
        :rtype: :class:`~imgw_meteo.stations.StationRegistry`
        """
        if self._registry is None:
            path = self.downloader.fetch_file(BASE_URL + STATIONS_FILE)
            text = path.read_bytes().decode(SOURCE_ENCODING)
            self._registry = StationRegistry(parse_stations(text))
        return self._registry

    # --- discovery --------------------------------------------------------
    def available_years(self, frequency: str | Frequency, station_type: str | StationType) -> list[str]:
        """List the years (or year-ranges) available for a data set.

        :param frequency: Temporal resolution, e.g. ``"daily"`` / ``"dobowe"``.
        :param station_type: Station type, e.g. ``"synop"``, ``"klimat"``,
            ``"opad"``.
        :returns: Directory names found on the server, sorted ascending, e.g.
            ``["1966_1970", "2001", ..., "2026"]``.
        :rtype: list[str]
        """
        freq = Frequency.parse(frequency)
        stype = StationType.parse(station_type)
        html = self.downloader.fetch_text(catalog.type_dir_url(freq, stype))
        entries = catalog.parse_index(html)
        return sorted(e.rstrip("/") for e in entries if e.endswith("/"))

    # --- selection --------------------------------------------------------
    def select(
        self,
        *,
        frequency: str | Frequency,
        station_type: str | StationType,
        years: int | Iterable[int],
        months: int | Iterable[int] | None = None,
        stations: str | Iterable[str] | None = None,
    ) -> "Dataset":
        """Describe a subset of IMGW data to work with.

        This only records the selection; no download happens until you call
        :meth:`Dataset.get_dataframe` (or :meth:`Dataset.export`).

        :param frequency: Temporal resolution, e.g. ``"daily"`` / ``"dobowe"``.
        :param station_type: Station type: ``"synop"``, ``"klimat"`` or ``"opad"``.
        :param years: A single year or any iterable of years, e.g. ``2025`` or  ``range(2010, 2026)``.
        :param months: Optional month or months (1–12) to restrict to. Leave as
            ``None`` for the whole year.
        :param stations: Optional station code or codes to restrict to. Leave as
            ``None`` for all stations.
        :returns: A reusable selection handle.
        :rtype: :class:`Dataset`
        """
        year_list = sorted(_as_list(years))  # type: ignore[arg-type]
        month_list = _as_list(months)
        if month_list is not None:
            month_list = sorted(month_list)
        freq = Frequency.parse(frequency)
        stype = StationType.parse(station_type)
        # Fail fast on combinations IMGW does not publish (e.g. term/opad).
        from .canonical import schema_codes

        try:
            schema_codes(freq, stype)
        except KeyError as exc:
            raise SelectionError(str(exc)) from None
        return Dataset(
            client=self,
            frequency=freq,
            station_type=stype,
            years=year_list,
            months=month_list,
            stations=_as_list(stations),
        )


class Dataset:
    """An immutable selection handle. Call :meth:`get_dataframe` to materialize."""

    def __init__(
        self,
        *,
        client: IMGWClient,
        frequency: Frequency,
        station_type: StationType,
        years: list[int],
        months: list[int] | None,
        stations: list[str] | None,
    ) -> None:
        self.client = client
        self.frequency = frequency
        self.station_type = station_type
        self.years = years
        self.months = months
        self.stations = stations

    def get_dataframe(self) -> pd.DataFrame:
        """Download, parse and standardize the whole selection into one table.

        :returns: A single tidy, typed table combining every file in the
            selection, cleaned according to the client's standardization config.
        :rtype: pandas.DataFrame
        :raises imgw_meteo.exceptions.SelectionError: If no files match the
            selection, or the selection yields no data.
        """
        return pipeline.load_selection(
            self.client.downloader,
            self.frequency,
            self.station_type,
            self.years,
            self.months,
            self.stations,
            self.client.standardization,
        )

    def export(self, path: str | Path) -> Path:
        """Write the standardized selection to a file.

        The format is chosen from the file extension: ``.parquet`` writes
        Parquet, anything else writes UTF-8 CSV.

        :param path: Destination file path, e.g. ``"synop.parquet"`` or
            ``"out.csv"``.
        :returns: The path that was written.
        :rtype: pathlib.Path
        """
        path = Path(path)
        df = self.get_dataframe()
        if path.suffix.lower() == ".parquet":
            df.to_parquet(path, index=False)
        else:
            df.to_csv(path, index=False, encoding="utf-8")
        return path

    def get_dataloaders(self, *args: object, **kwargs: object):
        """Build PyTorch dataloaders for this selection.

        .. note::
           Not implemented yet — arrives in a later iteration (``ml.torch``).

        :raises NotImplementedError: Always, until the ML layer lands.
        """
        raise NotImplementedError("get_dataloaders arrives in the next iteration (ml.torch).")
