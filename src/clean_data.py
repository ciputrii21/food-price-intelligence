import re
import pandas as pd 
from pathlib import Path 

ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw"
PROC_DIR = ROOT / "data" / "processed"
PROC_DIR.mkdir(parents=True, exist_ok=True)

ROMAN = {
    "I", "II", "III", "IV", "V", "VI", "VII", "VIII", 
    "IX", "X", "XI", "XII", "XIII", "XIV", "XV", "XVI",
    "XVII", "XVIII", "XIX", "XX",
}

def parse_tanggal(nilai):
    """'01/01/2025' -> Timestamp. Hapus semua spasi dulu."""
    teks = re.sub(r"\s+", "", str(nilai))
    return pd.to_datetime(teks, format="%d/%m/%Y", errors="coerce")

def parse_harga(nilai):
    """'16, 400' -> 16400. '-' atau kosong -> NA. """
    teks = str(nilai).strip()
    if teks in {"-", "", "nan", "None", "NaN"}:
        return pd.NA
    angka = re.sub(r"[^\d]", "", teks)
    return int(angka) if angka else pd.NA

def bersihkan(path):
    raw = pd.read_excel(path, sheet_name=0, header=None, engine="openpyxl")

    header = raw.iloc[0]
    body = raw.iloc[1:].reset_index(drop=True)

    #Petakan kolom ke tanggal
    peta_tanggal = {}
    kolom_gagal = []
    for idx in range(2, raw.shape[1]):
        tgl = parse_tanggal(header[idx])
        if pd.isna(tgl):
            kolom_gagal.append((idx, header[idx]))
        else: 
            peta_tanggal[idx] = tgl

    #metadata komoditas
    meta = pd.DataFrame({
        "no": body[0].astype(str).str.strip(),
        "komoditas": body[1].astype(str).str.strip().str.replace(r"\s+", " ", regex=True), 
    })
    meta["level"] = meta["no"].str.upper().isin(ROMAN).map(
        {True: "kategori", False: "varian"}
    )
    meta["kategori"] = meta["komoditas"].where(meta["level"] == "kategori").ffill()

    # ubah wide jadi long
    harga = body[list(peta_tanggal.keys())].copy()
    harga.columns = [peta_tanggal[c] for c in peta_tanggal.keys()]
    harga = pd.concat([meta[["komoditas", "kategori", "level"]], harga], axis=1)

    tidy = harga.melt(
        id_vars=["komoditas", "kategori", "level"],
        var_name="tanggal",
        value_name="harga_mentah",
    )
    tidy["harga"] = tidy["harga_mentah"].map(parse_harga).astype("Int64")
    tidy = tidy.drop(columns=["harga_mentah"])
    tidy = tidy.sort_values(["kategori", "komoditas", "tanggal"]).reset_index(drop=True)

    return tidy, kolom_gagal

def laporan(tidy, kolom_gagal):
    print("=" * 60)
    print("LAPORAN KUALITAS DATA")
    print("=" * 60)

    print(f"\nTotal baris       : {len(tidy):,}")
    print(f"Rentang tanggal     : {tidy['tanggal'].min():%d %b %Y} s/d {tidy['tanggal'].max():%d %b %Y}")
    print(f"Jumlah hari unik    : {tidy['tanggal'].nunique()}")
    print(f"Jumlah kategori     : {tidy[tidy['level'] == 'kategori']['komoditas'].nunique()}")
    print(f"Jumlah varian       : {tidy[tidy['level'] == 'varian']['komoditas'].nunique()}")

    if kolom_gagal:
        print(f"\nKolom tanggal gagal diparse: {len(kolom_gagal)}")
        for idx, nilai in kolom_gagal[:5]:
            print(f" kolom {idx}: {nilai!r}")

    kosong = tidy["harga"].isna().sum()
    print(f"\nHarga kosong      : {kosong:,} ({kosong / len(tidy) * 100:.2f}%)")

    print("\n--- Harga kosong per komoditas (10 teratas) ---")
    per_kom = (
        tidy[tidy["harga"].isna()]
        .groupby("komoditas")
        .size()
        .sort_values(ascending=False)
        .head(10)
    )
    print(per_kom.to_string() if len(per_kom) else" (tidak ada)")

    print("\n--- Ringkasan harga per varian ---")
    ringkas = (
        tidy[tidy["level"] == "varian"]
        .groupby("komoditas")["harga"]
        .agg(["min", "max", "mean", "count"])
        .round(0)
        .astype("Int64")
    )
    with pd.option_context("display.width", 200):
        print(ringkas.to_string())

if __name__ == "__main__":
    path = sorted(RAW_DIR.glob("*.xlsx"))[0]
    print(f"Membaca: {path.name}\n")

    tidy, kolom_gagal = bersihkan(path)
    laporan(tidy, kolom_gagal)

    keluaran = PROC_DIR / "harga_pangan_manado_long.csv"
    tidy.to_csv(keluaran, index=False)
    print(f"\nTersimpan: {keluaran}")
    print(f"Bentuk akhir: {tidy.shape[0]:,} baris x {tidy.shape[1]} kolom")