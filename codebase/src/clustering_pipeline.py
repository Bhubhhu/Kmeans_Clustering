"""
Country Immunisation Coverage Profiles Through Unsupervised Clustering Analysis
Source Context: Bill & Melinda Gates Foundation / Open WHO & GAVI Immunisation Indicators
"""
import os
import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.preprocessing import StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.metrics import silhouette_score, davies_bouldin_score, adjusted_rand_score
from scipy.spatial.distance import cdist

def kmedians_manhattan(X, n_clusters, random_state=42, max_iter=100):
    """
    K-Medians / K-Means variant using Manhattan (L1) distance metric and component-wise median centroids.
    """
    rng = np.random.RandomState(random_state)
    init_idx = rng.choice(len(X), n_clusters, replace=False)
    centroids = X[init_idx].copy()
    labels = np.zeros(len(X), dtype=int)
    
    for _ in range(max_iter):
        dists = cdist(X, centroids, metric='cityblock')
        new_labels = np.argmin(dists, axis=1)
        if np.array_equal(labels, new_labels):
            break
        labels = new_labels
        for k in range(n_clusters):
            cluster_pts = X[labels == k]
            if len(cluster_pts) > 0:
                centroids[k] = np.median(cluster_pts, axis=0)
                
    # Calculate L1 Within-Cluster Dispersion (analogous to WCSS)
    dists = cdist(X, centroids, metric='cityblock')
    wcss_l1 = float(np.sum(np.min(dists, axis=1)))
    return labels, centroids, wcss_l1

