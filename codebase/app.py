"""Streamlit dashboard: post-COVID childhood immunisation recovery."""
import json
import os

import pandas as pd
import plotly.express as px
import streamlit as st

from src.pipeline import (BACKSLIDE, BASE_YEAR, CONTEXT, LAST_YEAR, LOW_UP, MID, STABLE, TARGET, run)

st.set_page_config(page_title="Vaccination recovery after COVID-19", layout="wide")

BASE = os.path.dirname(os.path.abspath(__file__))
RAW, OUT = os.path.join(BASE, "data", "raw"), os.path.join(BASE, "outputs")
COLORS = {STABLE: "#2a9d8f", MID: "#e9a23b", LOW_UP: "#3b82c4", BACKSLIDE: "#d1495b"}
LABELS = {"child_mortality": "Under-5 death risk (%)", "gdp_pc": "GDP per person (PPP $)",
          "physicians": "Doctors per 1,000 people", "skilled_birth": "Births with skilled staff (%)",
          "fertility": "Children per woman", "rural_share": "Rural population (%)"}


@st.cache_data
def load():
    if not os.path.exists(os.path.join(OUT, "country_archetypes.csv")):
        run(RAW, OUT)
    r = lambda n: pd.read_csv(os.path.join(OUT, n))
    with open(os.path.join(OUT, "summary.json")) as fh:
        info = json.load(fh)
    return (r("country_archetypes.csv"), r("timeseries.csv"), r("archetype_summary.csv"),
            r("k_validation.csv"), r("method_comparison.csv"), info)


df, ts, summ, kval, meth, info = load()
df["recovered_peers"] = df["recovered_peers"].fillna("")

st.title("Which countries are still behind on childhood vaccination after COVID-19, and what do they need?")
st.markdown(
    f"In 2020-22 routine vaccination was disrupted almost everywhere, but countries did not lose or regain ground in the same way. "
    f"A single global response wastes money. This tool groups **{info['countries']} countries** by how their DTP3 and measles "
    f"coverage behaved before ({BASE_YEAR}), during and after the disruption (to {LAST_YEAR}), then suggests what kind of help each group needs. "
    f"Data: WHO/UNICEF WUENIC coverage estimates plus World Bank / UN context indicators.")

c1, c2, c3, c4 = st.columns(4)
c1.metric("Countries analysed", info["countries"])
c2.metric(f"Still below {BASE_YEAR} DTP3 level", info["below_pre_covid"])
c3.metric(f"Below {TARGET:.0f}% target in {LAST_YEAR}", info["below_target"])
c4.metric("Severe backsliders", info["backsliders"], f"{info['backslider_avg_loss']:+.0f} pts since {BASE_YEAR}")

tab_map, tab_country, tab_list, tab_groups, tab_method = st.tabs(
    ["World map", "Country report", "Priority list", "The four groups", "Method and limits"])

with tab_map:
    fig = px.choropleth(df, locations="code", color="archetype", hover_name="country",
                        hover_data={"code": False, "dtp3_2019": True, "dtp3_2024": True, "dtp3_net": True},
                        color_discrete_map=COLORS, labels={"archetype": "Group", "dtp3_2019": f"DTP3 {BASE_YEAR} (%)",
                                                           "dtp3_2024": f"DTP3 {LAST_YEAR} (%)", "dtp3_net": "Change (pts)"})
    fig.update_geos(projection_type="natural earth", projection_rotation_lon=10, showframe=False,
                    bgcolor="rgba(0,0,0,0)", lataxis_range=[-58, 85], landcolor="#cccccc", showland=True)
    fig.update_layout(margin=dict(l=0, r=0, t=0, b=0), legend_title_text="", height=520)
    st.plotly_chart(fig, width="stretch", config={"topojsonURL": "/app/static/"})  # map outline is bundled, no CDN needed
    st.caption("Countries under 100,000 people are left out because their percentages rest on very few children.")

with tab_country:
    names = sorted(df["country"])
    name = st.selectbox("Choose a country", names, index=names.index("Nigeria") if "Nigeria" in names else 0)
    row = df[df["country"] == name].iloc[0]
    a, b, c, d = st.columns(4)
    a.metric(f"DTP3 {BASE_YEAR}", f"{row['dtp3_2019']:.0f}%")
    b.metric(f"DTP3 {LAST_YEAR}", f"{row['dtp3_2024']:.0f}%", f"{row['dtp3_net']:+.0f} pts")
    c.metric("Gap to 90% target", f"{row['gap_to_target']:.0f} pts")
    d.metric("Group", row["archetype"])
    st.info(f"**Suggested focus:** {row['suggested_focus']}")
    t = ts[ts["code"] == row["code"]].melt(id_vars=["code", "year"], value_vars=["dtp3", "mcv1"], var_name="vaccine", value_name="coverage")
    t["vaccine"] = t["vaccine"].map({"dtp3": "DTP3", "mcv1": "Measles (MCV1)"})
    lf = px.line(t, x="year", y="coverage", color="vaccine", markers=True, labels={"coverage": "Coverage (%)", "year": ""})
    lf.add_hline(y=TARGET, line_dash="dash", annotation_text="90% target")
    lf.add_vrect(x0=2019.5, x1=2022.5, fillcolor="grey", opacity=0.12, line_width=0, annotation_text="COVID disruption")
    lf.update_yaxes(range=[0, 100])
    st.plotly_chart(lf, width="stretch")
    if row["recovered_peers"]:
        st.write(f"**Look-alike countries that regained more coverage (worth learning from):** {row['recovered_peers']}")
    grp = summ[summ["archetype"] == row["archetype"]].iloc[0]
    ctx = pd.DataFrame({"Indicator": [LABELS[k] for k in CONTEXT],
                        name: [row[k] for k in CONTEXT],
                        f"Typical for '{row['archetype']}'": [grp[k] for k in CONTEXT]}).round(1)
    st.dataframe(ctx, hide_index=True, width="stretch")

