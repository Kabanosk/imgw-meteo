# Contributing

Thanks for your interest in improving `imgw-meteo`!

## Development setup

The project uses [uv](https://docs.astral.sh/uv/).

```bash
git clone https://github.com/Kabanosk/imgw-meteo
cd imgw-meteo
uv venv
uv pip install -e ".[dev,cli]"
# optional, for the ML tests:
uv pip install torch --index-url https://download.pytorch.org/whl/cpu
```

## Checks

All of these run in CI; run them locally before opening a PR:

```bash
uv run ruff check src/ tests/          # lint
uv run ruff format --check src/ tests/ # formatting
uv run mypy src/                       # type check
uv run pytest --cov=imgw_meteo         # tests + coverage
```

The test suite is fully offline (network is mocked), so it is fast and
deterministic.

## Building the docs

```bash
uv pip install -e ".[docs]"
uv run sphinx-build -b html -W docs docs/_build/html
# open docs/_build/html/index.html
```

## Adding a data schema

Canonical schemas live in `src/imgw_meteo/canonical.py`, keyed by member code
(e.g. `s_d`, `s_d_t`). Each is transcribed from the IMGW `format.txt` /
`nagłówek.csv` for that dataset and verified against a real sample. When adding
one, include a test asserting the column count matches the source header.

## Commit & PR guidelines

- Keep commits focused and the test suite green.
- Add or update tests for behavior changes.
- Update `CHANGELOG.md` under an "Unreleased" section.