def run_pipeline(data_path, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    df = pd.read_csv(data_path)
    
    num_features = [
        'BCG', 'DTP1', 'DTP3', 'POL3', 'MCV1', 
        'MCV2', 'HEPB3', 'HIB3', 'PCV3', 'ROTA', 'DTP_Dropout_Rate'
    ]
    cat_features = ['WHO_Region', 'Income_Group', 'GAVI_Eligibility']
    
    # 1. Document Missing Values
    missing_summary = df[num_features].isnull().sum().reset_index()
    missing_summary.columns = ['Feature', 'Missing_Count']
    missing_summary['Missing_Percentage'] = (missing_summary['Missing_Count'] / len(df) * 100).round(2)
    missing_summary.to_csv(os.path.join(output_dir, 'preprocessing_missing_report.csv'), index=False)
    
    # 2. Group-wise Median Imputation by Income_Group (fallback to global median)
    df_imputed = df.copy()
    for col in num_features:
        df_imputed[col] = df_imputed.groupby('Income_Group')[col].transform(lambda x: x.fillna(x.median()))
        df_imputed[col] = df_imputed[col].fillna(df_imputed[col].median())
        
    # Recompute DTP_Dropout_Rate cleanly after imputation
    df_imputed['DTP_Dropout_Rate'] = (((df_imputed['DTP1'] - df_imputed['DTP3']) / df_imputed['DTP1']) * 100).round(2)
    
    # 3. Categorical Encoding (One-Hot Encoding for contextual auditing, kept separate from pure coverage clustering space)
    df_encoded = pd.get_dummies(df_imputed, columns=cat_features, drop_first=False)
    df_encoded.to_csv(os.path.join(output_dir, 'preprocessed_encoded_dataset.csv'), index=False)
    
    # 4. Standardisation (Z-score scaling on numerical coverage indicators)
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(df_imputed[num_features])
    
    # 5. Evaluate K-Means (Euclidean L2) & K-Medians (Manhattan L1) across K = 2..8
    k_values = list(range(2, 9))
    eval_records = []
    
    for k in k_values:
        # Euclidean K-Means
        km = KMeans(n_clusters=k, init='k-means++', n_init=20, random_state=42)
        labels_euc = km.fit_predict(X_scaled)
        wcss_euc = float(km.inertia_)
        sil_euc = float(silhouette_score(X_scaled, labels_euc, metric='euclidean'))
        db_euc = float(davies_bouldin_score(X_scaled, labels_euc))
        
        # Stability across 15 random seeds for Euclidean K-Means
        ari_scores = []
        for seed in range(100, 115):
            km_seed = KMeans(n_clusters=k, init='k-means++', n_init=10, random_state=seed)
            lbl_s = km_seed.fit_predict(X_scaled)
            ari_scores.append(adjusted_rand_score(labels_euc, lbl_s))
        mean_ari_euc = float(np.mean(ari_scores))
        
        eval_records.append({
            'K': k,
            'Distance_Metric': 'Euclidean (L2)',
            'WCSS_Dispersion': round(wcss_euc, 2),
            'Silhouette_Score': round(sil_euc, 4),
            'Davies_Bouldin_Index': round(db_euc, 4),
            'Seed_Stability_ARI': round(mean_ari_euc, 4)
        })
        
        # Manhattan K-Medians (L1)
        labels_man, _, wcss_man = kmedians_manhattan(X_scaled, n_clusters=k, random_state=42)
        sil_man = float(silhouette_score(X_scaled, labels_man, metric='cityblock'))
        db_man = float(davies_bouldin_score(X_scaled, labels_man))
        
        ari_man_scores = []
        for seed in range(100, 115):
            lbl_m_s, _, _ = kmedians_manhattan(X_scaled, n_clusters=k, random_state=seed)
            ari_man_scores.append(adjusted_rand_score(labels_man, lbl_m_s))
        mean_ari_man = float(np.mean(ari_man_scores))
        
        eval_records.append({
            'K': k,
            'Distance_Metric': 'Manhattan (L1)',
            'WCSS_Dispersion': round(wcss_man, 2),
            'Silhouette_Score': round(sil_man, 4),
            'Davies_Bouldin_Index': round(db_man, 4),
            'Seed_Stability_ARI': round(mean_ari_man, 4)
        })
        
    df_eval = pd.DataFrame(eval_records)
    df_eval.to_csv(os.path.join(output_dir, 'clustering_validation_metrics.csv'), index=False)
    
    # 6. Select Defensible Configuration: K = 4 with Euclidean Distance
    optimal_k = 4
    final_km = KMeans(n_clusters=optimal_k, init='k-means++', n_init=30, random_state=42)
    raw_clusters = final_km.fit_predict(X_scaled)
    
    # Order cluster IDs 0..3 from Highest DTP3 coverage to Lowest DTP3 coverage for intuitive interpretation
    df_imputed['Raw_Cluster'] = raw_clusters
    cluster_order = df_imputed.groupby('Raw_Cluster')['DTP3'].mean().sort_values(ascending=False).index.tolist()
    cluster_map = {old_id: new_id for new_id, old_id in enumerate(cluster_order)}
    df_imputed['Cluster_ID'] = df_imputed['Raw_Cluster'].map(cluster_map)
    df_imputed.drop(columns=['Raw_Cluster'], inplace=True)
    
    profile_names = {
        0: 'Tier 1: High Universal & Sustained Coverage',
        1: 'Tier 2: Strong Core Coverage, Lagging Newer Vaccines',
        2: 'Tier 3: Moderate Coverage with Multi-Dose Dropout Gaps',
        3: 'Tier 4: Fragile & Zero-Dose Challenged Systems'
    }
    df_imputed['Cluster_Profile_Name'] = df_imputed['Cluster_ID'].map(profile_names)
    
    # 7. PCA Visualisation & Loadings
    pca = PCA(n_components=2, random_state=42)
    X_pca = pca.fit_transform(X_scaled)
    df_imputed['PCA1'] = X_pca[:, 0].round(4)
    df_imputed['PCA2'] = X_pca[:, 1].round(4)
    
    df_imputed.to_csv(os.path.join(output_dir, 'country_cluster_assignments.csv'), index=False)
    
    loadings = pd.DataFrame(
        pca.components_.T,
        index=num_features,
        columns=['PC1_Loading', 'PC2_Loading']
    ).reset_index().rename(columns={'index': 'Feature'})
    loadings['Variance_Contribution_Score'] = np.sqrt(loadings['PC1_Loading']**2 + loadings['PC2_Loading']**2).round(4)
    loadings.to_csv(os.path.join(output_dir, 'pca_feature_loadings.csv'), index=False)
    
    # 8. Cluster Summary Profiles Table
    summary_profile = df_imputed.groupby(['Cluster_ID', 'Cluster_Profile_Name'])[num_features].mean().round(2).reset_index()
    counts = df_imputed['Cluster_ID'].value_counts().rename('Country_Count')
    summary_profile = summary_profile.merge(counts, on='Cluster_ID')
    summary_profile.to_csv(os.path.join(output_dir, 'cluster_summary_profiles.csv'), index=False)
    
    # 9. Generate High-Resolution Plots for Report & PPT
    plt.style.use('seaborn-v0_8-whitegrid' if 'seaborn-v0_8-whitegrid' in plt.style.available else 'default')
    
    # Plot 1: Validation Curves (WCSS, Silhouette, Davies-Bouldin)
    fig, axes = plt.subplots(1, 3, figsize=(16, 4.8), dpi=200)
    euc_df = df_eval[df_eval['Distance_Metric'] == 'Euclidean (L2)']
    man_df = df_eval[df_eval['Distance_Metric'] == 'Manhattan (L1)']
    
    axes[0].plot(euc_df['K'], euc_df['WCSS_Dispersion'], 'o-', color='#1f4e78', lw=2.2, label='Euclidean (L2) WCSS')
    axes[0].axvline(4, color='#d9534f', linestyle='--', lw=1.5, label='Selected K=4')
    axes[0].set_title('Elbow Method: Within-Cluster Sum of Squares', fontsize=11, fontweight='bold')
    axes[0].set_xlabel('Number of Clusters (K)')
    axes[0].set_ylabel('WCSS (Inertia)')
    axes[0].legend()
    
    axes[1].plot(euc_df['K'], euc_df['Silhouette_Score'], 'o-', color='#1f4e78', lw=2.2, label='Euclidean (L2)')
    axes[1].plot(man_df['K'], man_df['Silhouette_Score'], 's--', color='#2e8b57', lw=2.0, label='Manhattan (L1)')
    axes[1].axvline(4, color='#d9534f', linestyle='--', lw=1.5, label='Selected K=4')
    axes[1].set_title('Silhouette Score Comparison (Higher = Better)', fontsize=11, fontweight='bold')
    axes[1].set_xlabel('Number of Clusters (K)')
    axes[1].set_ylabel('Silhouette Coefficient')
    axes[1].legend()
    
    axes[2].plot(euc_df['K'], euc_df['Davies_Bouldin_Index'], 'o-', color='#1f4e78', lw=2.2, label='Euclidean (L2)')
    axes[2].plot(man_df['K'], man_df['Davies_Bouldin_Index'], 's--', color='#2e8b57', lw=2.0, label='Manhattan (L1)')
    axes[2].axvline(4, color='#d9534f', linestyle='--', lw=1.5, label='Selected K=4')
    axes[2].set_title('Davies-Bouldin Index (Lower = Better)', fontsize=11, fontweight='bold')
    axes[2].set_xlabel('Number of Clusters (K)')
    axes[2].set_ylabel('Davies-Bouldin Index')
    axes[2].legend()
    
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'fig1_validation_metrics_comparison.png'), dpi=200)
    plt.close()
    
    # Plot 2: PCA 2D Cluster Separation Biplot
    fig, ax = plt.subplots(figsize=(10, 6.5), dpi=200)
    colors = ['#1b6ca8', '#2a9d8f', '#e9c46a', '#e76f51']
    for cid in range(optimal_k):
        sub = df_imputed[df_imputed['Cluster_ID'] == cid]
        ax.scatter(
            sub['PCA1'], sub['PCA2'],
            c=colors[cid], s=65, alpha=0.85, edgecolors='k', linewidth=0.5,
            label=f"{profile_names[cid]} (n={len(sub)})"
        )
    # Overlay feature vectors
    for i, feat in enumerate(num_features):
        ax.arrow(0, 0, pca.components_[0, i]*4.5, pca.components_[1, i]*4.5,
                 color='#333333', alpha=0.6, head_width=0.12)
        ax.text(pca.components_[0, i]*4.85, pca.components_[1, i]*4.85, feat,
                fontsize=8.5, fontweight='bold', color='#111111')
        
    var_exp = pca.explained_variance_ratio_ * 100
    ax.set_title('PCA Biplot of Country Immunisation Coverage Profiles (K=4, Euclidean)', fontsize=13, fontweight='bold')
    ax.set_xlabel(f'Principal Component 1 ({var_exp[0]:.1f}% Explained Variance - Overall System Strength)', fontsize=10.5)
    ax.set_ylabel(f'Principal Component 2 ({var_exp[1]:.1f}% Explained Variance - New Vaccine vs Dropout Axis)', fontsize=10.5)
    ax.legend(loc='upper right', frameon=True, fontsize=9)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'fig2_pca_cluster_separation.png'), dpi=200)
    plt.close()
    
    # Plot 3: Cluster Immunisation Indicator Profiles (Grouped Bar / Heatmap View)
    fig, ax = plt.subplots(figsize=(12, 6), dpi=200)
    x = np.arange(len(num_features))
    width = 0.2
    for cid in range(optimal_k):
        vals = summary_profile[summary_profile['Cluster_ID'] == cid][num_features].values.flatten()
        ax.bar(x + (cid - 1.5)*width, vals, width, label=profile_names[cid], color=colors[cid], edgecolor='black', linewidth=0.4)
    ax.set_xticks(x)
    ax.set_xticklabels(num_features, rotation=30, ha='right', fontweight='bold')
    ax.set_ylabel('Mean Percentage (%) / Dropout Rate (%)')
    ax.set_title('Mean Vaccine Coverage & DTP Dropout Rate Across Country Cluster Profiles', fontsize=12.5, fontweight='bold')
    ax.legend(loc='upper right', fontsize=9)
    ax.set_ylim(0, 110)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'fig3_cluster_feature_profiles.png'), dpi=200)
    plt.close()
    
    return {
        'pca_variance': [round(float(v*100), 2) for v in pca.explained_variance_ratio_],
        'summary_profile': summary_profile.to_dict(orient='records'),
        'eval_metrics': df_eval.to_dict(orient='records')
    }

if __name__ == '__main__':
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_file = os.path.join(base_dir, 'data', 'who_gavi_immunisation_coverage.csv')
    out_dir = os.path.join(base_dir, 'outputs')
    results = run_pipeline(data_file, out_dir)
    print("Pipeline executed successfully. PCA Explained Variance (%):", results['pca_variance'])
