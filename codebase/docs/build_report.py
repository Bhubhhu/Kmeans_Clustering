"""Builds Project_Report.pdf from the real outputs.  Run: python docs/build_report.py"""
import json
import os

import pandas as pd
from PIL import Image as PILImage
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Image, KeepTogether, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT, FIG = os.path.join(ROOT, "outputs"), os.path.join(ROOT, "outputs", "figures")
PDF = os.path.join(os.path.dirname(ROOT), "Project_Report.pdf")

df = pd.read_csv(os.path.join(OUT, "country_archetypes.csv"))
summ = pd.read_csv(os.path.join(OUT, "archetype_summary.csv")).set_index("archetype")
kval = pd.read_csv(os.path.join(OUT, "k_validation.csv"))
meth = pd.read_csv(os.path.join(OUT, "method_comparison.csv"))
info = json.load(open(os.path.join(OUT, "summary.json")))
order = ["Stable high performers", "Mid-level, slow recovery", "Low but improving", "COVID backsliders"]

ss = getSampleStyleSheet()
BODY = ParagraphStyle("b", parent=ss["BodyText"], fontSize=10.5, leading=15, spaceAfter=7)
H1 = ParagraphStyle("h1", parent=ss["Heading1"], fontSize=16, spaceBefore=14, spaceAfter=8, keepWithNext=1, textColor=colors.HexColor("#1f4e5f"))
H2 = ParagraphStyle("h2", parent=ss["Heading2"], fontSize=12.5, spaceBefore=10, spaceAfter=5, keepWithNext=1, textColor=colors.HexColor("#264653"))
CAP = ParagraphStyle("c", parent=BODY, fontSize=9, leading=12, textColor=colors.HexColor("#555555"), alignment=TA_CENTER)
BUL = ParagraphStyle("bu", parent=BODY, leftIndent=14, bulletIndent=4, spaceAfter=3)
CELL = ParagraphStyle("cell", parent=BODY, fontSize=8.8, leading=11, spaceAfter=0)
CTR = ParagraphStyle("ctr", parent=BODY, alignment=TA_CENTER)


def P(t, s=BODY):
    return Paragraph(t, s)


def B(items):
    return [Paragraph(i, BUL, bulletText="•") for i in items]


def img(name, w=15.5):
    iw, ih = PILImage.open(os.path.join(FIG, name)).size
    return Image(os.path.join(FIG, name), width=w * cm, height=w * cm * ih / iw)


def table(rows, widths):
    rows = [[Paragraph(str(c), CELL) for c in r] for r in rows]
    t = Table(rows, colWidths=[w * cm for w in widths], repeatRows=1)
    t.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#b8c4c2")), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                           ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                           ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#dcebe8"))]))
    return KeepTogether(t)


def footer(c, d):
    c.saveState()
    c.setFont("Helvetica", 8)
    c.setFillColor(colors.grey)
    c.drawString(2 * cm, 1.2 * cm, "Post-COVID immunisation recovery: clustering countries by trajectory")
    c.drawRightString(A4[0] - 2 * cm, 1.2 * cm, f"Page {d.page}")
    c.restoreState()


def g(a, k):
    return summ.loc[a, k]


def kv(k, col):
    return kval.loc[kval.K == k, col].iloc[0]


S = []
# ---- title page
S += [Spacer(1, 3.5 * cm),
      P("Which Countries Are Still Behind on Childhood Vaccination After COVID-19, and What Do They Need?",
        ParagraphStyle("t", parent=H1, fontSize=22, leading=28, alignment=TA_CENTER)),
      Spacer(1, 0.6 * cm),
      P("Unsupervised clustering of countries by their vaccination recovery pattern",
        ParagraphStyle("s", parent=BODY, fontSize=13, alignment=TA_CENTER, textColor=colors.HexColor("#555555"))),
      Spacer(1, 2 * cm),
      P("Problem Statement ID: BMGF-GAVI-WHO-CLUST-2026", CTR),
      P("Group members: RegNo1 (12104501), RegNo2 (12104502), RegNo3 (12104503)", CTR),
      P("Code and data: github.com/Bhubhhu/Kmeans_Clustering", CTR), PageBreak()]

