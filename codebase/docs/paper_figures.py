"""Single-column (3.45 in) figures for the IEEE-style paper.  Run from codebase/:  python docs/paper_figures.py"""
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.patches import FancyBboxPatch

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "outputs")
FIG = os.path.join(OUT, "paper")
os.makedirs(FIG, exist_ok=True)
plt.rcParams.update({"font.family": "serif", "font.serif": ["Times New Roman", "DejaVu Serif"], "font.size": 7,
                     "axes.spines.top": False, "axes.spines.right": False, "axes.linewidth": 0.6})
COL = {"Stable high performers": "#2a9d8f", "Mid-level, slow recovery": "#e9a23b", "Low but improving": "#3b82c4", "COVID backsliders": "#d1495b"}
W = 3.45

df = pd.read_csv(os.path.join(OUT, "country_archetypes.csv"))
ts = pd.read_csv(os.path.join(OUT, "timeseries.csv")).merge(df[["code", "archetype"]], on="code")


def save(name):
    plt.savefig(os.path.join(FIG, name), dpi=300, bbox_inches="tight", pad_inches=0.03)
    plt.close()


# Fig 1: architecture
fig, ax = plt.subplots(figsize=(W, 4.3)); ax.axis("off"); ax.set_xlim(0, 10); ax.set_ylim(-0.7, 13.2)


def box(x, y, w, h, text, fc="#e8f4f2", ec="#2a9d8f", fs=6.3):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.05,rounding_size=0.15", fc=fc, ec=ec, lw=0.8))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=fs, linespacing=1.25)


def arrow(x, y1, y2):
    ax.annotate("", xy=(x, y2), xytext=(x, y1), arrowprops=dict(arrowstyle="-|>", lw=0.8, color="#264653", mutation_scale=7))


box(0.5, 11.3, 9, 1.6, "1. Data ingestion\nWUENIC DTP3 and MCV1 (2000-2025) + six context series\n201 countries")
arrow(5, 11.3, 10.4)
box(0.5, 8.9, 9, 1.5, "2. Cleaning and filtering\ncomplete trajectories (n = 200), population >= 100,000 (n = 182)")
arrow(5, 8.9, 8.0)
box(0.5, 6.5, 9, 1.5, "3. Feature construction and z-score standardisation\nsix trajectory features (2019 level, shock, net change, trend)")
for x in (1.6, 5.0, 8.4):
    arrow(x, 6.5, 5.6)
box(0.3, 4.4, 2.8, 1.2, "Model A\n6 features", fc="#fdf1dd", ec="#e9a23b")
box(3.6, 4.4, 2.8, 1.2, "Model B\n5 features\n(correlation-pruned)", fc="#fdf1dd", ec="#e9a23b", fs=5.6)
box(6.9, 4.4, 2.8, 1.2, "Model C\n5 features\n(trend removed)", fc="#fdf1dd", ec="#e9a23b", fs=5.6)
for x in (1.7, 5.0, 8.3):
    arrow(x, 4.4, 3.5)
box(0.5, 2.0, 9, 1.5, "4. K-Means (K = 2 ... 6) and validation\nWCSS, silhouette, Davies-Bouldin, 20-seed ARI")
arrow(5, 2.0, 1.1)
box(0.5, -0.4, 9, 1.5, "5. Baseline (Model A, K = 4), PCA, group profiles,\npriority score, look-alike peers, dashboard", fc="#e3ecf7", ec="#3b82c4")
save("fig1_architecture.png")

# Fig 2: PCA scatter
fig, ax = plt.subplots(figsize=(W, 2.5))
for a, c in COL.items():
    s = df[df["archetype"] == a]
    ax.scatter(s["pca1"], s["pca2"], color=c, s=11, alpha=0.85, edgecolor="k", lw=0.25, label=f"{a} ({len(s)})")
for n in ["Sudan", "Lebanon", "Nigeria", "Brazil"]:
    r = df[df["country"] == n].iloc[0]
    ax.annotate(n, (r["pca1"], r["pca2"]), fontsize=5.5, xytext=(3, 3), textcoords="offset points")
