import pandas as pd
from pathlib import Path

RAW_DIR = Path(__file__).resolve().parents[1] / "data" / "raw"
path = sorted(RAW_DIR.glob("*.xlsx"))[0]

df = pd.read_excel(path, sheet_name=0, header=None, engine="openpyxl")

print(f"Bentuk: {df.shape[0]} baris x {df.shape[1]} kolom\n")

print("--- Semua baris, 4 kolom pertama ---")
with pd.option_context("display.max_rows", None, "display.width", 200):
    print(df.iloc[:, :4].to_string())

print("\n--- Tipe data kolom 0 dan 1 ---")
for i in [0, 1]:
    print(f"kolom {i}: {df[i].map(type).value_counts().to_dict()}")
