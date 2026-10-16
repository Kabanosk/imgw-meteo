# Changelog

All notable changes to this project are documented here. The format is based on
[Keep a Changelog](https://keepachangelog.com/), and the project follows
[Semantic Versioning](https://semver.org/).

## [0.1.0] — 2026-10-16

First public release.

### Added

- **Configured client API**: `IMGWClient` holding cache/network and
  standardization config (Pydantic `ClientConfig` / `StandardizationConfig`),
  producing reusable `Dataset` selection handles via `.select(...)`.
- **Full data coverage** for all published IMGW meteorological combinations:
  daily, monthly and term (sub-daily) frequencies across synop, klimat and opad
  station types. Term add-on members (e.g. `s_d_t`) merge onto primary rows via
  `include_term`.
- **Standardization** into a stable, typed table: cp1250 decoding, decimal
  normalization (`-.4` → `-0.4`), status `8`/`9` → missing, declared dtypes
  (never inferred), assembled `datetime`, whitespace trimming, optional English
  aliases and preserved status columns.
- **Station registry** with diacritic- and case-insensitive search.
- **PyTorch dataloaders** via `Dataset.get_dataloaders(...)`: per-station
  sliding windows, chronological (leakage-free) or random split, train-only
  normalization, and configurable missing-value handling. A framework-agnostic
  windowing core (`imgw_meteo.ml.windowing`) backs it for numpy/JAX/sklearn use.
- **CLI** `imgw-meteo` (via the `[cli]` extra): `stations`, `years`, `fetch`.
- Typed package (ships `py.typed`); documentation site; CI with tests,
  coverage, type checking and docs build.

[0.1.0]: https://github.com/Kabanosk/imgw-meteo/releases/tag/v0.1.0
