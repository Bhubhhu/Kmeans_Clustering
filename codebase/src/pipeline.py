"""Post-COVID immunisation recovery: clustering countries by how their vaccination
coverage behaved before, during and after the 2020-22 disruption.

Problem: donors and ministries have limited money. Countries did not all lose or recover
the same way, so one global response is wasteful. We group countries by *trajectory* and
then profile each group with health-system and socio-economic context to suggest what
kind of help each needs.

Run:  python src/pipeline.py
"""
import json
import os

import numpy as np
import pandas as pd
from sklearn.cluster import AgglomerativeClustering, KMeans
from sklearn.decomposition import PCA
from sklearn.metrics import adjusted_rand_score, davies_bouldin_score, silhouette_score
from sklearn.mixture import GaussianMixture
from sklearn.preprocessing import StandardScaler

BASE_YEAR = 2019            # last normal year before COVID-19
SHOCK_YEARS = [2020, 2021, 2022]
LAST_YEAR = 2024            # latest year used for "now"
TARGET = 90.0               # Immunisation Agenda 2030 coverage target for DTP3 / MCV1
K_FINAL = 4
MIN_POPULATION = 100_000    # coverage % of a micro-state rests on a handful of children, so it is too noisy

# Clustering uses only the trajectory of the two vaccines (what happened).
FEATURES = ["dtp3_2019", "mcv1_2019", "dtp3_drop", "dtp3_net", "mcv1_net", "trend_pre"]
# Context is used afterwards to describe the groups (why / who they are).
CONTEXT = ["child_mortality", "gdp_pc", "physicians", "skilled_birth", "fertility", "rural_share"]

STABLE, BACKSLIDE, LOW_UP, MID = (
    "Stable high performers",
    "COVID backsliders",
    "Low but improving",
    "Mid-level, slow recovery",
)
ACTIONS = {
    STABLE: "Maintain routine programme; look for weak districts hidden inside the national average.",
    BACKSLIDE: "Urgent catch-up: re-vaccinate the cohorts missed in 2020-22 and restore routine services.",
    LOW_UP: "Protect the gains: fund routine delivery and outreach to children who have never been reached.",
    MID: "Targeted recovery: defaulter tracking, reminders and outreach to finish started vaccine schedules.",
}


def _load(raw_dir, name):
    d = pd.read_csv(os.path.join(raw_dir, name + ".csv"))
    return d[d["code"].notna() & ~d["code"].astype(str).str.startswith("OWID")]


def _latest(raw_dir, name, col, min_year, max_year=LAST_YEAR):
    d = _load(raw_dir, name)
    d = d[(d["year"] >= min_year) & (d["year"] <= max_year)].dropna(subset=[col])
    return d.sort_values("year").groupby("code")[col].last()


