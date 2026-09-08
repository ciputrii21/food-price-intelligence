# Indonesian Food Price Intelligence

End-to-end data pipeline for Indonesian staple food prices: raw ingestion,
cleaning, analysis, dashboard, and price forecasting.

## Data source

[PIHPS Nasional](https://www.bi.go.id/hargapangan) - Bank Indonesia.
Daily traditional market prices, Kota Manado, North Sulawesi.
Period: January 2025 - September 2026.

Raw data is not committed to this repository. See "How to get the data" below.

## Data quality notes

Findings from inspecting the raw export:

- Prices are stored as text with comma thousand separators (`16,400`)
- Missing values are written as `-`, not empty cells, so a naive
  null check reports zero missing data
- Dates in the header contain internal spaces (`01/ 01/ 2025`)
- The table mixes two levels: categories (Roman numerals) are averages
  of their variants (Arabic numerals). Mixing them double-counts.
- Commodity names contain inconsistent trailing whitespace
- Cabai Merah Besar is not surveyed in Kota Manado

## Project structure
data/raw/ Original Excel export (not committed)
data/processed/ Cleaned long-format data
src/ Pipeline scripts
notebooks/ Exploration
outputs/ Charts and reports


## How to get the data

1. Go to https://www.bi.go.id/hargapangan
2. Tabel Harga > Pasar Tradisional > Berdasarkan Daerah
3. Select all commodities, Sulawesi Utara, Kota Manado, Laporan Harian
4. Set the date range and download
5. Save to `data/raw/`

## Setup

```bash
pip install pandas openpyxl
python3 src/clean_data.py
```

## Status

Work in progress.