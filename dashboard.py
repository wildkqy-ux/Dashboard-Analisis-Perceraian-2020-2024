import streamlit as st
import pandas as pd
import plotly.express as px

# --- Konfigurasi Halaman ---
st.set_page_config(page_title="Dashboard Perceraian Jatim", layout="wide")

# --- Judul dan Deskripsi ---
st.title("💔 Dashboard Analisis Perceraian Jawa Timur")
st.markdown("Analisis faktor-faktor penyebab perceraian di Kabupaten/Kota Jawa Timur (2022-2024).")

# --- Load Data ---
@st.cache_data
def load_data():
    try:
        # Load data
        df = pd.read_csv("data.csv", encoding = 'latin-1')
        
        # --- PERBAIKAN DI SINI ---
        # Hapus baris jika Kota ATAU Tahun kosong
        df = df.dropna(subset=['Kabupaten/Kota', 'Tahun'])
        
        # Sekarang aman untuk convert ke integer
        df['Tahun'] = df['Tahun'].astype(int)
        
        # Rename kolom
        kolom_baru = {
            'Fakor Perceraian - Zina': 'Zina',
            'Fakor Perceraian - Mabuk': 'Mabuk',
            'Fakor Perceraian - Madat': 'Madat',
            'Fakor Perceraian - Judi': 'Judi',
            'Fakor Perceraian - Meninggalkan Salah satu Pihak': 'Ditinggal Pasangan',
            'Fakor Perceraian - Dihukum Penjara': 'Dipenjara',
            'Fakor Perceraian - Poligami': 'Poligami',
            'Fakor Perceraian - Kekerasan Dalam Rumah Tangga': 'KDRT',
            'Fakor Perceraian - Cacat Badan': 'Cacat Badan',
            'Fakor Perceraian - Perselisihan dan Pertengkaran Terus Menerus': 'Pertengkaran Terus Menerus',
            'Fakor Perceraian - Kawin Paksa': 'Kawin Paksa',
            'Fakor Perceraian - Murtad': 'Murtad',
            'Fakor Perceraian - Ekonomi': 'Ekonomi',
            'Fakor Perceraian - Jumlah': 'Total Kasus'
        }
        df = df.rename(columns=kolom_baru)
        return df
        
    except Exception as e:
        # Jika masih error, kita tangkap biar tidak crash total
        st.error(f"Terjadi kesalahan saat memproses data: {e}")
        return pd.DataFrame() # Return dataframe kosong agar tidak crash

df = load_data()

# Cek jika load data gagal/kosong
if df.empty:
    st.warning("Data tidak ditemukan atau kosong. Cek nama file CSV kamu.")
    st.stop()

# --- Sidebar: Filter ---
st.sidebar.header("Filter Data")
pilihan_tahun = st.sidebar.multiselect(
    "Pilih Tahun:",
    options=sorted(df['Tahun'].unique()),
    default=sorted(df['Tahun'].unique())
)

pilihan_kota = st.sidebar.multiselect(
    "Pilih Kabupaten/Kota:",
    options=sorted(df['Kabupaten/Kota'].unique()),
    default=sorted(df['Kabupaten/Kota'].unique())
)

# Filter Data
df_selection = df.query("Tahun == @pilihan_tahun & `Kabupaten/Kota` == @pilihan_kota")

# --- Validasi Data Kosong Setelah Filter ---
if df_selection.empty:
    st.warning("⚠️ Data kosong dengan filter ini. Silakan pilih Tahun dan Kota lain.")
    st.stop()

# --- KPI Utama ---
total_kasus = df_selection['Total Kasus'].sum()
rata_rata = df_selection['Total Kasus'].mean()

# List kolom faktor
faktor_cols = ['Zina', 'Mabuk', 'Madat', 'Judi', 'Ditinggal Pasangan', 
               'Dipenjara', 'Poligami', 'KDRT', 'Cacat Badan', 
               'Pertengkaran Terus Menerus', 'Kawin Paksa', 'Murtad', 'Ekonomi']

# Cari penyebab dominan (handling jika semua 0)
if df_selection[faktor_cols].sum().sum() == 0:
    top_cause = "-"
else:
    top_cause = df_selection[faktor_cols].sum().idxmax()

col1, col2, col3 = st.columns(3)
col1.metric("Total Kasus Perceraian", f"{total_kasus:,.0f}")
col2.metric("Rata-rata per Kota", f"{rata_rata:,.0f}")
col3.metric("Penyebab Dominan", top_cause)

st.markdown("---")

# --- Visualisasi 1: Bar Chart Top 10 ---
st.subheader("📊 Top 10 Wilayah dengan Angka Perceraian Tertinggi")
top_10_cities = df_selection.groupby('Kabupaten/Kota')['Total Kasus'].sum().sort_values(ascending=False).head(10).reset_index()

fig_bar = px.bar(
    top_10_cities, 
    x='Total Kasus', 
    y='Kabupaten/Kota', 
    orientation='h',
    text_auto=True,
    color='Total Kasus',
    color_continuous_scale='Reds'
)
fig_bar.update_layout(yaxis={'categoryorder':'total ascending'})
st.plotly_chart(fig_bar, use_container_width=True)

# --- Visualisasi 2: Pie & Bar Factors ---
st.subheader("🔍 Proporsi Faktor Penyebab")

df_factors = df_selection[faktor_cols].sum().reset_index()
df_factors.columns = ['Faktor', 'Jumlah']
df_factors = df_factors.sort_values(by='Jumlah', ascending=False)

col_chart1, col_chart2 = st.columns(2)

with col_chart1:
    fig_pie = px.pie(
        df_factors.head(5), 
        values='Jumlah', 
        names='Faktor', 
        title='5 Faktor Penyebab Utama',
        hole=0.4
    )
    st.plotly_chart(fig_pie, use_container_width=True)

with col_chart2:
    fig_factor_bar = px.bar(
        df_factors,
        x='Faktor',
        y='Jumlah',
        title='Ranking Seluruh Faktor',
        color='Jumlah'
    )
    st.plotly_chart(fig_factor_bar, use_container_width=True)

# --- Visualisasi 3: Scatter Plot ---
st.subheader("📈 Hubungan Ekonomi vs Pertengkaran")
fig_scatter = px.scatter(
    df_selection,
    x="Ekonomi",
    y="Pertengkaran Terus Menerus",
    size="Total Kasus",
    color="Kabupaten/Kota",
    hover_name="Kabupaten/Kota",
    size_max=60,
    title="Korelasi: Masalah Ekonomi & Pertengkaran"
)
st.plotly_chart(fig_scatter, use_container_width=True)

# --- Data Table ---
with st.expander("Lihat Data Mentah"):
    st.dataframe(df_selection)