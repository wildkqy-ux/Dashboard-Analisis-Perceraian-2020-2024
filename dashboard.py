import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Set page configuration
st.set_page_config(page_title="Dashboard Pernikahan dan Perceraian Jawa Timur", 
                   page_icon="💑", 
                   layout="wide")

# Load data
@st.cache_data
def load_data():
    df = pd.read_excel('data.xlsx')
    return df

df = load_data()

# Title and description
st.title("📊 Dashboard Analisis Pernikahan dan Perceraian Jawa Timur")
st.markdown("---")

# Sidebar filters
st.sidebar.header("🔍 Filter Data")
years = sorted(df['Tahun'].unique())
selected_years = st.sidebar.multiselect("Pilih Tahun", years, default=years)

regencies = sorted(df['Kabupaten/Kota'].unique())
selected_regencies = st.sidebar.multiselect("Pilih Kabupaten/Kota", 
                                            regencies, 
                                            default=regencies)

# Filter data
filtered_df = df[df['Tahun'].isin(selected_years) & 
                 df['Kabupaten/Kota'].isin(selected_regencies)]

# Main metrics
st.header("📈 Ringkasan Statistik")
col1, col2, col3, col4 = st.columns(4)

with col1:
    total_nikah = filtered_df['Nikah'].sum()
    st.metric("Total Pernikahan", f"{total_nikah:,}")

with col2:
    total_cerai = filtered_df['Faktor Perceraian - Jumlah'].sum()
    st.metric("Total Perceraian", f"{total_cerai:,}")

with col3:
    if total_nikah > 0:
        rasio = (total_cerai / total_nikah) * 100
        st.metric("Rasio Perceraian", f"{rasio:.2f}%")
    else:
        st.metric("Rasio Perceraian", "N/A")

with col4:
    avg_nikah = filtered_df.groupby('Kabupaten/Kota')['Nikah'].sum().mean()
    st.metric("Rata-rata Nikah/Kab", f"{avg_nikah:,.0f}")

st.markdown("---")

# Tabs for different visualizations
tab1, tab2, tab3, tab4, tab5 = st.tabs(["📊 Tren Tahunan", 
                                         "🗺️ Per Wilayah", 
                                         "🔍 Faktor Perceraian", 
                                         "📉 Perbandingan", 
                                         "📋 Data Mentah"])

with tab1:
    st.subheader("Tren Pernikahan dan Perceraian per Tahun")

    yearly_data = filtered_df.groupby('Tahun').agg({
        'Nikah': 'sum',
        'Faktor Perceraian - Jumlah': 'sum'
    }).reset_index()

    fig_trend = go.Figure()
    fig_trend.add_trace(go.Scatter(x=yearly_data['Tahun'], 
                                   y=yearly_data['Nikah'],
                                   mode='lines+markers',
                                   name='Pernikahan',
                                   line=dict(color='green', width=3),
                                   marker=dict(size=10)))
    fig_trend.add_trace(go.Scatter(x=yearly_data['Tahun'], 
                                   y=yearly_data['Faktor Perceraian - Jumlah'],
                                   mode='lines+markers',
                                   name='Perceraian',
                                   line=dict(color='red', width=3),
                                   marker=dict(size=10)))
    fig_trend.update_layout(height=500, 
                           xaxis_title="Tahun",
                           yaxis_title="Jumlah",
                           hovermode='x unified')
    st.plotly_chart(fig_trend, use_container_width=True)

    # Rasio perceraian per tahun
    st.subheader("Tren Rasio Perceraian (%)")
    yearly_data['Rasio'] = (yearly_data['Faktor Perceraian - Jumlah'] / yearly_data['Nikah']) * 100

    fig_ratio = px.bar(yearly_data, x='Tahun', y='Rasio',
                       text='Rasio',
                       color='Rasio',
                       color_continuous_scale='Reds')
    fig_ratio.update_traces(texttemplate='%{text:.2f}%', textposition='outside')
    fig_ratio.update_layout(height=400, yaxis_title="Rasio Perceraian (%)")
    st.plotly_chart(fig_ratio, use_container_width=True)