# ---- abstract
S += [P("Abstract", H1), P(
    f"Routine childhood vaccination fell almost everywhere in 2020-22. Some countries regained their pre-pandemic coverage, others did not, "
    f"and a few collapsed. Funders and health ministries have limited money, so they need to know which countries need which kind of help. "
    f"This project clusters <b>{info['countries']} countries</b> using real WHO/UNICEF coverage estimates for DTP3 and measles vaccines. "
    f"Each country is described by six trajectory features: its 2019 coverage, its worst drop in 2020-22, its net change by 2024, and its pre-COVID trend. "
    f"K-Means with K = 4 finds four groups: <b>stable high performers</b> ({int(g(order[0], 'countries'))} countries), <b>mid-level with slow recovery</b> "
    f"({int(g(order[1], 'countries'))}), <b>low but improving</b> ({int(g(order[2], 'countries'))}) and <b>severe COVID backsliders</b> ({int(g(order[3], 'countries'))}: "
    f"Sudan, Lebanon, Myanmar, Mozambique and Vanuatu). {info['below_pre_covid']} of the {info['countries']} countries are still below their 2019 DTP3 level, "
    f"and {info['below_target']} are below the 90% target. Health-system and socio-economic indicators are used afterwards to describe each group, "
    f"and the result is delivered as a public dashboard with a world map, a country report and a ranked priority list.")]

# ---- 1 introduction
S += [P("1. The real-world problem", H1),
      P("Vaccines are among the most cost-effective health tools, but only when children actually receive every dose. DTP3 (the third dose of the "
        "diphtheria-tetanus-pertussis vaccine) is the standard yardstick for how well a country's routine service works, because it needs a child to "
        "be reached three times. The Immunisation Agenda 2030 sets a target of 90% coverage."),
      P("The COVID-19 pandemic disrupted clinics, supply chains and families' ability to travel. The decision problem that followed is: "
        "<b>with limited money and staff, which countries should be helped first, and with what kind of programme?</b> A catch-up campaign for children "
        "who missed their doses is the right answer for a country that was doing well and suddenly collapsed, but it is not the right answer for a "
        "country that never reached many children in the first place."),
      P("The task is unsupervised because no one has labelled countries as 'backslider' or 'recovering'. We let the data reveal natural groups of "
        "countries with similar recovery behaviour, and then check whether the groups make sense and are useful for planning."),
      P("Objectives", H2)] + B([
          "Group countries by <i>how their coverage behaved</i> before, during and after the disruption.",
          "Describe each group using health-system and socio-economic context.",
          "Turn the groups into practical outputs: a priority list, a suggested focus per group, and look-alike countries to learn from.",
          "Be clear about what the method can and cannot say."])

# ---- 2 data
S += [P("2. Data", H1),
      P("All data is real and public. It is downloaded by one script (<font face='Courier'>src/fetch_data.py</font>) so the work can be repeated exactly."),
      table([["Series", "Years", "Original source"],
             ["DTP3 coverage (%)", "1980-2025", "WHO/UNICEF Estimates of National Immunization Coverage (WUENIC)"],
             ["Measles first-dose coverage, MCV1 (%)", "1980-2025", "WHO/UNICEF WUENIC"],
             ["Under-5 mortality risk", "to 2019", "UN Inter-agency Group for Child Mortality Estimation"],
             ["GDP per person (PPP)", "1990-2025", "World Bank"],
             ["Doctors per 1,000 people", "to 2023", "World Bank / WHO"],
             ["Births attended by skilled staff (%)", "to 2022", "WHO / UNICEF"],
             ["Children per woman; urban and rural population", "to 2023-25", "UN"]], [6.2, 2.4, 8.4]),
      Spacer(1, 6),
      P("The files come through the Our World in Data CSV service, which republishes the official series.", CAP),
      Spacer(1, 4), P("Preparation steps", H2)] + B([
          "<b>Real countries only.</b> Regional aggregates such as 'World' or 'Africa' are removed. 201 countries have DTP3 data.",
          "<b>Complete trajectories.</b> A country must have every value needed for the six features. This leaves 200 countries.",
          f"<b>Micro-states removed.</b> Countries with under 100,000 people (for example Nauru and the Cook Islands) are excluded. Their percentages depend on a handful of children and swing wildly from year to year. {info['countries']} countries remain.",
          "<b>Context values</b> use the latest value available in a recent window (for example doctors per 1,000 people since 2005). A few countries have gaps, which are left blank rather than invented."])

