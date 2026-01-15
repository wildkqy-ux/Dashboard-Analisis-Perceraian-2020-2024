import streamlit as st
import pandas as pd
import plotly.express as px

# ---------------------------------------------------------
# PAGE CONFIG
# ---------------------------------------------------------
st.set_page_config(page_title="Dashboard Perceraian Jawa Timur", layout="wide")

st.title("💔 Dashboard Perceraian Jawa Timur")
st.markdown("Analisis perceraian berdasarkan Kabupaten/Kota dan faktor penyebab (2020–2024).")


# ---------------------------------------------------------
# LOAD DATA (bersihkan semua angka)
# ---------------------------------------------------------
@st.cache_data
def load_data():
    df = pd.read_excel("data.xlsx")
    df.columns = df.columns.str.strip()

    kolom_total = "Fakor Perceraian - Jumlah"

    faktor_cols = [
        c for c in df.columns
        if c.startswith("Fakor Perceraian -") and c != kolom_total
    ]

    # Bersihkan angka: hilangkan ".", "-", "..."
    for c in faktor_cols + [kolom_total]:
        df[c] = df[c].astype(str).str.replace(r"[^0-9]", "", regex=True)
        df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0).astype(int)

    df["Nikah"] = pd.to_numeric(
        df["Nikah"].astype(str).str.replace(r"[^0-9]", "", regex=True),
        errors="coerce"
    ).fillna(0).astype(int)

    df["Tahun"] = pd.to_numeric(df["Tahun"], errors="coerce").astype(int)

    return df, kolom_total, faktor_cols


df, kolom_total, faktor_cols = load_data()


# ---------------------------------------------------------
# SIDEBAR FILTER
# ---------------------------------------------------------
st.sidebar.header("🔍 Filter Data")

pilih_tahun = st.sidebar.multiselect(
    "Pilih Tahun",
    sorted(df["Tahun"].unique()),
    default=sorted(df["Tahun"].unique())
)

pilih_kota = st.sidebar.multiselect(
    "Pilih Kabupaten/Kota",
    sorted(df["Kabupaten/Kota"].unique()),
    default=sorted(df["Kabupaten/Kota"].unique())
)

pilih_faktor = st.sidebar.multiselect(
    "Pilih Faktor Penyebab",
    faktor_cols,
    default=faktor_cols
)

df_sel = df[
    df["Tahun"].isin(pilih_tahun) &
    df["Kabupaten/Kota"].isin(pilih_kota)
]

if df_sel.empty:
    st.warning("⚠ Tidak ada data yang cocok.")
    st.stop()


# ---------------------------------------------------------
# KPI SUMMARY
# ---------------------------------------------------------
st.subheader("📌 Ringkasan Utama")

col1, col2, col3, col4 = st.columns(4)

total_cerai = df_sel[kolom_total].sum()
rerata = df_sel[kolom_total].mean()

tahun_top = df_sel.groupby("Tahun")[kolom_total].sum().idxmax()

if pilih_faktor:
    faktor_sum = df_sel[pilih_faktor].sum()
    faktor_dominan = faktor_sum.idxmax() if faktor_sum.sum() > 0 else "-"
else:
    faktor_dominan = "-"

col1.metric("Total Perceraian", f"{total_cerai:,.0f}")
col2.metric("Rata-rata per Kota", f"{rerata:,.0f}")
col3.metric("Tahun Tertinggi", tahun_top)
col4.metric("Faktor Dominan", faktor_dominan)

st.markdown("---")


# ---------------------------------------------------------
# TREN TOTAL CERAI + TOTAL NIKAH PER TAHUN
# ---------------------------------------------------------
st.subheader("📈 Tren Total Perceraian & Total Pernikahan per Tahun")

df_tren_cerai = df_sel.groupby("Tahun")[kolom_total].sum().reset_index()
df_tren_nikah = df_sel.groupby("Tahun")["Nikah"].sum().reset_index()

df_tren = df_tren_cerai.merge(df_tren_nikah, on="Tahun")
df_tren.columns = ["Tahun", "Total Perceraian", "Total Pernikahan"]