with tab2:
    st.subheader("Distribusi Pernikahan dan Perceraian per Kabupaten/Kota")

    regional_data = filtered_df.groupby('Kabupaten/Kota').agg({
        'Nikah': 'sum',
        'Faktor Perceraian - Jumlah': 'sum'
    }).reset_index()
    regional_data = regional_data.sort_values('Nikah', ascending=False)

    col1, col2 = st.columns(2)

    with col1:
        fig_nikah = px.bar(regional_data.head(15), 
                          x='Nikah', 
                          y='Kabupaten/Kota',
                          orientation='h',
                          title='Top 15 Wilayah - Pernikahan',
                          color='Nikah',
                          color_continuous_scale='Greens')
        fig_nikah.update_layout(height=600, yaxis={'categoryorder':'total ascending'})
        st.plotly_chart(fig_nikah, use_container_width=True)

    with col2:
        regional_data_cerai = regional_data.sort_values('Faktor Perceraian - Jumlah', ascending=False)
        fig_cerai = px.bar(regional_data_cerai.head(15), 
                          x='Faktor Perceraian - Jumlah', 
                          y='Kabupaten/Kota',
                          orientation='h',
                          title='Top 15 Wilayah - Perceraian',
                          color='Faktor Perceraian - Jumlah',
                          color_continuous_scale='Reds')
        fig_cerai.update_layout(height=600, yaxis={'categoryorder':'total ascending'})
        st.plotly_chart(fig_cerai, use_container_width=True)

    # Map visualization (simplified)
    st.subheader("Rasio Perceraian per Wilayah")
    regional_data['Rasio Perceraian'] = (regional_data['Faktor Perceraian - Jumlah'] / 
                                         regional_data['Nikah']) * 100
    regional_data = regional_data.sort_values('Rasio Perceraian', ascending=False)

    fig_map = px.bar(regional_data, 
                     x='Kabupaten/Kota', 
                     y='Rasio Perceraian',
                     color='Rasio Perceraian',
                     color_continuous_scale='RdYlGn_r',
                     title='Rasio Perceraian per Wilayah (%)')
    fig_map.update_layout(height=500, xaxis_tickangle=-45)
    st.plotly_chart(fig_map, use_container_width=True)

with tab3:
    st.subheader("Analisis Faktor-Faktor Penyebab Perceraian")

    # Get divorce factor columns
    divorce_factors = [col for col in df.columns if 'Faktor Perceraian' in col and col != 'Faktor Perceraian - Jumlah']

    # Simplify column names
    factor_names = {col: col.replace('Faktor Perceraian - ', '') for col in divorce_factors}

    # Aggregate by factors
    factor_data = filtered_df[divorce_factors].sum().reset_index()
    factor_data.columns = ['Faktor', 'Jumlah']
    factor_data['Faktor'] = factor_data['Faktor'].map(factor_names)
    factor_data = factor_data.sort_values('Jumlah', ascending=False)

    col1, col2 = st.columns([2, 1])

    with col1:
        fig_factors = px.bar(factor_data, 
                            x='Jumlah', 
                            y='Faktor',
                            orientation='h',
                            title='Total Kasus per Faktor Perceraian',
                            color='Jumlah',
                            color_continuous_scale='Reds')
        fig_factors.update_layout(height=600, yaxis={'categoryorder':'total ascending'})
        st.plotly_chart(fig_factors, use_container_width=True)

    with col2:
        fig_pie = px.pie(factor_data, 
                        values='Jumlah', 
                        names='Faktor',
                        title='Proporsi Faktor Perceraian')
        fig_pie.update_traces(textposition='inside', textinfo='percent+label')
        fig_pie.update_layout(height=600, showlegend=False)
        st.plotly_chart(fig_pie, use_container_width=True)

    # Trend of top factors over years
    st.subheader("Tren Faktor Perceraian Utama per Tahun")
    top_factors = factor_data.head(5)['Faktor'].tolist()

    # Reverse the mapping to get original column names
    reverse_factor_names = {v: k for k, v in factor_names.items()}
    top_factor_cols = [reverse_factor_names[f] for f in top_factors]

    factor_trend = filtered_df.groupby('Tahun')[top_factor_cols].sum().reset_index()
    factor_trend_melted = factor_trend.melt(id_vars='Tahun', 
                                           value_vars=top_factor_cols,
                                           var_name='Faktor', 
                                           value_name='Jumlah')
    factor_trend_melted['Faktor'] = factor_trend_melted['Faktor'].map(factor_names)

    fig_factor_trend = px.line(factor_trend_melted, 
                              x='Tahun', 
                              y='Jumlah', 
                              color='Faktor',
                              markers=True,
                              title='Tren 5 Faktor Perceraian Teratas')
    fig_factor_trend.update_layout(height=500)
    st.plotly_chart(fig_factor_trend, use_container_width=True)

