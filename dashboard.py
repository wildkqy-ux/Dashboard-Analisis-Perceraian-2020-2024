import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Set page configuration
st.set_page_config(page_title="Dashboard Pernikahan dan Perceraian Jawa Timur", 
                   page_icon="", 
                   layout="wide")

# Custom CSS for compact layout
st.markdown("""
<style>
    .block-container {
        padding-top: 1rem;
        padding-bottom: 0rem;
    }
    h1 {
        padding-bottom: 0.5rem;
    }
    h3 {
        padding-top: 0.5rem;
        padding-bottom: 0.3rem;
    }
</style>
""", unsafe_allow_html=True)

# Load data
@st.cache_data
def load_data():
    df = pd.read_excel('data.xlsx')
    # Pastikan kolom Tahun adalah integer
    df['Tahun'] = df['Tahun'].astype(int)
    return df

df = load_data()

# Title
st.title(" Dashboard Pernikahan dan Perceraian Jawa Timur (2020-2024)")

# Sidebar filters
with st.sidebar:
    st.header("🔍 Filter Data")
    years = sorted(df['Tahun'].unique())
    selected_years = st.multiselect("Pilih Tahun", years, default=years)

    regencies = sorted(df['Kabupaten/Kota'].unique())
    selected_regencies = st.multiselect("Pilih Kabupaten/Kota", 
                                        regencies, 
                                        default=regencies,
                                        help="Kosongkan untuk pilih semua")

# Filter data
if not selected_regencies:
    selected_regencies = regencies

filtered_df = df[df['Tahun'].isin(selected_years) & 
                 df['Kabupaten/Kota'].isin(selected_regencies)]

# === SECTION 1: KEY METRICS ===
col1, col2, col3, col4, col5 = st.columns(5)

total_nikah = filtered_df['Nikah'].sum()
total_cerai = filtered_df['Faktor Perceraian - Jumlah'].sum()
rasio = (total_cerai / total_nikah * 100) if total_nikah > 0 else 0
avg_nikah = filtered_df.groupby('Kabupaten/Kota')['Nikah'].sum().mean()
jumlah_wilayah = filtered_df['Kabupaten/Kota'].nunique()

col1.metric("Total Pernikahan", f"{total_nikah:,}")
col2.metric("Total Perceraian", f"{total_cerai:,}")
col3.metric("Rasio Perceraian", f"{rasio:.2f}%")
col4.metric("Rata-rata/Kab", f"{avg_nikah:,.0f}")
col5.metric("Jumlah Wilayah", f"{jumlah_wilayah}")

st.markdown("---")

# === SECTION 2: MAIN CHARTS (2 COLUMNS) ===
col_left, col_right = st.columns([1.2, 1])

with col_left:
    st.subheader("📈 Tren Pernikahan dan Perceraian per Tahun")

    yearly_data = filtered_df.groupby('Tahun').agg({
        'Nikah': 'sum',
        'Faktor Perceraian - Jumlah': 'sum'
    }).reset_index()
    yearly_data['Rasio (%)'] = (yearly_data['Faktor Perceraian - Jumlah'] / 
                                 yearly_data['Nikah']) * 100

    fig_trend = go.Figure()
    fig_trend.add_trace(go.Bar(
        x=yearly_data['Tahun'], 
        y=yearly_data['Nikah'],
        name='Pernikahan',
        marker_color='lightgreen',
        yaxis='y',
        text=yearly_data['Nikah'],
        texttemplate='%{text:,.0f}',
        textposition='outside'
    ))
    fig_trend.add_trace(go.Bar(
        x=yearly_data['Tahun'], 
        y=yearly_data['Faktor Perceraian - Jumlah'],
        name='Perceraian',
        marker_color='lightcoral',
        yaxis='y',
        text=yearly_data['Faktor Perceraian - Jumlah'],
        texttemplate='%{text:,.0f}',
        textposition='outside'
    ))
    fig_trend.add_trace(go.Scatter(
        x=yearly_data['Tahun'], 
        y=yearly_data['Rasio (%)'],
        name='Rasio (%)',
        marker_color='red',
        yaxis='y2',
        mode='lines+markers',
        line=dict(width=3),
        marker=dict(size=10)
    ))

    fig_trend.update_layout(
        height=350,
        yaxis=dict(title='Jumlah', side='left', showgrid=False),
        yaxis2=dict(title='Rasio (%)', side='right', overlaying='y', showgrid=False),
        xaxis=dict(dtick=1),  # Tampilkan setiap tahun
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1),
        margin=dict(l=0, r=0, t=30, b=0),
        hovermode='x unified'
    )
    st.plotly_chart(fig_trend, use_container_width=True)

