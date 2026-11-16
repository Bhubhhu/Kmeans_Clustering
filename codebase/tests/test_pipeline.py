"""
Automated Verification & Unit Tests for Country Immunisation Clustering Pipeline
"""
import os
import pandas as pd

def test_outputs_exist():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    out_dir = os.path.join(base_dir, "outputs")
    expected_files = [
        "preprocessing_missing_report.csv",
        "preprocessed_encoded_dataset.csv",
        "clustering_validation_metrics.csv",
        "country_cluster_assignments.csv",
        "pca_feature_loadings.csv",
        "cluster_summary_profiles.csv",
        "fig1_validation_metrics_comparison.png",
        "fig2_pca_cluster_separation.png",
        "fig3_cluster_feature_profiles.png"
    ]
    for fname in expected_files:
        fpath = os.path.join(out_dir, fname)
        assert os.path.exists(fpath), f"Missing output file: {fname}"
        
    df_assign = pd.read_csv(os.path.join(out_dir, "country_cluster_assignments.csv"))
    assert len(df_assign) == 194, "Expected 194 WHO member state records"
    assert df_assign.isnull().sum().sum() == 0, "Imputed dataset should contain zero NaN values"
    assert set(df_assign["Cluster_ID"].unique()) == {0, 1, 2, 3}, "Optimal K=4 clusters expected"
    print("ALL PIPELINE VERIFICATION TESTS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    test_outputs_exist()