# ---- 3 method
S += [P("3. Methodology", H1), img("fig_pipeline.png", 16.5), P("Figure 1. The pipeline from raw data to dashboard.", CAP),
      P("3.1 Features: what happened", H2),
      P("Clustering uses only the six trajectory features. Region, income and health-system data are kept out on purpose, so the groups reflect "
        "behaviour and are not just a restatement of how rich a country is."),
      table([["Feature", "Meaning"],
             ["dtp3_2019, mcv1_2019", "Coverage in the last normal year"],
             ["dtp3_drop", "Worst DTP3 value in 2020-22 minus the 2019 value (how hard the shock hit)"],
             ["dtp3_net, mcv1_net", "Coverage in 2024 minus 2019 (still lost, or regained)"],
             ["trend_pre", "Slope of DTP3 over 2010-19 (was the country already improving or sliding?)"]], [4.6, 12.4]),
      Spacer(1, 6), P("All six are standardised (z-score) so that no feature dominates because of its units."),
      P("3.2 Clustering", H2),
      P("<b>K-Means</b> starts with K centres (chosen by k-means++ so they are well spread), assigns each country to its nearest centre, moves each "
        "centre to the average of its group, and repeats until nothing changes. We run it 30 times and keep the tightest result. "
        "Euclidean distance on standardised data is the natural choice here because all features are smooth numeric quantities."),
      P("<b>Choosing K.</b> We compare K = 2 to 8 with four checks: WCSS (the elbow), the silhouette score (how well each country fits its own group "
        "versus the next nearest), the Davies-Bouldin index (how much groups overlap; lower is better) and seed stability (the adjusted Rand index "
        "between 15 runs from different random starts; 1 means identical groups)."),
      P("<b>Cross-check with other methods.</b> The same data is clustered with Ward hierarchical clustering and a Gaussian mixture model. "
        "This shows whether the structure belongs to the data or is just an effect of K-Means."),
      P("3.3 From groups to decisions", H2)] + B([
          "<b>Group names are generated from the data.</b> The group with the largest net loss is called 'COVID backsliders', the one with the highest coverage now 'Stable high performers', "
          "the one with the lowest 2019 coverage 'Low but improving', and the rest 'Mid-level, slow recovery'. Names never depend on the arbitrary cluster number.",
          "<b>Context profile.</b> For each group we report median child mortality, income, doctors, skilled birth attendance, fertility and rural share.",
          "<b>Priority score</b> = points below the 90% target in 2024 plus points still lost since 2019. It highlights countries that are both low and slipping.",
          "<b>Look-alike peers.</b> For each country we find the nearest countries in the standardised feature space that regained at least 3 more points. These are practical countries to learn from.",
          "<b>PCA</b> is used only to draw the groups on a flat picture. The clusters themselves are found in all six dimensions."])

# ---- 4 results
S += [PageBreak(), P("4. Results", H1), P("4.1 Choosing K and checking the method", H2),
      img("fig_validation.png", 15.5), P("Figure 2. Elbow, silhouette and seed stability for K = 2 to 8. The red line marks K = 4.", CAP),
      table([["K", "WCSS", "Silhouette", "Davies-Bouldin", "Seed stability (ARI)"]] +
            [[int(r.K), r.WCSS, r.Silhouette, r.Davies_Bouldin, r.Seed_Stability_ARI] for r in kval.itertuples()], [2, 3.2, 3.2, 3.6, 4.4]),
      Spacer(1, 6),
      P(f"K = 3 has the best silhouette ({kv(3, 'Silhouette')}), and K = 4 is lower ({kv(4, 'Silhouette')}) but still reasonable, "
        f"with a stability of {kv(4, 'Seed_Stability_ARI')}. We choose <b>K = 4</b> because it splits one large middle group into two that need different help: "
        "severe backsliders (needing urgent catch-up) and mid-level countries (needing steady recovery work). This is a judgement based on usefulness, not just on the highest score, and we say so openly."),
      table([["Method (K = 4)", "Silhouette", "Davies-Bouldin", "Agreement with K-Means (ARI)"]] +
            [[r.Method, r.Silhouette, r.Davies_Bouldin, r.ARI_vs_KMeans] for r in meth.itertuples()], [5.2, 3.2, 3.6, 5]),
      Spacer(1, 6),
      P("K-Means gives the cleanest groups. Ward hierarchical clustering agrees only partly (ARI 0.48), which tells us that the boundaries between "
        "groups are soft, since countries change gradually from strong to weak. The Gaussian mixture fits poorly with such small groups. "
        "This is why the groups should be read as a practical grouping and not as exact categories."),
      P("4.2 The four groups", H2),
      table([["Group", "Countries", "DTP3 2019", "DTP3 2024", "Change", "Measles 2024"]] +
            [[a, int(g(a, "countries")), f"{g(a, 'dtp3_2019'):.0f}%", f"{g(a, 'dtp3_2024'):.0f}%", f"{g(a, 'dtp3_net'):+.0f}", f"{g(a, 'mcv1_2024'):.0f}%"] for a in order],
            [5.4, 2.2, 2.4, 2.4, 2, 2.6]),
      Spacer(1, 8), img("fig_trajectories.png", 15.5), P("Figure 3. Average DTP3 coverage of each group, 2010-2025.", CAP),
      P("What the picture shows", H2)] + B([
          "<b>Stable high performers</b> stayed near 93% throughout. COVID barely moved them.",
          "<b>COVID backsliders</b> were high (88%) and then fell sharply to 61% in 2021. They are the clearest case for emergency catch-up. "
          "Their average rebounded to 68% in 2025, but remains about 20 points below 2019. The 2025 figure is the newest and may still be revised.",
          "<b>Mid-level countries were already sliding before COVID</b> (about 84% in 2010 to 79% in 2019) and then dropped again. This is a longer problem than the pandemic.",
          "<b>Low but improving</b> countries have steadily gained since 2021 and by 2024 are above the mid-level group. These gains are fragile and worth protecting."])

