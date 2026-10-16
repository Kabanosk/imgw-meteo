# Command-line interface

Install the CLI extra to get the `imgw-meteo` command:

```bash
pip install imgw-meteo[cli]
```

Running `imgw-meteo` without the extra prints a clear hint instead of failing
with an import error.

## Commands

### `stations` — search the station registry

```bash
imgw-meteo stations                      # list all
imgw-meteo stations --name "Kraków"      # filter by name (diacritic-insensitive)
```

### `years` — what's available

```bash
imgw-meteo years --freq daily --type synop
imgw-meteo years --freq monthly --type opad
```

### `fetch` — download and standardize

```bash
# print the first rows to the terminal
imgw-meteo fetch --freq daily --type klimat --year 2025 --month 6

# one station, write to Parquet
imgw-meteo fetch --freq daily --type synop --year 2016 --station 100 --output out.parquet

# write to CSV (UTF-8)
imgw-meteo fetch --freq monthly --type opad --year 2024 --output opad_2024.csv
```

`--freq` accepts `daily` / `monthly` / `term` (or the Polish directory names).
`--type` accepts `synop` / `klimat` / `opad`.
```
