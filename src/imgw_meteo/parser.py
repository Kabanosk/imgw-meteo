"""Parse a downloaded IMGW zip into a raw (string-typed) DataFrame.

The only job here is: unzip -> decode cp1250 -> read CSV with the canonical
header -> return raw strings. All cleaning/typing happens in ``standardize``.
"""

import io
import zipfile
from pathlib import Path

import pandas as pd

from .constants import SOURCE_ENCODING
from .exceptions import ParseError


def read_zip_member(zip_path: Path, member: str, columns: list[str]) -> pd.DataFrame:
    """Read one CSV member from a zip as all-string columns.

    :param zip_path: Local path to the ``.zip`` file.
    :param member: Name of the CSV member to read.
    :param columns: Canonical column names to assign (source files have no
        header row).
    :returns: The member's rows as an all-string table.
    :rtype: pandas.DataFrame
    :raises imgw_meteo.exceptions.ParseError: If the member is missing, the zip
        is invalid, or the column count does not match.
    """
    try:
        with zipfile.ZipFile(zip_path) as zf:
            if member not in zf.namelist():
                raise ParseError(f"member {member!r} not found in {zip_path.name}; present: {zf.namelist()}")
            raw = zf.read(member)
    except zipfile.BadZipFile as exc:
        raise ParseError(f"{zip_path} is not a valid zip: {exc}") from exc

    text = raw.decode(SOURCE_ENCODING)
    df = pd.read_csv(
        io.StringIO(text),
        header=None,
        names=columns,
        dtype=str,
        keep_default_na=False,
        na_values=[],
        skipinitialspace=True,
    )
    if df.shape[1] != len(columns):
        raise ParseError(f"{member}: expected {len(columns)} columns, got {df.shape[1]}")
    return df


def list_members(zip_path: Path) -> list[str]:
    """Return CSV member names inside a zip."""
    with zipfile.ZipFile(zip_path) as zf:
        return [n for n in zf.namelist() if n.lower().endswith(".csv")]