with col_right:
    st.subheader("🏆 Top 10 Wilayah (Pernikahan)")

    regional_data = filtered_df.groupby('Kabupaten/Kota').agg({
        'Nikah': 'sum',
        'Faktor Perceraian - Jumlah': 'sum'
    }).reset_index()
    regional_data['Rasio (%)'] = (regional_data['Faktor Perceraian - Jumlah'] / 
                                   regional_data['Nikah']) * 100
    regional_data = regional_data.sort_values('Nikah', ascending=False).head(10)

    fig_top = px.bar(regional_data, 
                     x='Nikah', 
                     y='Kabupaten/Kota',
                     orientation='h',
                     color='Rasio (%)',
                     color_continuous_scale='RdYlGn_r',
                     text='Nikah')
    fig_top.update_traces(texttemplate='%{text:,.0f}', textposition='outside')
    fig_top.update_layout(
        height=350,
        yaxis={'categoryorder':'total ascending'},
        margin=dict(l=0, r=0, t=0, b=0),
        showlegend=False
    )
    st.plotly_chart(fig_top, use_container_width=True)

# === SECTION 3: DIVORCE FACTORS (REORGANIZED) ===
st.markdown("---")
st.subheader("🔍 Analisis Faktor Penyebab Perceraian")

# Get divorce factors
divorce_factors = [col for col in df.columns if 'Faktor Perceraian' in col and col != 'Faktor Perceraian - Jumlah']
factor_names = {col: col.replace('Faktor Perceraian - ', '') for col in divorce_factors}

# Prepare factor data
factor_data = filtered_df[divorce_factors].sum().reset_index()
factor_data.columns = ['Faktor', 'Jumlah']
factor_data['Faktor'] = factor_data['Faktor'].map(factor_names)
factor_data = factor_data.sort_values('Jumlah', ascending=False)

# BARIS PERTAMA: Bar Chart + Pie Chart (2 kolom)
col1, col2 = st.columns([1.3, 1])

with col1:
    fig_factors = px.bar(factor_data, 
                        x='Jumlah', 
                        y='Faktor',
                        orientation='h',
                        color='Jumlah',
                        color_continuous_scale='Reds',
                        text='Jumlah')
    fig_factors.update_traces(texttemplate='%{text:,.0f}', textposition='outside')
    fig_factors.update_layout(
        height=400,
        yaxis={'categoryorder':'total ascending'},
        margin=dict(l=0, r=0, t=0, b=0),
        showlegend=False
    )
    st.plotly_chart(fig_factors, use_container_width=True)

with col2:
    # Top 3 + Faktor Lainnya untuk Pie Chart
    top3_factors = factor_data.head(3).copy()
    other_factors = factor_data.iloc[3:]['Jumlah'].sum()

    other_row = pd.DataFrame({'Faktor': ['Faktor Lainnya'], 'Jumlah': [other_factors]})
    pie_data = pd.concat([top3_factors, other_row], ignore_index=True)

    fig_pie = px.pie(pie_data, 
                    values='Jumlah', 
                    names='Faktor',
                    title='Proporsi Top 3 Faktor + Lainnya',
                    hole=0.4)
    fig_pie.update_traces(textposition='inside', textinfo='percent+label')
    fig_pie.update_layout(
        height=400,
        margin=dict(l=0, r=0, t=40, b=0),
        showlegend=False
    )
    st.plotly_chart(fig_pie, use_container_width=True)

# BARIS KEDUA: Tren Line Chart (full width di bawah)
st.subheader("📈 Tren Top 2 Faktor Perceraian per Tahun")

reverse_factor_names = {v: k for k, v in factor_names.items()}
top2_factors = factor_data.head(2)
top2_factor_cols = [reverse_factor_names[f] for f in top2_factors['Faktor'].tolist()]
other_factor_cols = [reverse_factor_names[f] for f in factor_data.iloc[2:]['Faktor'].tolist()]

factor_trend = filtered_df.groupby('Tahun')[top2_factor_cols + other_factor_cols].sum().reset_index()

# Hitung "Faktor Lainnya" per tahun
factor_trend['Faktor Lainnya'] = factor_trend[other_factor_cols].sum(axis=1)

# Buat data untuk plotting (top 2 + lainnya)
plot_cols = top2_factor_cols + ['Faktor Lainnya']
factor_trend_plot = factor_trend[['Tahun'] + plot_cols]

