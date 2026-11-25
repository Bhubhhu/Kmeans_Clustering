"""Extra experiments for the IEEE-style paper: three feature-set models x K = 2..6, bands, membership tables.
Run from codebase/:  python docs/paper_experiments.py   (writes outputs/paper/*.csv and a heat-map figure)
"""
import itertools
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.metrics import adjusted_rand_score, davies_bouldin_score, silhouette_score
from sklearn.preprocessing import StandardScaler

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from src import pipeline as p  # noqa: E402

OUT = os.path.join(ROOT, "outputs", "paper")
os.makedirs(OUT, exist_ok=True)
df, _ = p.build_dataset(os.path.join(ROOT, "data", "raw"))
final = pd.read_csv(os.path.join(ROOT, "outputs", "country_archetypes.csv")).set_index("code")
df = df.join(final[["cluster", "archetype"]])

corr = df[p.FEATURES].corr()
pairs = [(a, b, corr.loc[a, b]) for a, b in itertools.combinations(p.FEATURES, 2) if abs(corr.loc[a, b]) > 0.85]
corr.round(3).to_csv(os.path.join(OUT, "feature_correlation.csv"))
print("pairs |r|>0.85:", [(a, b, round(r, 3)) for a, b, r in pairs])

MODELS = {"A": list(p.FEATURES)}
drop_b = {b for _, b, _ in pairs}                      # drop the second member of every highly correlated pair
MODELS["B"] = [f for f in p.FEATURES if f not in drop_b]
MODELS["C"] = [f for f in p.FEATURES if f != "trend_pre"]  # trend is estimated from ten noisy points
print({k: v for k, v in MODELS.items()})

rows, labels = [], {}
for m, feats in MODELS.items():
    X = StandardScaler().fit_transform(df[feats])
    for k in range(2, 7):
        km = KMeans(k, init="k-means++", n_init=20, random_state=42).fit(X)
        runs = [KMeans(k, n_init=10, random_state=s).fit_predict(X) for s in range(20)]
        ari = np.mean([adjusted_rand_score(a, b) for a, b in itertools.combinations(runs, 2)])
        rows.append({"Model": m, "Features": len(feats), "K": k, "WCSS": round(km.inertia_, 2),
                     "Silhouette": round(silhouette_score(X, km.labels_), 4),
                     "DBI": round(davies_bouldin_score(X, km.labels_), 4), "Mean_ARI": round(float(ari), 4)})
        order = pd.Series(km.labels_).map(pd.Series(km.labels_).value_counts().rank(ascending=False, method="first") - 1)
        labels[(m, k)] = pd.Series(order.values.astype(int), index=df.index)
res = pd.DataFrame(rows)
res.to_csv(os.path.join(OUT, "model_evaluation.csv"), index=False)
print(res.to_string(index=False))

# sizes of every partition (largest cluster first)
sizes = [{"Model": m, "K": k, "Sizes": "/".join(map(str, sorted(l.value_counts().tolist(), reverse=True)))} for (m, k), l in labels.items()]
pd.DataFrame(sizes).to_csv(os.path.join(OUT, "partition_sizes.csv"), index=False)

# top-priority countries across Model A configurations
top = df.sort_values("priority_score", ascending=False).head(12).index
mem = pd.DataFrame({f"K={k}": labels[("A", k)].loc[top] for k in (2, 3, 4, 5)})
mem.insert(0, "Country", df.loc[top, "country"].values)
mem["Final group"] = df.loc[top, "archetype"].values
mem.to_csv(os.path.join(OUT, "membership_top12.csv"), index=False)

# fixed descriptive bands on 2024 DTP3 and their overlap with the final groups
bands = pd.cut(df["dtp3_2024"], [-1, 59.999, 79.999, 89.999, 101], labels=["Critical (<60%)", "Substantial gap (60-79%)", "Close (80-89%)", "Target met (>=90%)"])
bt = pd.crosstab(bands, df["archetype"])
bt["Total"] = bt.sum(axis=1)
bt.to_csv(os.path.join(OUT, "bands.csv"))
print(bt)

# heat map of standardised group means
cols = p.FEATURES + ["dtp3_2024", "mcv1_2024"] + p.CONTEXT
Z = (df[cols] - df[cols].mean()) / df[cols].std()
H = Z.groupby(df["archetype"]).mean().loc[["Stable high performers", "Mid-level, slow recovery", "Low but improving", "COVID backsliders"]]
H.round(3).to_csv(os.path.join(OUT, "group_means_z.csv"))
nice = {"dtp3_2019": "DTP3 2019", "mcv1_2019": "MCV1 2019", "dtp3_drop": "DTP3 drop", "dtp3_net": "DTP3 net chg", "mcv1_net": "MCV1 net chg",
        "trend_pre": "Pre-COVID trend", "dtp3_2024": "DTP3 2024", "mcv1_2024": "MCV1 2024", "child_mortality": "Child mortality", "gdp_pc": "GDP/person",
        "physicians": "Doctors/1000", "skilled_birth": "Skilled births", "fertility": "Fertility", "rural_share": "Rural share"}
fig, ax = plt.subplots(figsize=(8.5, 3.0), dpi=200)
im = ax.imshow(H.values, cmap="RdYlGn", vmin=-2.5, vmax=2.5, aspect="auto")
ax.set_xticks(range(len(cols))); ax.set_xticklabels([nice[c] for c in cols], rotation=40, ha="right", fontsize=8)
ax.set_yticks(range(4)); ax.set_yticklabels([f"{a}" for a in H.index], fontsize=8)
for i in range(H.shape[0]):
    for j in range(H.shape[1]):
        ax.text(j, i, f"{H.values[i, j]:.1f}", ha="center", va="center", fontsize=7)
fig.colorbar(im, ax=ax, fraction=0.025, pad=0.01).ax.tick_params(labelsize=7)
plt.tight_layout(); plt.savefig(os.path.join(ROOT, "outputs", "figures", "fig_heatmap.png"), bbox_inches="tight"); plt.close()
print("done")
