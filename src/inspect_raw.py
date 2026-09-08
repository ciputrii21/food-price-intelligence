import pandas as pd
from pathlib import Path 

RAW_DIR = Path(__file__).resolve().parents[1] / "data" / "raw"

files = sorted(RAW_DIR.glob("*.xlsx"))
if not files:
    raise SystemExit(f"Tidak ada file .xlsx di {RAW_DIR}")

path = files[0]
print(f"File    : {path.name}")
print(f"Ukuran  : {path.stat().st_size / 1024:.1f} KB")

sheets = pd.read_excel(path, sheet_name=None, header=None, engine="openpyxl")
print(f"Jumlah sheet: {len(sheets)}")
print(f"Nama sheet: {list(sheets.keys())}\n")

for name, df in sheets.items():
    print("=" * 70)
    print(f"SHEET: {name}  ->  {df.shape[0]} baris x {df.shape[1]} kolom")
    print("=" * 70)

    print("\n--- 15 baris pertama, 8 kolom pertama (mentah) ---")
    with pd.option_context("display.max_column", None, "display.width", 200):
        print(df.iloc[:15, -8:].to_string())
    
    print("\n--- Jumlah sel kosong per baris (10 baris pertama) ---")
    print(df.iloc[:10].isna().sum(axis=1).to_string())
    print()