def build_dataset(raw_dir):
    """Return (features+context table, time-series table)."""
    dtp = _load(raw_dir, "dtp3")
    mcv = _load(raw_dir, "mcv1")
    dt = dtp.pivot(index="code", columns="year", values="coverage__antigen_dtpcv3")
    mc = mcv.pivot(index="code", columns="year", values="coverage__antigen_mcv1")

    f = pd.DataFrame(index=dt.index)
    f["dtp3_2019"] = dt[BASE_YEAR]
    f["mcv1_2019"] = mc[BASE_YEAR]
    f["dtp3_drop"] = dt[SHOCK_YEARS].min(axis=1) - dt[BASE_YEAR]   # worst loss during the shock
    f["dtp3_net"] = dt[LAST_YEAR] - dt[BASE_YEAR]                 # still lost (<0) or regained (>0)
    f["mcv1_net"] = mc[LAST_YEAR] - mc[BASE_YEAR]
    pre = dt.loc[:, BASE_YEAR - 9:BASE_YEAR]
    f["trend_pre"] = pre.apply(lambda r: np.polyfit(range(len(r)), r.values, 1)[0] if r.notna().sum() > 5 else np.nan, axis=1)
    f["dtp3_2024"] = dt[LAST_YEAR]
    f["mcv1_2024"] = mc[LAST_YEAR]
    f = f.dropna(subset=FEATURES + ["dtp3_2024"])

    names = dtp.drop_duplicates("code").set_index("code")["entity"]
    f.insert(0, "country", names.reindex(f.index))

    gdp = _load(raw_dir, "gdp_pc")
    region = gdp.dropna(subset=["owid_region"]).drop_duplicates("code").set_index("code")["owid_region"]
    f["region"] = region.reindex(f.index).fillna("Other")

    pop = _load(raw_dir, "population")
    pop = pop[pop["year"] == LAST_YEAR].set_index("code")
    urb = pop["population__area_type_urban__data_type_estimates"]
    rur = pop["population__area_type_rural__data_type_estimates"]
    f["population"] = (urb + rur).reindex(f.index)
    f["rural_share"] = (100 * rur / (urb + rur)).reindex(f.index)

    f = f[f["population"] >= MIN_POPULATION].copy()   # also drops territories with no population figure

    f["child_mortality"] = _latest(raw_dir, "child_mortality", "probability_of_death_under_5", 2010, 2019).reindex(f.index)
    f["gdp_pc"] = _latest(raw_dir, "gdp_pc", "ny_gdp_pcap_pp_kd", 2015).reindex(f.index)
    f["physicians"] = _latest(raw_dir, "physicians", "sh_med_phys_zs", 2005).reindex(f.index)
    f["skilled_birth"] = _latest(raw_dir, "skilled_birth", "sh_sta_brtc_zs", 2005).reindex(f.index)
    f["fertility"] = _latest(raw_dir, "fertility", "fertility_rate_hist", 2015).reindex(f.index)

    # Priority: how far below the 90% target now, plus coverage still lost since 2019.
    f["gap_to_target"] = (TARGET - f["dtp3_2024"]).clip(lower=0).round(1)
    f["priority_score"] = (f["gap_to_target"] + (-f["dtp3_net"]).clip(lower=0)).round(1)

    ts = pd.DataFrame({"dtp3": dtp.set_index(["code", "year"])["coverage__antigen_dtpcv3"],
                       "mcv1": mcv.set_index(["code", "year"])["coverage__antigen_mcv1"]}).reset_index()
    ts = ts[ts["code"].isin(f.index) & (ts["year"] >= 2000)]
    return f, ts


def evaluate_k(X, k_values=range(2, 9)):
    rows = []
    for k in k_values:
        km = KMeans(k, init="k-means++", n_init=20, random_state=42).fit(X)
        aris = [adjusted_rand_score(km.labels_, KMeans(k, n_init=10, random_state=s).fit_predict(X)) for s in range(100, 115)]
        rows.append({"K": k, "WCSS": round(km.inertia_, 2),
                     "Silhouette": round(silhouette_score(X, km.labels_), 4),
                     "Davies_Bouldin": round(davies_bouldin_score(X, km.labels_), 4),
                     "Seed_Stability_ARI": round(float(np.mean(aris)), 4)})
    return pd.DataFrame(rows)


def compare_methods(X, k):
    """K-Means vs Ward hierarchical vs Gaussian mixture on the same data and K."""
    km = KMeans(k, init="k-means++", n_init=30, random_state=42).fit_predict(X)
    ward = AgglomerativeClustering(n_clusters=k, linkage="ward").fit_predict(X)
    gmm = GaussianMixture(k, covariance_type="full", n_init=10, random_state=42).fit(X).predict(X)
    rows = []
    for name, lab in [("K-Means (final)", km), ("Ward hierarchical", ward), ("Gaussian mixture", gmm)]:
        rows.append({"Method": name,
                     "Silhouette": round(silhouette_score(X, lab), 4),
                     "Davies_Bouldin": round(davies_bouldin_score(X, lab), 4),
                     "ARI_vs_KMeans": round(adjusted_rand_score(km, lab), 4)})
    return pd.DataFrame(rows)