factor_trend_melted = factor_trend_plot.melt(id_vars='Tahun', 
                                              value_vars=plot_cols,
                                              var_name='Faktor', 
                                              value_name='Jumlah')

# Map nama faktor (kecuali Faktor Lainnya)
factor_trend_melted['Faktor'] = factor_trend_melted['Faktor'].apply(
    lambda x: factor_names.get(x, x)
)

fig_factor_trend = px.line(factor_trend_melted, 
                          x='Tahun', 
                          y='Jumlah', 
                          color='Faktor',
                          markers=True)
fig_factor_trend.update_traces(line=dict(width=3), marker=dict(size=10))
# FIX: Tampilkan tahun sebagai integer, bukan desimal
fig_factor_trend.update_xaxes(dtick=1, tickmode='linear')
fig_factor_trend.update_layout(
    height=350,
    margin=dict(l=0, r=0, t=0, b=0),
    legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='center', x=0.5, font=dict(size=11)),
    hovermode='x unified'
)
st.plotly_chart(fig_factor_trend, use_container_width=True)

# === SECTION 4: REGIONAL COMPARISON ===
st.markdown("---")
col1, col2 = st.columns(2)

with col1:
    st.subheader("📊 Rasio Perceraian Tertinggi")
    high_ratio = regional_data.nlargest(10, 'Rasio (%)')

    fig_high = px.bar(high_ratio, 
                     x='Rasio (%)', 
                     y='Kabupaten/Kota',
                     orientation='h',
                     color='Rasio (%)',
                     color_continuous_scale='Reds',
                     text='Rasio (%)')
    fig_high.update_traces(texttemplate='%{text:.2f}%', textposition='outside')
    fig_high.update_layout(
        height=350,
        yaxis={'categoryorder':'total ascending'},
        margin=dict(l=0, r=0, t=0, b=0),
        showlegend=False
    )
    st.plotly_chart(fig_high, use_container_width=True)

with col2:
    st.subheader("📉 Top 10 Wilayah (Perceraian)")
    top_cerai = filtered_df.groupby('Kabupaten/Kota')['Faktor Perceraian - Jumlah'].sum().reset_index()
    top_cerai = top_cerai.sort_values('Faktor Perceraian - Jumlah', ascending=False).head(10)

    fig_cerai = px.bar(top_cerai, 
                      x='Faktor Perceraian - Jumlah', 
                      y='Kabupaten/Kota',
                      orientation='h',
                      color='Faktor Perceraian - Jumlah',
                      color_continuous_scale='Oranges',
                      text='Faktor Perceraian - Jumlah')
    fig_cerai.update_traces(texttemplate='%{text:,.0f}', textposition='outside')
    fig_cerai.update_layout(
        height=350,
        yaxis={'categoryorder':'total ascending'},
        margin=dict(l=0, r=0, t=0, b=0),
        showlegend=False
    )
    st.plotly_chart(fig_cerai, use_container_width=True)

# === SECTION 5: DATA SUMMARY TABLE ===
st.markdown("---")
st.subheader("📋 Ringkasan Data per Wilayah")

summary_df = filtered_df.groupby('Kabupaten/Kota').agg({
    'Nikah': 'sum',
    'Faktor Perceraian - Jumlah': 'sum',
    'Faktor Perceraian - Perselisihan dan Pertengkaran Terus Menerus': 'sum',
    'Faktor Perceraian - Ekonomi': 'sum',
    'Faktor Perceraian - Meninggalkan Salah satu Pihak': 'sum'
}).reset_index()

summary_df.columns = ['Kabupaten/Kota', 'Nikah', 'Perceraian', 'Pertengkaran', 'Ekonomi', 'Ditinggalkan']
summary_df['Rasio (%)'] = (summary_df['Perceraian'] / summary_df['Nikah'] * 100).round(2)
summary_df = summary_df.sort_values('Nikah', ascending=False)

# Format numbers
for col in ['Nikah', 'Perceraian', 'Pertengkaran', 'Ekonomi', 'Ditinggalkan']:
    summary_df[col] = summary_df[col].apply(lambda x: f"{x:,.0f}")

st.dataframe(summary_df, use_container_width=True, height=300)

# Download button
csv = filtered_df.to_csv(index=False).encode('utf-8')
st.download_button(
    label="📥 Download Data Lengkap (CSV)",
    data=csv,
    file_name="data_pernikahan_perceraian_jatim.csv",
    mime="text/csv"
)

# Footer
st.markdown("---")
st.caption("📊 Dashboard Pernikahan dan Perceraian Jawa Timur 2020-2024 | Data: Pengadilan Agama")