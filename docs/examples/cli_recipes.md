# CLI recipes

```bash
pip install imgw-meteo[cli]
```

## Find a station code

```bash
imgw-meteo stations --name "Kraków"
```

## Discover available years

```bash
imgw-meteo years --freq daily --type synop
imgw-meteo years --freq term  --type klimat
```

## Peek at data in the terminal

```bash
imgw-meteo fetch --freq daily --type klimat --year 2025 --month 6
```

## Save a month to Parquet

```bash
imgw-meteo fetch --freq daily --type synop --year 2025 --month 6 --output synop_2025_06.parquet
```

## One station to CSV

```bash
imgw-meteo fetch --freq daily --type synop --year 2016 --station 100 --output kolobrzeg_2016.csv
```

## Monthly precipitation totals

```bash
imgw-meteo fetch --freq monthly --type opad --year 2024 --output opad_2024.parquet
```

## Shell loop over several years

```bash
for y in 2021 2022 2023 2024 2025; do
  imgw-meteo fetch --freq daily --type synop --year "$y" --month 7 --output "synop_july_${y}.parquet"
done
```