df_melt = df_tren.melt(
    id_vars="Tahun",
    value_vars=["Total Perceraian", "Total Pernikahan"],
    var_name="Kategori",
    value_name="Jumlah"
)

fig_tren = px.line(
    df_melt,
    x="Tahun",
    y="Jumlah",
    color="Kategori",
    markers=True,
    title="Tren Total Perceraian & Total Pernikahan per Tahun"
)

fig_tren.update_xaxes(dtick=1, type="category")

st.plotly_chart(fig_tren, use_container_width=True)


# ---------------------------------------------------------
# TREN FAKTOR PENYEBAB (TOP 3 + LAINNYA)
# ---------------------------------------------------------
st.subheader("📊 Tren Faktor Penyebab (Top 3 + Faktor Lainnya)")

total_faktor = df_sel[pilih_faktor].sum().sort_values(ascending=False)

top3 = total_faktor.head(3).index.tolist()
lainnya = [f for f in pilih_faktor if f not in top3]

df_faktor = df_sel.groupby("Tahun")[top3 + lainnya].sum().reset_index()
df_faktor["Faktor Lainnya"] = df_faktor[lainnya].sum(axis=1)

viz = top3 + ["Faktor Lainnya"]

df_melt_f = df_faktor.melt(
    id_vars="Tahun",
    value_vars=viz,
    var_name="Faktor",
    value_name="Jumlah"
)

fig_faktor = px.line(
    df_melt_f,
    x="Tahun",
    y="Jumlah",
    color="Faktor",
    markers=True,
    title="Tren Faktor Penyebab (Top 3 + Faktor Lainnya)"
)

fig_faktor.update_xaxes(dtick=1, type="category")

st.plotly_chart(fig_faktor, use_container_width=True)


# ---------------------------------------------------------
# RANKING KOTA
# ---------------------------------------------------------
st.subheader("🏙️ Ranking Kabupaten/Kota berdasarkan Jumlah Perceraian")

df_rank = df_sel.groupby("Kabupaten/Kota")[kolom_total].sum().sort_values().reset_index()

fig_rank = px.bar(
    df_rank,
    x=kolom_total,
    y="Kabupaten/Kota",
    orientation="h",
    color=kolom_total,
    color_continuous_scale="Reds"
)

st.plotly_chart(fig_rank, use_container_width=True)


# ---------------------------------------------------------
# PIE CHART (TOP 3 + LAINNYA)
# ---------------------------------------------------------
st.subheader("🧩 Komposisi Faktor Penyebab (Top 3 + Lainnya)")

nilai_lain = df_sel[lainnya].sum().sum() if lainnya else 0

pie_df = pd.DataFrame({
    "Faktor": top3 + ["Faktor Lainnya"],
    "Jumlah": list(total_faktor[top3]) + [nilai_lain]
})

fig_pie = px.pie(
    pie_df,
    values="Jumlah",
    names="Faktor",
    hole=0.45,
    title="Proporsi Faktor Penyebab (Top 3 + Lainnya)"
)

st.plotly_chart(fig_pie, use_container_width=True)


# ---------------------------------------------------------
# SCATTER PLOT (TOTAL PER KOTA) — 1 TITIK PER KOTA
# ---------------------------------------------------------
st.subheader("📌 Scatter Plot: Ekonomi vs Pertengkaran (Total per Kota)")

kol_eko = "Fakor Perceraian - Ekonomi"
kol_pert = "Fakor Perceraian - Perselisihan dan Pertengkaran Terus Menerus"

df_sct = df_sel.groupby("Kabupaten/Kota")[
    [kol_eko, kol_pert, kolom_total]
].sum().reset_index()

fig_sct = px.scatter(
    df_sct,
    x=kol_eko,
    y=kol_pert,
    size=kolom_total,
    color="Kabupaten/Kota",
    hover_name="Kabupaten/Kota",
    title="Hubungan Ekonomi vs Pertengkaran (Total Per Kota)",
    size_max=50
)

st.plotly_chart(fig_sct, use_container_width=True)


# ---------------------------------------------------------
# RAW DATA
# ---------------------------------------------------------
with st.expander("📄 Lihat Data Mentah"):
    st.dataframe(df_sel)
