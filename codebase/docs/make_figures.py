"""Figures for the report and slides, drawn from outputs/*.csv.  Run: python docs/make_figures.py"""
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.patches import FancyBboxPatch

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT, FIG = os.path.join(ROOT, "outputs"), os.path.join(ROOT, "outputs", "figures")
COL = {"Stable high performers": "#2a9d8f", "Mid-level, slow recovery": "#e9a23b",
       "Low but improving": "#3b82c4", "COVID backsliders": "#d1495b"}
plt.rcParams.update({"font.size": 11, "axes.spines.top": False, "axes.spines.right": False, "figure.dpi": 200})

df = pd.read_csv(os.path.join(OUT, "country_archetypes.csv"))
ts = pd.read_csv(os.path.join(OUT, "timeseries.csv")).merge(df[["code", "archetype"]], on="code")
kval = pd.read_csv(os.path.join(OUT, "k_validation.csv"))
summ = pd.read_csv(os.path.join(OUT, "archetype_summary.csv"))


def save(name):
    plt.tight_layout(); plt.savefig(os.path.join(FIG, name), bbox_inches="tight"); plt.close()


# 1. average DTP3 trajectory of each group
fig, ax = plt.subplots(figsize=(9, 4.6))
m = ts[ts["year"] >= 2010].groupby(["archetype", "year"])["dtp3"].mean().reset_index()
for a, c in COL.items():
    s = m[m["archetype"] == a]
    ax.plot(s["year"], s["dtp3"], color=c, lw=2.6, marker="o", ms=4, label=f"{a} (n={int((df['archetype'] == a).sum())})")
ax.axvspan(2019.5, 2022.5, color="grey", alpha=0.15); ax.text(2021, 41, "COVID-19\ndisruption", ha="center", fontsize=9, color="#555")
ax.axhline(90, ls="--", color="#777", lw=1); ax.text(2010.1, 91, "90% target", fontsize=9, color="#555")
ax.set_ylim(35, 100); ax.set_ylabel("Average DTP3 coverage (%)"); ax.legend(frameon=False, fontsize=9, loc="lower left", bbox_to_anchor=(0.0, 0.08))
save("fig_trajectories.png")

# 2. top-priority countries: 2019 vs 2024
top = df.sort_values("priority_score", ascending=False).head(12).iloc[::-1]
fig, ax = plt.subplots(figsize=(8, 5))
for i, (_, r) in enumerate(top.iterrows()):
    ax.plot([r["dtp3_2024"], r["dtp3_2019"]], [i, i], color="#bbb", lw=2, zorder=1)
    ax.scatter(r["dtp3_2019"], i, color="#888", s=45, zorder=2)
    ax.scatter(r["dtp3_2024"], i, color=COL[r["archetype"]], s=70, zorder=3)
ax.set_yticks(range(len(top))); ax.set_yticklabels(top["country"]); ax.axvline(90, ls="--", color="#777", lw=1)
ax.set_xlabel("DTP3 coverage (%)   grey dot = 2019, coloured dot = 2024"); ax.set_xlim(30, 100)
save("fig_priority.png")

# 3. validation
fig, axs = plt.subplots(1, 2, figsize=(10, 3.8))
axs[0].plot(kval["K"], kval["WCSS"], "o-", color="#264653", lw=2); axs[0].axvline(4, color="#d1495b", ls="--")
axs[0].set_xlabel("Number of clusters K"); axs[0].set_ylabel("WCSS (lower = tighter)"); axs[0].set_title("Elbow", fontsize=11)
axs[1].plot(kval["K"], kval["Silhouette"], "o-", color="#2a9d8f", lw=2, label="Silhouette")
axs[1].plot(kval["K"], kval["Seed_Stability_ARI"], "s--", color="#e9a23b", lw=2, label="Seed stability (ARI)")
axs[1].axvline(4, color="#d1495b", ls="--"); axs[1].set_xlabel("Number of clusters K"); axs[1].legend(frameon=False, fontsize=9)
axs[1].set_title("Silhouette and stability", fontsize=11)
save("fig_validation.png")

# 4. PCA scatter
fig, ax = plt.subplots(figsize=(7.5, 5))
for a, c in COL.items():
    s = df[df["archetype"] == a]; ax.scatter(s["pca1"], s["pca2"], color=c, s=40, alpha=0.85, edgecolor="k", lw=0.3, label=a)
for n in ["Sudan", "Lebanon", "Nigeria", "Brazil"]:
    r = df[df["country"] == n].iloc[0]; ax.annotate(n, (r["pca1"], r["pca2"]), fontsize=8, xytext=(4, 4), textcoords="offset points")
ax.set_xlabel("PC1 (35% of variation)"); ax.set_ylabel("PC2 (32% of variation)"); ax.legend(frameon=False, fontsize=8)
save("fig_pca.png")

# 5. context by group
items = [("child_mortality", "Under-5 death risk (%)"), ("physicians", "Doctors per 1,000"),
         ("skilled_birth", "Births with skilled staff (%)"), ("gdp_pc", "GDP per person (PPP $)")]
fig, axs = plt.subplots(1, 4, figsize=(12, 3.4)); order = list(COL)
for ax, (k, t) in zip(axs, items):
    v = [float(summ[summ["archetype"] == a][k].iloc[0]) for a in order]
    ax.bar(range(4), v, color=[COL[a] for a in order]); ax.set_title(t, fontsize=10); ax.set_xticks([])
fig.legend(handles=[plt.Rectangle((0, 0), 1, 1, color=COL[a]) for a in order], labels=order, loc="lower center", ncol=4, frameon=False, fontsize=9)
plt.tight_layout(rect=(0, 0.1, 1, 1)); plt.savefig(os.path.join(FIG, "fig_context.png"), bbox_inches="tight"); plt.close()

# 6. pipeline
steps = ["Real data\n(WHO/UNICEF,\nWorld Bank, UN)", "Features\n(2019 level, drop,\nchange, trend)", "Standardise\n+ filter\nmicro-states", "K-Means\nK = 4\n(+ checks)", "Name groups\n+ context\nprofile", "Dashboard\n+ priority list"]
fig, ax = plt.subplots(figsize=(12, 2.2)); ax.axis("off"); ax.set_xlim(0, 12); ax.set_ylim(0, 2)
for i, s in enumerate(steps):
    x = i * 2 + 0.1
    ax.add_patch(FancyBboxPatch((x, 0.35), 1.6, 1.3, boxstyle="round,pad=0.03", fc="#e8f4f2", ec="#2a9d8f", lw=1.5))
    ax.text(x + 0.8, 1.0, s, ha="center", va="center", fontsize=9)
    if i < 5: ax.annotate("", xy=(x + 1.95, 1.0), xytext=(x + 1.65, 1.0), arrowprops=dict(arrowstyle="-|>", color="#264653"))
save("fig_pipeline.png")
print("figures:", sorted(os.listdir(FIG)))