def name_clusters(prof):
    """Give each cluster a meaningful name from its own averages (never from its numeric id)."""
    names, left = {}, set(prof.index)
    c = prof["dtp3_net"].idxmin(); names[c] = BACKSLIDE; left.discard(c)
    if left:
        c = prof.loc[list(left), "dtp3_2024"].idxmax(); names[c] = STABLE; left.discard(c)
    if left:
        c = prof.loc[list(left), "dtp3_2019"].idxmin(); names[c] = LOW_UP; left.discard(c)
    for c in left:
        names[c] = MID if list(names.values()).count(MID) == 0 else f"{MID} ({c})"
    return names


def run(raw_dir, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    df, ts = build_dataset(raw_dir)
    X = StandardScaler().fit_transform(df[FEATURES])

    validation = evaluate_k(X)
    methods = compare_methods(X, K_FINAL)

    km = KMeans(K_FINAL, init="k-means++", n_init=30, random_state=42).fit(X)
    df["cluster"] = km.labels_
    prof = df.groupby("cluster")[FEATURES + ["dtp3_2024", "mcv1_2024"]].mean()
    names = name_clusters(prof)
    df["archetype"] = df["cluster"].map(names)
    df["suggested_focus"] = df["archetype"].map(lambda a: ACTIONS.get(a, ACTIONS[MID]))

    pca = PCA(n_components=2, random_state=42)
    xy = pca.fit_transform(X)
    df["pca1"], df["pca2"] = xy[:, 0].round(4), xy[:, 1].round(4)
    loadings = pd.DataFrame(pca.components_.T, index=FEATURES, columns=["PC1", "PC2"]).round(4).reset_index(names="feature")

    # Context profile of each archetype (medians are robust to the few extreme countries).
    summary = df.groupby("archetype").agg(
        countries=("country", "size"),
        dtp3_2019=("dtp3_2019", "mean"), dtp3_2024=("dtp3_2024", "mean"), dtp3_net=("dtp3_net", "mean"),
        mcv1_2024=("mcv1_2024", "mean"),
        **{c: (c, "median") for c in CONTEXT}).round(1).reset_index()
    summary["suggested_focus"] = summary["archetype"].map(lambda a: ACTIONS.get(a, ACTIONS[MID]))

    # Look-alike peers: nearest countries in the clustering space that regained more coverage.
    from sklearn.neighbors import NearestNeighbors
    nn = NearestNeighbors(n_neighbors=15).fit(X)
    _, idx = nn.kneighbors(X)
    peers = {}
    for i, code in enumerate(df.index):
        cand = [df.index[j] for j in idx[i][1:] if df["dtp3_net"].iloc[j] > df["dtp3_net"].iloc[i] + 3]
        peers[code] = cand[:3]
    df["recovered_peers"] = [", ".join(df.loc[p, "country"]) for p in peers.values()]

    df.reset_index(names="code").round(3).to_csv(os.path.join(out_dir, "country_archetypes.csv"), index=False)
    ts.to_csv(os.path.join(out_dir, "timeseries.csv"), index=False)
    validation.to_csv(os.path.join(out_dir, "k_validation.csv"), index=False)
    methods.to_csv(os.path.join(out_dir, "method_comparison.csv"), index=False)
    summary.to_csv(os.path.join(out_dir, "archetype_summary.csv"), index=False)
    loadings.to_csv(os.path.join(out_dir, "pca_loadings.csv"), index=False)

    back = df[df["archetype"] == BACKSLIDE]
    info = {
        "countries": int(len(df)),
        "pca_variance": [round(float(v) * 100, 2) for v in pca.explained_variance_ratio_],
        "silhouette_final": round(float(silhouette_score(X, km.labels_)), 4),
        "davies_bouldin_final": round(float(davies_bouldin_score(X, km.labels_)), 4),
        "below_pre_covid": int((df["dtp3_net"] < 0).sum()),
        "below_target": int((df["dtp3_2024"] < TARGET).sum()),
        "backsliders": int(len(back)),
        "backslider_avg_loss": round(float(back["dtp3_net"].mean()), 1) if len(back) else 0.0,
    }
    with open(os.path.join(out_dir, "summary.json"), "w") as fh:
        json.dump(info, fh, indent=2)
    return df, info


if __name__ == "__main__":
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    _, info = run(os.path.join(root, "data", "raw"), os.path.join(root, "outputs"))
    print(json.dumps(info, indent=2))