ax.set_xlabel("PC1 (35.21% of variance)"); ax.set_ylabel("PC2 (31.78% of variance)")
ax.legend(frameon=False, fontsize=5.6, loc="lower left", handletextpad=0.2)
save("fig2_pca.png")

# Fig 3: trajectories
fig, ax = plt.subplots(figsize=(W, 2.45))
m = ts[ts["year"] >= 2010].groupby(["archetype", "year"])["dtp3"].mean().reset_index()
for a, c in COL.items():
    s = m[m["archetype"] == a]
    ax.plot(s["year"], s["dtp3"], color=c, lw=1.5, marker="o", ms=2, label=a)
ax.axvspan(2019.5, 2022.5, color="grey", alpha=0.15); ax.axhline(90, ls="--", color="#777", lw=0.7)
ax.text(2010.2, 91, "90% target", fontsize=5.5, color="#555"); ax.text(2021, 38, "COVID-19\ndisruption", ha="center", fontsize=5.5, color="#555")
ax.set_ylim(35, 100); ax.set_ylabel("Mean DTP3 coverage (%)"); ax.legend(frameon=False, fontsize=5.4, loc="lower left", bbox_to_anchor=(0, 0.1))
save("fig3_trajectories.png")

# Fig 4: priority countries
top = df.sort_values("priority_score", ascending=False).head(12).iloc[::-1]
fig, ax = plt.subplots(figsize=(W, 2.7))
for i, (_, r) in enumerate(top.iterrows()):
    ax.plot([r["dtp3_2024"], r["dtp3_2019"]], [i, i], color="#bbb", lw=1.2, zorder=1)
    ax.scatter(r["dtp3_2019"], i, color="#888", s=14, zorder=2)
    ax.scatter(r["dtp3_2024"], i, color=COL[r["archetype"]], s=22, zorder=3)
ax.set_yticks(range(len(top))); ax.set_yticklabels(top["country"], fontsize=6); ax.axvline(90, ls="--", color="#777", lw=0.7)
ax.set_xlabel("DTP3 coverage (%): grey = 2019, coloured = 2024"); ax.set_xlim(30, 100)
save("fig4_priority.png")

# Fig 5: heat map of standardised group means (indicators as rows)
cols = ["dtp3_2019", "mcv1_2019", "dtp3_drop", "dtp3_net", "mcv1_net", "trend_pre", "dtp3_2024", "mcv1_2024",
        "child_mortality", "gdp_pc", "physicians", "skilled_birth", "fertility", "rural_share"]
nice = ["DTP3 2019", "MCV1 2019", "DTP3 shock drop", "DTP3 net change", "MCV1 net change", "Pre-COVID trend", "DTP3 2024", "MCV1 2024",
        "Child mortality", "GDP per person", "Doctors per 1,000", "Skilled births", "Fertility", "Rural share"]
Z = (df[cols] - df[cols].mean()) / df[cols].std()
H = Z.groupby(df["archetype"]).mean().loc[list(COL)].T
fig, ax = plt.subplots(figsize=(W, 3.5))
im = ax.imshow(H.values, cmap="RdYlGn", vmin=-2.5, vmax=2.5, aspect="auto")
ax.set_yticks(range(len(cols))); ax.set_yticklabels(nice, fontsize=6)
ax.set_xticks(range(4)); ax.set_xticklabels(["Stable\nhigh", "Mid-level\nslow rec.", "Low but\nimproving", "COVID\nbacksliders"], fontsize=5.8)
for i in range(H.shape[0]):
    for j in range(H.shape[1]):
        ax.text(j, i, f"{H.values[i, j]:.1f}", ha="center", va="center", fontsize=5.8)
cb = fig.colorbar(im, ax=ax, fraction=0.04, pad=0.02); cb.ax.tick_params(labelsize=5.5)
ax.spines[:].set_visible(False)
save("fig5_heatmap.png")
print(sorted(os.listdir(FIG)))