S += [P("4.3 Who they are: context of each group", H2), img("fig_context.png", 16.5),
      P("Figure 4. Median context indicators of each group.", CAP),
      P("Stable high performers have a median of 2.4 doctors per 1,000 people and 99% of births attended by skilled staff. Low but improving countries have about 0.2 doctors per 1,000 "
        "and 68% skilled birth attendance, so they are succeeding with very thin health systems. The severe backsliders also have few doctors (0.2 per 1,000) "
        "and a 65% rural population, but had high pre-COVID coverage, which suggests their gains were fragile and exposed to shocks. "
        "With only five countries these medians are indicative, not conclusive."),
      table([["Group", "Under-5 death risk (%)", "Doctors / 1,000", "Skilled births (%)", "GDP per person ($)", "Rural pop. (%)"]] +
            [[a, f"{g(a, 'child_mortality'):.1f}", f"{g(a, 'physicians'):.1f}", f"{g(a, 'skilled_birth'):.0f}", f"{g(a, 'gdp_pc'):,.0f}", f"{g(a, 'rural_share'):.0f}"] for a in order],
            [4.8, 2.9, 2.4, 2.4, 2.6, 2.1]),
      Spacer(1, 6), P("4.4 The priority list", H2), img("fig_priority.png", 12.5),
      P("Figure 5. The twelve highest-priority countries: DTP3 in 2019 (grey) and in 2024 (coloured by group).", CAP)]

top = df.sort_values("priority_score", ascending=False).head(8)
S += [table([["Country", "Group", "DTP3 2019", "DTP3 2024", "Priority score"]] +
            [[r.country, r.archetype, f"{r.dtp3_2019:.0f}%", f"{r.dtp3_2024:.0f}%", f"{r.priority_score:.0f}"] for r in top.itertuples()],
            [3.6, 5.4, 2.6, 2.6, 2.8]),
      Spacer(1, 6), img("fig_pca.png", 11.5),
      P("Figure 6. PCA view of the six features (67% of the variation in two dimensions). Groups overlap at the edges because the change is gradual.", CAP)]

# ---- 5 use
S += [P("5. How this is used in the real world", H1),
      P("The output is designed for a person who must decide where to send limited support. The dashboard answers three practical questions."),
      P("<b>1. Where do we look first?</b> The world map and the ranked priority list show which countries are both below the 90% target and still below their 2019 level. "
        "The list can be filtered by region or group and downloaded as a CSV file for a planning meeting."),
      P("<b>2. What kind of help fits?</b> Each group carries a suggested focus:"),
      table([["Group", "Suggested focus"],
             ["COVID backsliders", "Urgent catch-up: re-vaccinate the cohorts missed in 2020-22 and restore routine services."],
             ["Mid-level, slow recovery", "Targeted recovery: defaulter tracking, reminders and outreach so children finish started schedules."],
             ["Low but improving", "Protect the gains: fund routine delivery and outreach to children who have never been reached."],
             ["Stable high performers", "Maintain the programme; look for weak districts hidden inside the national average."]], [4.6, 12.4]),
      Spacer(1, 6),
      P("<b>3. Who can we learn from?</b> The country report page lists look-alike countries that regained more coverage. Planners can ask what those countries did differently, "
        "which is cheaper than designing a programme from scratch."),
      P("Worked examples", H2)] + B([
          "<b>Sudan</b> fell from 93% to 39% (-54 points), the largest loss in the data. It tops the priority list and sits in the backslider group.",
          "<b>Lebanon</b> fell from 83% to 49% (-34 points). Its pattern resembles Sudan's, even though the countries differ greatly. The grouping is about behaviour, not geography.",
          "<b>Nigeria</b> (66% to 63%) is in the mid-level group: coverage was already low before COVID and has barely recovered, so a long-term recovery plan fits better than an emergency campaign.",
          "<b>Central African Republic</b> and <b>Papua New Guinea</b> are 'low but improving' yet still reach only 42% of children. They rank high on the priority list despite improving."]) + [
      P("Who could use it", H2)] + B([
          "Immunisation programme managers at ministries of health, to benchmark their country against look-alikes.",
          "Funders such as Gavi, WHO regional offices, UNICEF and foundations, to match the type of support to the type of problem.",
          "Researchers, to select countries for deeper study, for example district-level work."]) + [
      P("Why clustering is the right tool", H2),
      P("A simple league table of coverage would put Sudan and Papua New Guinea side by side, although one has lost half its coverage and the other has been gaining. "
        "Clustering on the <i>shape</i> of the trajectory separates these cases, which a single number cannot.")]