with tab_list:
    st.write("Ranked by **priority score** = points below the 90% target now + points still lost since 2019. "
             "It shows where coverage is both low and slipping; it is a starting list, not a funding formula.")
    regions = st.multiselect("Region", sorted(df["region"].unique()), default=sorted(df["region"].unique()))
    groups = st.multiselect("Group", list(COLORS), default=list(COLORS))
    top = st.slider("Show top", 5, 60, 25)
    view = df[df["region"].isin(regions) & df["archetype"].isin(groups)].sort_values("priority_score", ascending=False).head(top)
    cols = ["country", "region", "archetype", "dtp3_2019", "dtp3_2024", "dtp3_net", "mcv1_2024", "priority_score", "suggested_focus"]
    st.dataframe(view[cols], hide_index=True, width="stretch")
    st.download_button("Download this list (CSV)", view[cols].to_csv(index=False), "priority_countries.csv", "text/csv")

with tab_groups:
    st.write("Each group is described by its own averages. Names are generated from those averages, not typed in by hand.")
    show = summ.rename(columns={"archetype": "Group", "countries": "Countries", "dtp3_2019": f"DTP3 {BASE_YEAR}", "dtp3_2024": f"DTP3 {LAST_YEAR}",
                                "dtp3_net": "Change (pts)", "mcv1_2024": f"Measles {LAST_YEAR}", **LABELS})
    st.dataframe(show.drop(columns="suggested_focus"), hide_index=True, width="stretch")
    for _, g in summ.iterrows():
        st.markdown(f"**{g['archetype']}**: {g['suggested_focus']}")
    sc = px.scatter(df, x="pca1", y="pca2", color="archetype", hover_name="country", color_discrete_map=COLORS,
                    labels={"pca1": f"PC1 ({info['pca_variance'][0]:.0f}% of variation)", "pca2": f"PC2 ({info['pca_variance'][1]:.0f}% of variation)", "archetype": "Group"})
    st.plotly_chart(sc, width="stretch")
    st.caption("Two-dimensional view of the six trajectory features. PCA is only used to draw this picture; the clusters are found in all six dimensions.")

with tab_method:
    st.markdown("""
**Features used for clustering (what happened):** DTP3 and measles coverage in 2019, the worst DTP3 drop in 2020-22,
net change in DTP3 and measles from 2019 to 2024, and the 2010-19 DTP3 trend. All are standardised first.
**Context used afterwards to describe groups (why):** child mortality, income, doctors, skilled birth attendance, fertility, rural share.

**Algorithm:** K-Means (k-means++, 30 restarts), K = 4. It was checked against Ward hierarchical clustering and a Gaussian mixture.
""")
    m1, m2 = st.columns(2)
    m1.plotly_chart(px.line(kval, x="K", y="WCSS", markers=True, title="Elbow: within-cluster spread"), width="stretch")
    m2.plotly_chart(px.line(kval, x="K", y=["Silhouette", "Seed_Stability_ARI"], markers=True, title="Silhouette and stability"), width="stretch")
    st.dataframe(kval, hide_index=True, width="stretch")
    st.dataframe(meth, hide_index=True, width="stretch")
    st.markdown(f"""
**Why K = 4?** K = 3 scores a slightly higher silhouette, but K = 4 separates the *severe backsliders* from the
*mid-level, slow recovery* group. Those need different help (urgent catch-up vs. steady recovery work).
Final model: silhouette {info['silhouette_final']}, Davies-Bouldin {info['davies_bouldin_final']}.

**Limits you should know**
- National averages hide weak districts. This is a first filter, not a district plan.
- Coverage figures are WHO/UNICEF *estimates*, and recent years can still be revised.
- Groups describe *what happened*, not *why*. War, funding cuts or data problems are not in the data.
- The severe-backslider group is small (a handful of countries), so its average moves with each member.
- Micro-states under 100,000 people are excluded; 2024 is treated as the latest year.
- Labels like "backslider" are for prioritising support, not for ranking or blaming countries.
""")
