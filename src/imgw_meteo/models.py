"""Internal value objects (plain frozen dataclasses).

Configuration lives in :mod:`imgw_meteo.config` (Pydantic). These dataclasses
carry trusted internal data and sit on hot paths, so they stay dependency-free.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Station:
    """A meteorological station from the IMGW registry.

    All string fields are normalized on construction (surrounding whitespace
    trimmed), so values are clean regardless of how the Station was built. In
    the source CSV ``code5`` may carry leading spaces, e.g. ``" 3902"``.
    """

    code: str  # numeric station code, e.g. "252200080"
    name: str  # human-readable name
    code5: str  # five-character code

    def __post_init__(self) -> None:
        # frozen dataclass: assign via object.__setattr__ to normalize fields.
        object.__setattr__(self, "code", self.code.strip())
        object.__setattr__(self, "name", self.name.strip())
        object.__setattr__(self, "code5", self.code5.strip())

    def __str__(self) -> str:  # pragma: no cover - trivial
        return f"{self.name} ({self.code})"


@dataclass(frozen=True)
class ColumnSpec:
    """A single canonical column definition."""

    code: str  # IMGW column code, e.g. "TMAX"
    dtype: str  # pandas dtype string, e.g. "float32", "Int16", "category"
    description_pl: str = ""
    description_en: str = ""
    unit: str = ""
    status_col: str | None = None  # paired status column, e.g. "WTMAX"
    is_status: bool = False  # True if this column itself is a status column
    english_alias: str | None = None
