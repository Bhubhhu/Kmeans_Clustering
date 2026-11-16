# Country Immunisation Coverage Profiles Through Unsupervised Clustering Analysis

**Source Domain:** Bill & Melinda Gates Foundation | Open GAVI & WHO/UNICEF (WUENIC) Immunisation Indicators  
**Problem Statement ID:** BMGF-GAVI-WHO-CLUST-2026  

---

## 1. Project Overview
This project develops a reproducible, end-to-end unsupervised machine learning workflow to stratify **194 WHO member states** into interpretable **Country Immunisation Coverage Profiles**. Using 11 core antigen and delivery continuity indicators (`BCG`, `DTP1`, `DTP3`, `POL3`, `MCV1`, `MCV2`, `HEPB3`, `HIB3`, `PCV3`, `ROTA`, and derived `DTP_Dropout_Rate`) alongside contextual regional and GAVI eligibility attributes, the pipeline:
1. Documents variable relevance, performs income-group stratified median imputation for missing values, encodes categorical variables, and applies Z-score standardisation (`StandardScaler`).
2. Benchmarks **K-Means (Euclidean $L_2$ distance)** against **K-Medians/K-Means (Manhattan $L_1$ distance)** across $K \in \{2, 3, 4, 5, 6, 7, 8\}$ using **Within-Cluster Sum of Squares (WCSS)**, **Silhouette Score**, **Davies-Bouldin Index (DBI)**, and multi-seed **Adjusted Rand Index (ARI)** stability.
3. Projects high-dimensional profiles onto a 2D **Principal Component Analysis (PCA)** biplot (capturing **90.81%** total variance) and interprets the selected $K=4$ configuration responsibly without treating exploratory statistical clusters as rigid real-world labels.

---

## 2. Directory Structure
```text
RegNo1_RegNo2_RegNo3/
├── Project_Report.pdf                      # Comprehensive Technical Project Report (PDF)
├── PPT_Presentation.pptx                   # Project Presentation Deck (PPTX)
├── PPT_Presentation.pdf                    # Project Presentation Deck (PDF export)
├── README.md                               # Project overview, setup, and execution guide
├── requirements.txt                        # Python package dependencies
├── PROJECT_LINKS.txt                       # GitHub repository and live deployment URLs
└── codebase/                               # Complete executable source codebase
    ├── app.py                              # Interactive Streamlit web dashboard
    ├── requirements.txt                    # Environment dependencies
    ├── data/
    │   └── who_gavi_immunisation_coverage.csv  # Open WHO/GAVI country coverage dataset (194 countries)
    ├── src/
    │   └── clustering_pipeline.py          # Core preprocessing, clustering, PCA, and plotting engine
    ├── tests/
    │   └── test_pipeline.py                # Automated verification and integrity test suite
    └── outputs/                            # Generated CSV tables and high-res PNG visualisations
        ├── preprocessing_missing_report.csv
        ├── preprocessed_encoded_dataset.csv
        ├── clustering_validation_metrics.csv
        ├── country_cluster_assignments.csv
        ├── pca_feature_loadings.csv
        ├── cluster_summary_profiles.csv
        ├── fig1_validation_metrics_comparison.png
        ├── fig2_pca_cluster_separation.png
        └── fig3_cluster_feature_profiles.png
```

---

## 3. Prerequisites & Installation Steps

### Prerequisites
- **Python**: Version 3.9 or higher
- **pip**: Standard Python package installer

### Installation
1. Unzip the submission archive (`RegNo1_RegNo2_RegNo3.zip`) and navigate into the project directory:
   ```bash
   cd codebase
   ```
2. (Optional) Create and activate a virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate   # On Windows: venv\Scripts\activate
   ```
3. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

---

## 4. Execution Instructions

### A. Run the Complete Clustering & PCA Pipeline
To execute data preprocessing, distance metric comparisons ($L_2$ vs $L_1$), PCA projection, and regenerate all CSV tables and high-resolution figures in `codebase/outputs/`:
```bash
python3 src/clustering_pipeline.py
```

### B. Run Automated Verification Tests
To verify that all output tables, cluster assignments, and visualisations pass integrity checks:
```bash
python3 tests/test_pipeline.py
```

### C. Launch the Interactive Streamlit Web Application
To explore the clusters, PCA biplots, and country-level filtering interactively in your browser:
```bash
streamlit run app.py
```

---

## 5. External Dataset Sources & Setup
The dataset (`codebase/data/who_gavi_immunisation_coverage.csv`) is pre-packaged for immediate offline reproducibility and is structured around official open global immunisation repositories:
- **WHO / UNICEF Estimates of National Immunization Coverage (WUENIC)**: [https://immunizationdata.who.int/](https://immunizationdata.who.int/)
- **GAVI, the Vaccine Alliance — Country Eligibility & Transition Data**: [https://www.gavi.org/programmes-impact/country-hub](https://www.gavi.org/programmes-impact/country-hub)
- **Bill & Melinda Gates Foundation — Global Delivery & Immunisation Strategy**: [https://www.gatesfoundation.org/our-work/programs/global-development/immunization](https://www.gatesfoundation.org/our-work/programs/global-development/immunization)
