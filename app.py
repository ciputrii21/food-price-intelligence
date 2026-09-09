"""
Dashboard Harga Pangan — Kota Manado
Sumber data: PIHPS Bank Indonesia, pasar tradisional.

Jalankan dengan:
    streamlit run app.py
"""

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

# ---------------------------------------------------------------- konfigurasi

st.set_page_config(
    page_title="Harga Pangan Manado",
    page_icon="🌶️",
    layout="wide",
)

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data" / "processed" / "harga_pangan_manado_long.csv"

WARNA_UTAMA = "#2c3e50"
WARNA_AKSEN = "#c0392b"
WARNA_NETRAL = "#95a5a6"

JENDELA = 30
AMBANG = 4.0
MAD_MIN = 0.5
PERUBAHAN_MIN = 5.0


# ------------------------------------------------------------------ pemuatan

@st.cache_data
def muat_data():
    df = pd.read_csv(DATA, parse_dates=["tanggal"])
    varian = df[df["level"] == "varian"].copy()
    varian["harga"] = varian["harga"].astype(float)
    return varian.sort_values(["komoditas", "tanggal"])


@st.cache_data
def hitung_volatilitas(varian):
    ringkas = varian.groupby("komoditas")["harga"].agg(
        rata="mean", terendah="min", tertinggi="max", stdev="std"
    )
    ringkas["cv"] = ringkas["stdev"] / ringkas["rata"]
    return ringkas.sort_values("cv", ascending=False)


@st.cache_data
def hitung_anomali(varian):
    d = varian.copy()

    g = d.groupby("komoditas")["harga"]
    d["perubahan_pct"] = g.transform(lambda s: s.pct_change() * 100)

    p = d.groupby("komoditas")["perubahan_pct"]
    d["median_roll"] = p.transform(
        lambda s: s.rolling(JENDELA, min_periods=10).median()
    )

    d["dev_abs"] = (d["perubahan_pct"] - d["median_roll"]).abs()
    d["mad_roll"] = d.groupby("komoditas")["dev_abs"].transform(
        lambda s: s.rolling(JENDELA, min_periods=10).median()
    )

    d["skala"] = (d["mad_roll"] * 1.4826).clip(lower=MAD_MIN)
    d["skor"] = (d["perubahan_pct"] - d["median_roll"]) / d["skala"]
    d["anomali"] = (d["skor"].abs() > AMBANG) & (
        d["perubahan_pct"].abs() >= PERUBAHAN_MIN
    )
    return d


def format_rp(x, _=None):
    return "{:,.0f}".format(x)


# ---------------------------------------------------------------------- data

varian = muat_data()
volatilitas = hitung_volatilitas(varian)
anomali = hitung_anomali(varian)

daftar_komoditas = sorted(varian["komoditas"].unique())
tanggal_awal = varian["tanggal"].min()
tanggal_akhir = varian["tanggal"].max()

if "Cabai Rawit Merah" in daftar_komoditas:
    INDEKS_AWAL = daftar_komoditas.index("Cabai Rawit Merah")
else:
    INDEKS_AWAL = 0


# -------------------------------------------------------------------- header

st.title("Harga Pangan Kota Manado")
st.caption(
    "Sumber: PIHPS Bank Indonesia, pasar tradisional. "
    "Periode {:%d %b %Y} – {:%d %b %Y}. "
    "Pasar tidak disurvei pada akhir pekan.".format(tanggal_awal, tanggal_akhir)
)

k1, k2, k3, k4 = st.columns(4)
k1.metric("Komoditas", len(daftar_komoditas))
k2.metric("Hari survei", varian["tanggal"].nunique())
k3.metric("Observasi", "{:,}".format(len(varian)))
k4.metric("Anomali terdeteksi", int(anomali["anomali"].sum()))

st.divider()

tab_tren, tab_vol, tab_anom = st.tabs(
    ["Tren harga", "Volatilitas", "Deteksi anomali"]
)


# ----------------------------------------------------------------- tab: tren

with tab_tren:
    kiri, kanan = st.columns([1, 3])

    with kiri:
        pilihan = st.selectbox("Komoditas", daftar_komoditas, index=INDEKS_AWAL)
        rentang = st.select_slider(
            "Rentang waktu",
            options=["3 bulan", "6 bulan", "1 tahun", "Semua"],
            value="Semua",
        )

    d = varian[varian["komoditas"] == pilihan].sort_values("tanggal")

    if rentang != "Semua":
        hari = {"3 bulan": 90, "6 bulan": 180, "1 tahun": 365}[rentang]
        batas = tanggal_akhir - pd.Timedelta(days=hari)
        d = d[d["tanggal"] >= batas]

    with kanan:
        harga_akhir = d["harga"].iloc[-1]
        harga_awal = d["harga"].iloc[0]
        selisih = (harga_akhir - harga_awal) / harga_awal * 100

        m1, m2, m3 = st.columns(3)
        m1.metric("Harga terakhir", "Rp {:,.0f}".format(harga_akhir))
        m2.metric("Perubahan periode", "{:+.1f}%".format(selisih))
        m3.metric(
            "Rentang",
            "Rp {:,.0f} – {:,.0f}".format(d["harga"].min(), d["harga"].max()),
        )

    fig, ax = plt.subplots(figsize=(12, 4.5))
    ax.plot(d["tanggal"], d["harga"], linewidth=1.4, color=WARNA_UTAMA)
    ax.fill_between(d["tanggal"], d["harga"], alpha=0.08, color=WARNA_UTAMA)
    ax.set_ylabel("Harga (Rp/kg)")
    ax.yaxis.set_major_formatter(format_rp)
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis="y", alpha=0.3)
    plt.tight_layout()
    st.pyplot(fig)

    cv = volatilitas.loc[pilihan, "cv"]
    peringkat = list(volatilitas.index).index(pilihan) + 1
    st.info(
        "**{}** menempati peringkat volatilitas ke-{} dari {} komoditas "
        "(CV {:.3f}). Harga bergerak antara Rp {:,.0f} dan Rp {:,.0f} "
        "sepanjang periode penuh.".format(
            pilihan,
            peringkat,
            len(volatilitas),
            cv,
            volatilitas.loc[pilihan, "terendah"],
            volatilitas.loc[pilihan, "tertinggi"],
        )
    )


