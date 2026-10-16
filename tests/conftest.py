"""Shared fixtures. All tests run offline — no real network access."""

import io
import zipfile
from pathlib import Path

import pytest

from imgw_meteo.constants import SOURCE_ENCODING

# A tiny klimat-daily (k_d, 18-column) CSV, mimicking real IMGW quirks:
# quoted key fields, unquoted values, status 8/9 markers, cp1250 Polish name.
KLIMAT_ROWS = (
    '"249190560","JABŁONKA","2025","06","01",26.5,,8.3,,16.6,,,"8",1.5,,"W",,"9"\n'
    '"249190560","JABŁONKA","2025","06","02",26.6,,11.8,,19.1,,,"8",14.4,,"W",,"9"\n'
)

# A synop-daily (s_d, 65-column) row with old-style decimals (-.4, .0) and
# quoted empty status fields, as seen in the 2016 per-station files.
_SYNOP_HEAD = '"354150100","KOŁOBRZEG","2016","01","01",-.4,"",-2.5,"",-1.9,"",-3.2,"",1.1,"","W",0'
_SYNOP_TAIL = ',"9"' * 48  # pad remaining columns to reach 65
SYNOP_ROW = _SYNOP_HEAD + _SYNOP_TAIL + "\n"


def make_zip(members: dict[str, str]) -> bytes:
    """Build an in-memory zip whose members are cp1250-encoded CSV text."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for name, text in members.items():
            zf.writestr(name, text.encode(SOURCE_ENCODING))
    return buf.getvalue()


@pytest.fixture
def klimat_zip_bytes() -> bytes:
    return make_zip({"k_d_06_2025.csv": KLIMAT_ROWS})


@pytest.fixture
def synop_zip_bytes() -> bytes:
    # Mirrors a 2016 per-station archive: both the main and term members.
    return make_zip(
        {
            "s_d_100_2016.csv": SYNOP_ROW,
            "s_d_t_100_2016.csv": SYNOP_ROW,  # term member (should be skipped)
        }
    )


@pytest.fixture
def klimat_zip_file(tmp_path: Path, klimat_zip_bytes: bytes) -> Path:
    p = tmp_path / "k_d_06_2025.zip"
    p.write_bytes(klimat_zip_bytes)
    return p


@pytest.fixture
def synop_zip_file(tmp_path: Path, synop_zip_bytes: bytes) -> Path:
    p = tmp_path / "2016_100_s.zip"
    p.write_bytes(synop_zip_bytes)
    return p