# ---- 6 limits
S += [P("6. Limitations and responsible use", H1)] + B([
    "<b>National averages hide local gaps.</b> A country in the 'stable' group can still have districts with many unvaccinated children. This tool is a first filter, not a district plan.",
    "<b>The inputs are estimates.</b> WUENIC values are modelled and can be revised, especially for the most recent years. Using 2025 instead of 2024 changes the backsliders' average from 60% to 68%.",
    "<b>Groups describe what happened, not why.</b> Conflict, economic crisis, funding cuts or data problems may explain a collapse, but none of them is in the data, and this project does not test causes.",
    "<b>One group is very small.</b> With five countries, its averages depend on each member. Treat it as a short list of emergency cases.",
    "<b>The boundaries are soft.</b> The hierarchical method agrees only partly with K-Means (ARI 0.48), and K = 3 has a slightly higher silhouette. The choice of K = 4 is explained, but it is a judgement.",
    "<b>Micro-states are excluded,</b> so very small countries are not covered.",
    "<b>Only two vaccines.</b> DTP1, pneumococcal and rotavirus series were not available from our source, so 'zero-dose' children cannot be counted directly.",
    "<b>Labels can harm.</b> Calling a country a 'backslider' is meant to direct support, not to rank or blame countries. Decisions should combine these groups with local knowledge."])

# ---- 7 conclusion
S += [P("7. Conclusion and future work", H1),
      P(f"Countries did not lose and regain vaccination coverage in the same way. Clustering their trajectories reveals four distinct groups, from {int(g(order[0], 'countries'))} stable high performers to a small set of "
        "severe backsliders that lost about 28 points on average. Each group suggests a different kind of response, and the dashboard turns the result into a map, a ranked list and look-alike countries to learn from."),
      P("Future work", H2)] + B([
          "Use district-level or survey data to find the weak areas inside each country.",
          "Add DTP1 to measure zero-dose children directly, and newer vaccines such as pneumococcal and rotavirus.",
          "Cluster the whole 2000-2025 time series (for example with dynamic time warping) instead of six summary features.",
          "Add soft assignments, so that countries on the border between two groups are marked as such.",
          "Refresh the analysis each year when WUENIC publishes new estimates."])

S += [P("References and data sources", H1)] + B([
    "WHO/UNICEF Estimates of National Immunization Coverage (WUENIC): immunizationdata.who.int",
    "Our World in Data, immunisation and health indicator series: ourworldindata.org",
    "World Bank, World Development Indicators: data.worldbank.org",
    "Immunization Agenda 2030, a global strategy to leave no one behind: who.int/teams/immunization-vaccines-and-biologicals/strategies/ia2030",
    "Pedregosa et al. (2011). Scikit-learn: machine learning in Python. Journal of Machine Learning Research 12.",
    "Rousseeuw (1987), silhouettes; Davies and Bouldin (1979), a cluster separation measure; Hubert and Arabie (1985), comparing partitions (adjusted Rand index)."]) + [
    P("Reproducing the work", H2),
    P("<font face='Courier'>cd codebase; pip install -r requirements.txt; python src/pipeline.py; python -m pytest tests -q; streamlit run app.py</font>")]

SimpleDocTemplate(PDF, pagesize=A4, leftMargin=2 * cm, rightMargin=2 * cm, topMargin=2 * cm, bottomMargin=2 * cm,
                  title="Post-COVID immunisation recovery: clustering countries by trajectory").build(
    S, onFirstPage=lambda c, d: None, onLaterPages=footer)
print("wrote", PDF)