with tab4:
    st.subheader("Perbandingan Antar Wilayah")

    # Select regions to compare
    comparison_regions = st.multiselect(
        "Pilih Wilayah untuk Dibandingkan (Max 5)",
        options=sorted(filtered_df['Kabupaten/Kota'].unique()),
        default=sorted(filtered_df['Kabupaten/Kota'].unique())[:3],
        max_selections=5
    )

    if comparison_regions:
        comparison_df = filtered_df[filtered_df['Kabupaten/Kota'].isin(comparison_regions)]

        # Comparison by year
        comparison_yearly = comparison_df.groupby(['Kabupaten/Kota', 'Tahun']).agg({
            'Nikah': 'sum',
            'Faktor Perceraian - Jumlah': 'sum'
        }).reset_index()

        col1, col2 = st.columns(2)

        with col1:
            fig_comp_nikah = px.line(comparison_yearly, 
                                    x='Tahun', 
                                    y='Nikah', 
                                    color='Kabupaten/Kota',
                                    markers=True,
                                    title='Perbandingan Pernikahan')
            fig_comp_nikah.update_layout(height=400)
            st.plotly_chart(fig_comp_nikah, use_container_width=True)

        with col2:
            fig_comp_cerai = px.line(comparison_yearly, 
                                    x='Tahun', 
                                    y='Faktor Perceraian - Jumlah', 
                                    color='Kabupaten/Kota',
                                    markers=True,
                                    title='Perbandingan Perceraian')
            fig_comp_cerai.update_layout(height=400)
            st.plotly_chart(fig_comp_cerai, use_container_width=True)

        # Factor comparison
        st.subheader("Perbandingan Faktor Perceraian")
        comparison_factors = comparison_df.groupby('Kabupaten/Kota')[divorce_factors].sum()
        comparison_factors.columns = [factor_names[col] for col in comparison_factors.columns]

        selected_factor = st.selectbox("Pilih Faktor untuk Dibandingkan", 
                                      options=comparison_factors.columns)

        fig_factor_comp = px.bar(comparison_factors, 
                                x=comparison_factors.index, 
                                y=selected_factor,
                                title=f'Perbandingan: {selected_factor}',
                                color=selected_factor,
                                color_continuous_scale='Reds')
        fig_factor_comp.update_layout(height=400, xaxis_title='Kabupaten/Kota')
        st.plotly_chart(fig_factor_comp, use_container_width=True)

with tab5:
    st.subheader("Data Mentah")

    # Display options
    show_all = st.checkbox("Tampilkan Semua Kolom", value=False)

    if show_all:
        display_df = filtered_df
    else:
        basic_cols = ['Kabupaten/Kota', 'Tahun', 'Nikah', 'Faktor Perceraian - Jumlah']
        display_df = filtered_df[basic_cols]

    st.dataframe(display_df, use_container_width=True, height=500)

    # Download button
    csv = filtered_df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Download Data (CSV)",
        data=csv,
        file_name="data_pernikahan_perceraian_jatim.csv",
        mime="text/csv"
    )

    # Statistics
    st.subheader("Statistik Deskriptif")
    st.dataframe(filtered_df.describe(), use_container_width=True)

# Footer
st.markdown("---")
st.markdown("**Sumber Data:** Data Pernikahan dan Perceraian Jawa Timur 2020-2024")
st.markdown("Dashboard dibuat menggunakan Streamlit & Plotly")
