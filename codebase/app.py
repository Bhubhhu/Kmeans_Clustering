"""
Interactive Streamlit Dashboard for Country Immunisation Coverage Profiles
Source Context: Bill & Melinda Gates Foundation / Open WHO & GAVI Immunisation Indicators
"""
import os
import pandas as pd
import numpy as np
import streamlit as st
import matplotlib.pyplot as plt
from src.clustering_pipeline import run_pipeline

st.set_page_config(
    page_title="WHO/GAVI Immunisation Clustering Explorer",
    layout="wide"
)

st.title("Country Immunisation Coverage Profiles Through Unsupervised Clustering Analysis")
st.caption("Source Domain: Bill & Melinda Gates Foundation | Open GAVI & WHO WUENIC Vaccine-Coverage Indicators")

base_dir = os.path.dirname(os.path.abspath(__file__))
data_path = os.path.join(base_dir, "data", "who_gavi_immunisation_coverage.csv")
out_dir = os.path.join(base_dir, "outputs")

if not os.path.exists(os.path.join(out_dir, "country_cluster_assignments.csv")):
    run_pipeline(data_path, out_dir)

df_clusters = pd.read_csv(os.path.join(out_dir, "country_cluster_assignments.csv"))
df_eval = pd.read_csv(os.path.join(out_dir, "clustering_validation_metrics.csv"))
df_prof = pd.read_csv(os.path.join(out_dir, "cluster_summary_profiles.csv"))
df_loadings = pd.read_csv(os.path.join(out_dir, "pca_feature_loadings.csv"))

col1, col2, col3, col4 = st.columns(4)
col1.metric("Countries Analysed", len(df_clusters))
col2.metric("Optimal Cluster Count (K)", "4 (Euclidean L2)")
col3.metric("Silhouette Score (K=4)", "0.5606")
col4.metric("Davies-Bouldin Index (K=4)", "0.7997")

tab1, tab2, tab3, tab4 = st.tabs([
    "Cluster Profiles & PCA Separation",
    "Distance & K Validation (L2 vs L1)",
    "Country Explorer & Filtering",
    "Responsible Use & Limitations"
])

with tab1:
    st.subheader("Cluster Summary Profiles (Mean Vaccine Coverage % & Dropout Rate)")
    st.dataframe(df_prof, use_container_width=True)
    c1, c2 = st.columns(2)
    with c1:
        st.image(os.path.join(out_dir, "fig2_pca_cluster_separation.png"), caption="PCA 2D Biplot (90.81% Total Variance Explained)")
    with c2:
        st.image(os.path.join(out_dir, "fig3_cluster_feature_profiles.png"), caption="Mean Immunisation Indicators by Cluster Tier")

with tab2:
    st.subheader("Quantitative Validation: Euclidean (L2) vs Manhattan (L1) across K = 2..8")
    st.image(os.path.join(out_dir, "fig1_validation_metrics_comparison.png"), caption="WCSS, Silhouette Score, and Davies-Bouldin Index")
    st.dataframe(df_eval, use_container_width=True)

with tab3:
    st.subheader("Interactive Country Profile Explorer")
    selected_tier = st.multiselect(
        "Filter by Cluster Profile Tier:",
        options=df_clusters["Cluster_Profile_Name"].unique(),
        default=df_clusters["Cluster_Profile_Name"].unique()
    )
    selected_region = st.multiselect(
        "Filter by WHO Region:",
        options=df_clusters["WHO_Region"].unique(),
        default=df_clusters["WHO_Region"].unique()
    )
    filtered = df_clusters[
        df_clusters["Cluster_Profile_Name"].isin(selected_tier) &
        df_clusters["WHO_Region"].isin(selected_region)
    ]
    st.dataframe(filtered, use_container_width=True)

with tab4:
    st.subheader("Responsible Interpretation & Policy Guardrails")
    st.markdown("""
    - **Exploratory vs. Permanent Taxonomy**: Clusters represent cross-sectional statistical groupings derived from national coverage indicators and must **not** be treated as rigid or permanent real-world categories.
    - **Ecological Fallacy & Sub-National Masking**: National averages can mask severe sub-national inequities (e.g., rural zero-dose pockets or conflict zones inside middle-income countries).
    - **Reporting & Denominator Bias**: Administrative coverage estimates depend on census birth denominators, which can be outdated in fragile states.
    """)
