"""Turn a raw string DataFrame into a stable, tidy, typed table.

This is the heart of the package. It fixes the year-to-year drift observed in
the real data:

* decimals like ``-.4`` / ``.0`` (missing leading zero);
* quoted vs unquoted empty cells;
* status codes 8 (no measurement) / 9 (no phenomenon) leaking in as values;
* fixed-width space padding in station names;
* columns present in some years and absent in others.

Dtypes are taken from the canonical schema, never inferred.

Standardization is expressed as an ordered list of small transform steps run in
sequence, so adding schemas or transforms stays painless.
"""

import re
from dataclasses import dataclass

import numpy as np
import pandas as pd

from .canonical import get_schema_by_code
from .config import StandardizationConfig
from .constants import (
    STATUS_NO_MEASUREMENT,
    STATUS_NO_PHENOMENON,
)
from .models import ColumnSpec

_LEADING_DOT_RE = re.compile(r"^(-?)\.(\d)")
_MISSING_STATUS = {STATUS_NO_MEASUREMENT, STATUS_NO_PHENOMENON}


# --- cell-level helpers ------------------------------------------------------
def _fix_decimal(value: str) -> str:
    """Normalize IMGW decimals: '-.4' -> '-0.4', '.0' -> '0.0'."""
    return _LEADING_DOT_RE.sub(r"\g<1>0.\2", value.strip())


def _coerce_numeric(series: pd.Series, dtype: str, normalize_decimals: bool) -> pd.Series:
    cleaned = series.astype(str).str.strip().str.strip('"')
    if normalize_decimals:
        cleaned = cleaned.map(_fix_decimal)
    cleaned = cleaned.replace({"": np.nan})
    numeric = pd.to_numeric(cleaned, errors="coerce")
    if dtype.startswith(("Int", "int")):
        return numeric.round().astype("Int64").astype(dtype)
    return numeric.astype(dtype)


def _clean_string(series: pd.Series, strip: bool) -> pd.Series:
    out = series.astype("string").str.strip('"')
    if strip:
        out = out.str.strip()
    return out


# --- pipeline context + steps ------------------------------------------------
@dataclass
class _Ctx:
    """Mutable context threaded through the transform steps."""

    raw: pd.DataFrame
    schema: list[ColumnSpec]
    config: StandardizationConfig
    out: pd.DataFrame


def _step_typed_columns(ctx: _Ctx) -> None:
    """Coerce every measurement/key column to its canonical dtype."""
    for spec in ctx.schema:
        if spec.is_status:
            continue
        if spec.code in ctx.raw.columns:
            src = ctx.raw[spec.code]
        else:
            src = pd.Series([pd.NA] * len(ctx.raw), index=ctx.raw.index)
        if spec.dtype in ("string", "category"):
            cleaned = _clean_string(src, ctx.config.strip_strings)
            ctx.out[spec.code] = cleaned.astype("category") if spec.dtype == "category" else cleaned
        else:
            ctx.out[spec.code] = _coerce_numeric(src, spec.dtype, ctx.config.normalize_decimals)


def _step_status_to_nan(ctx: _Ctx) -> None:
    """Blank out measurement values whose paired status is 8/9."""
    if not ctx.config.status_to_nan:
        return
    for spec in ctx.schema:
        if spec.is_status or not spec.status_col or spec.status_col not in ctx.raw.columns:
            continue
        status = ctx.raw[spec.status_col].astype(str).str.strip().str.strip('"')
        ctx.out.loc[status.isin(_MISSING_STATUS), spec.code] = pd.NA


def _step_keep_status(ctx: _Ctx) -> None:
    """Optionally preserve raw status columns as '<CODE>_status'."""
    if not ctx.config.keep_status:
        return
    for spec in ctx.schema:
        if spec.is_status and spec.code in ctx.raw.columns:
            ctx.out[f"{spec.code}_status"] = _clean_string(ctx.raw[spec.code], True)


def _step_datetime(ctx: _Ctx) -> None:
    """Insert a 'datetime' column assembled from the available date parts.

    * daily: ROK + MC + DZ
    * term:  ROK + MC + DZ + GG (hour)
    * monthly: ROK + MC (first of month)
    """
    if not ctx.config.add_datetime:
        return
    cols = ctx.out.columns
    if not {"ROK", "MC"}.issubset(cols):
        return
    parts = {
        "year": ctx.out["ROK"],
        "month": ctx.out["MC"],
        "day": ctx.out["DZ"] if "DZ" in cols else 1,
    }
    if "GG" in cols:
        parts["hour"] = ctx.out["GG"]
    ctx.out.insert(0, "datetime", pd.to_datetime(parts, errors="coerce"))


def _step_english_aliases(ctx: _Ctx) -> None:
    """Rename IMGW codes to English aliases where defined."""
    if not ctx.config.english_aliases:
        return
    aliases = {c.code: c.english_alias for c in ctx.schema if c.english_alias and not c.is_status}
    ctx.out.rename(columns=aliases, inplace=True)


#: Ordered transform pipeline. Order matters: type -> status -> keep -> dt -> alias.
_STEPS = (
    _step_typed_columns,
    _step_status_to_nan,
    _step_keep_status,
    _step_datetime,
    _step_english_aliases,
)


def standardize(df: pd.DataFrame, schema_code: str, config: StandardizationConfig) -> pd.DataFrame:
    """Standardize one parsed CSV member to its canonical schema.

    :param df: Raw, all-string table as read from one CSV member.
    :param schema_code: Member schema code, e.g. ``"s_d"``, ``"s_d_t"``,
        ``"o_d"``, ``"s_m_d"``.
    :param config: Options controlling the cleaning steps.
    :returns: A cleaned, typed table following the canonical schema.
    :rtype: pandas.DataFrame
    """
    schema = get_schema_by_code(schema_code)
    ctx = _Ctx(raw=df, schema=schema, config=config, out=pd.DataFrame(index=df.index))
    for step in _STEPS:
        step(ctx)
    return ctx.out


def canonical_columns(schema_code: str) -> list[ColumnSpec]:
    """Return the measurement/key specs that survive standardization."""
    return [c for c in get_schema_by_code(schema_code) if not c.is_status]
