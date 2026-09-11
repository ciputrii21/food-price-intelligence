# Indonesian Food Price Intelligence

End-to-end data pipeline for Indonesian staple food prices: raw ingestion, cleaning, analysis, anomaly detection, forecasting, and an interactive dashboard.

**[Live dashboard](https://food-price-intelligence.streamlit.app/)** · **[Full report (PDF, Indonesian)](report/Laporan_Harga_Pangan_Manado_FINAL.pdf)**

## Data source

[PIHPS Nasional](https://www.bi.go.id/hargapangan) - Bank Indonesia. Daily traditional market prices, Kota Manado, North Sulawesi. Period: January 2025 - September 2026.

440 survey days, 20 commodity variants, 13,200 rows after cleaning.

Raw data is not committed to this repository. See "How to get the data" below.

## Data quality notes

Findings from inspecting the raw export:

* Prices are stored as text with comma thousand separators (`16,400`)
* Missing values are written as `-`, not empty cells, so a naive null check reports zero missing data
* Dates in the header contain internal spaces (`01/ 01/ 2025`)
* The table mixes two levels: categories (Roman numerals) are averages of their variants (Arabic numerals). Mixing them double-counts.
* Commodity names contain inconsistent trailing whitespace
* Cabai Merah Besar is not surveyed in Kota Manado
* Markets are not surveyed on weekends, so the series is not equally spaced

## Key findings

**Volatility splits into two clear groups.** Chili and shallot sit far above everything else (coefficient of variation 0.438 for Cabai Merah Keriting). Rice and sugar barely move. The likely reason is that the second group has price intervention and can be stored, while horticultural products spoil fast and cannot buffer supply shocks.

**No monthly seasonal pattern was found.** The 2025 peak falls in March, the 2026 peak in September. With only two annual cycles and the second one incomplete, this is "not proven" rather than "proven absent".

**Prices have short memory.** Lag-1 correlation is 0.939 but drops to 0.343 at 14 days and turns negative at 30 days.

**Anomaly detection took three attempts.** A global z-score flagged rice and sugar as the most anomalous commodities, which is backwards. Rolling MAD flagged 8.76% of all observations, far too many, because prices often stay flat for days and drive MAD toward zero. The final version adds a floor on the MAD scale and a materiality threshold, landing at 1.85%.

**Gradient boosting did not beat the naive baseline.** Predicting "tomorrow equals today" gives MAPE 8.09%. The best model configuration reached 8.39%. Tree models cannot extrapolate beyond the training range, and with lag-1 correlation at 0.939, roughly 88% of tomorrow's variance is already explained by today's price. The report documents this in full rather than tuning until the numbers look good.

## Project structure

```
data/raw/          Original Excel export (not committed)
data/processed/    Cleaned long-format data
src/               Pipeline scripts
notebooks/         Exploration and modeling
report/            Full written report (PDF)
outputs/           Charts (not committed)
app.py             Streamlit dashboard
```

## How to get the data

1. Go to https://www.bi.go.id/hargapangan
2. Tabel Harga > Pasar Tradisional > Berdasarkan Daerah
3. Select all commodities, Sulawesi Utara, Kota Manado, Laporan Harian
4. Set the date range and download
5. Save to `data/raw/`

## Setup

```bash
pip install -r requirements.txt
python3 src/clean_data.py
streamlit run app.py
```

## Notebooks

* `notebooks/01_eksplorasi.ipynb` - price trends, volatility ranking, seasonality test, lag correlation, anomaly detection
* `notebooks/02_forecasting.ipynb` - baselines, three model configurations, permutation importance, diagnosis

Both notebooks include written commentary on why each failed approach failed.

## Limitations

One city, one market type. Twenty months of data with the second year incomplete. Model evaluation covers a single commodity, and the test period contains the largest price spike in the whole series, which was still ongoing when the data was pulled.

## Next steps

Extend to multiple cities for spatial comparison, automate the daily data pull, add automated data quality tests to the pipeline, and test whether exogenous variables (rainfall, religious holidays, production data) improve the forecast.