# ----------------------------------------------------------- tab: volatilitas

with tab_vol:
    st.subheader("Komoditas mana yang paling bergejolak?")
    st.write(
        "Diukur dengan *coefficient of variation* — standar deviasi dibagi "
        "rata-rata. Ukuran ini membuat perbandingan adil antar komoditas "
        "dengan level harga berbeda."
    )

    fig, ax = plt.subplots(figsize=(10, 7))
    warna = [
        WARNA_AKSEN if v > 0.2 else WARNA_NETRAL for v in volatilitas["cv"]
    ]
    ax.barh(volatilitas.index, volatilitas["cv"], color=warna)
    ax.invert_yaxis()
    ax.set_xlabel("Coefficient of variation")
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis="x", alpha=0.3)
    plt.tight_layout()
    st.pyplot(fig)

    st.info(
        "Terlihat pemisahan tajam. Cabai dan bawang berada jauh di atas "
        "sisanya, sementara gula dan beras nyaris datar. Dugaan penyebabnya "
        "adalah perbedaan antara komoditas dengan intervensi harga "
        "(beras, gula, minyak goreng) dan komoditas hortikultura yang mudah "
        "rusak sehingga tidak bisa ditimbun."
    )

    with st.expander("Lihat tabel lengkap"):
        tampil = pd.DataFrame({
            "Komoditas": volatilitas.index,
            "Rata-rata": volatilitas["rata"].map("{:,.0f}".format),
            "Terendah": volatilitas["terendah"].map("{:,.0f}".format),
            "Tertinggi": volatilitas["tertinggi"].map("{:,.0f}".format),
            "CV": volatilitas["cv"].map("{:.3f}".format),
        })
        st.dataframe(tampil, width="stretch", hide_index=True)


# -------------------------------------------------------------- tab: anomali

with tab_anom:
    st.subheader("Kapan harga bergerak tidak wajar?")
    st.write(
        "Metode: perubahan harian dibandingkan dengan median dan MAD dari "
        "30 hari terakhir. Sebuah titik ditandai bila skornya melebihi {} "
        "**dan** perubahannya minimal {:.0f}%. Syarat kedua memastikan yang "
        "terdeteksi adalah pergerakan yang berarti, bukan riak kecil yang "
        "kebetulan menonjol secara statistik.".format(AMBANG, PERUBAHAN_MIN)
    )

    pilihan_a = st.selectbox(
        "Komoditas",
        daftar_komoditas,
        index=INDEKS_AWAL,
        key="anomali_pilihan",
    )

    da = anomali[anomali["komoditas"] == pilihan_a].sort_values("tanggal")
    tanda = da[da["anomali"]]

    fig, ax = plt.subplots(figsize=(12, 4.5))
    ax.plot(
        da["tanggal"], da["harga"], linewidth=1.1,
        color=WARNA_NETRAL, label="Harga",
    )
    ax.scatter(
        tanda["tanggal"], tanda["harga"],
        color=WARNA_AKSEN, s=45, zorder=5, label="Anomali",
    )
    ax.set_ylabel("Harga (Rp/kg)")
    ax.yaxis.set_major_formatter(format_rp)
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis="y", alpha=0.3)
    ax.legend(frameon=False)
    plt.tight_layout()
    st.pyplot(fig)

    st.warning(
        "Metode ini mendeteksi **percepatan perubahan**, bukan level harga. "
        "Puncak tertinggi belum tentu ditandai bila kenaikannya bertahap."
    )

    if len(tanda) > 0:
        st.write(
            "**{} anomali terdeteksi pada {}**".format(len(tanda), pilihan_a)
        )
        tabel = pd.DataFrame({
            "Tanggal": tanda["tanggal"].dt.strftime("%d %b %Y"),
            "Harga": tanda["harga"].map("{:,.0f}".format),
            "Perubahan (%)": tanda["perubahan_pct"].map("{:+.2f}".format),
            "Skor": tanda["skor"].map("{:.2f}".format),
        })
        st.dataframe(tabel, width="stretch", hide_index=True)
    else:
        st.write("Tidak ada anomali terdeteksi pada komoditas ini.")
