"""Parse and query the IMGW station registry (wykaz_stacji.csv)."""

import csv
import io
import unicodedata

from .models import Station


def _normalize(text: str) -> str:
    """Case/diacritic-insensitive key for name search (ł -> l, ą -> a, ...)."""
    text = text.replace("ł", "l").replace("Ł", "L")
    decomposed = unicodedata.normalize("NFKD", text)
    stripped = "".join(c for c in decomposed if not unicodedata.combining(c))
    return stripped.casefold().strip()


def parse_stations(text: str) -> list[Station]:
    """Parse the decoded (UTF-8 str) station CSV into Station objects.

    Source rows look like ``"252200080","BIAŁOWIEŻA"," 3902"`` — three quoted
    fields: numeric code, name, five-char code (which may carry leading spaces).

    :param text: Decoded contents of ``wykaz_stacji.csv``.
    :returns: One :class:`~imgw_meteo.models.Station` per valid row.
    :rtype: list[imgw_meteo.models.Station]
    """
    reader = csv.reader(io.StringIO(text))
    stations: list[Station] = []
    for row in reader:
        if len(row) < 3:
            continue
        if not row[0].strip():
            continue
        # Station normalizes (strips) all fields on construction.
        stations.append(Station(code=row[0], name=row[1], code5=row[2]))
    return stations


class StationRegistry:
    """Searchable collection of stations."""

    def __init__(self, stations: list[Station]) -> None:
        self._stations = stations
        self._by_code = {s.code: s for s in stations}
        self._by_code5 = {s.code5: s for s in stations if s.code5}

    def __len__(self) -> int:
        return len(self._stations)

    def all(self) -> list[Station]:
        return list(self._stations)

    def by_code(self, code: str) -> Station | None:
        """Look up a station by its numeric code.

        :param code: Numeric station code, e.g. ``"252200080"``.
        :returns: The matching station, or ``None`` if not found.
        :rtype: imgw_meteo.models.Station | None
        """
        return self._by_code.get(code.strip())

    def search(self, name: str) -> list[Station]:
        """Diacritic/case-insensitive substring search over station names.

        :param name: Full or partial station name, e.g. ``"warszawa"``.
        :returns: All stations whose name contains ``name`` (ignoring case and
            Polish diacritics).
        :rtype: list[imgw_meteo.models.Station]
        """
        key = _normalize(name)
        return [s for s in self._stations if key in _normalize(s.name)]
