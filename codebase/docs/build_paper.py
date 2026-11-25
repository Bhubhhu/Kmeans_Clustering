"""Builds the IEEE-style two-column paper PDF from the real outputs.
Run from codebase/ after docs/paper_experiments.py and docs/paper_figures.py:  python docs/build_paper.py
"""
import io
import os
import re

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
matplotlib.rcParams["mathtext.fontset"] = "stix"
from PIL import Image as PILImage
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (CondPageBreak, BaseDocTemplate, Frame, FrameBreak, Image, KeepTogether, PageTemplate, Paragraph,
                                Spacer, Table, TableStyle)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT, PAP = os.path.join(ROOT, "outputs"), os.path.join(ROOT, "outputs", "paper")
PDF = os.path.join(os.path.dirname(ROOT), "Project_Report_IEEE_Format.pdf")

for n, f in [("TNR", "times.ttf"), ("TNR-B", "timesbd.ttf"), ("TNR-I", "timesi.ttf"), ("TNR-BI", "timesbi.ttf")]:
    pdfmetrics.registerFont(TTFont(n, os.path.join(r"C:\Windows\Fonts", f)))
pdfmetrics.registerFontFamily("TNR", normal="TNR", bold="TNR-B", italic="TNR-I", boldItalic="TNR-BI")

# ------------------------------------------------------------------ data
df = pd.read_csv(os.path.join(OUT, "country_archetypes.csv"))
summ = pd.read_csv(os.path.join(OUT, "archetype_summary.csv")).set_index("archetype")
ev = pd.read_csv(os.path.join(PAP, "model_evaluation.csv"))
sizes = pd.read_csv(os.path.join(PAP, "partition_sizes.csv"))
mem = pd.read_csv(os.path.join(PAP, "membership_top12.csv"))
bands = pd.read_csv(os.path.join(PAP, "bands.csv"), index_col=0)
ts = pd.read_csv(os.path.join(OUT, "timeseries.csv")).merge(df[["code", "archetype"]], on="code")
ym = ts.groupby(["archetype", "year"])["dtp3"].mean().unstack()
S, M, L, B = "Stable high performers", "Mid-level, slow recovery", "Low but improving", "COVID backsliders"
n = {a: int(summ.loc[a, "countries"]) for a in (S, M, L, B)}
d19 = {a: summ.loc[a, "dtp3_2019"] for a in (S, M, L, B)}
d24 = {a: summ.loc[a, "dtp3_2024"] for a in (S, M, L, B)}
N = len(df)
below_prev, below_tgt = int((df["dtp3_net"] < 0).sum()), int((df["dtp3_2024"] < 90).sum())
e = lambda m, k: ev[(ev.Model == m) & (ev.K == k)].iloc[0]
A4, C3, A3 = e("A", 4), e("C", 3), e("A", 3)
miss = df[["gdp_pc", "skilled_birth"]].isna().sum()

# ------------------------------------------------------------------ styles
BODY = ParagraphStyle("body", fontName="TNR", fontSize=10, leading=11.6, alignment=TA_JUSTIFY, firstLineIndent=11, spaceAfter=2.5)
BODY0 = ParagraphStyle("body0", parent=BODY, firstLineIndent=0)
ABS = ParagraphStyle("abs", fontName="TNR-B", fontSize=9, leading=10.6, alignment=TA_JUSTIFY, spaceAfter=4)
H1 = ParagraphStyle("h1", fontName="TNR", fontSize=9.5, leading=11, alignment=TA_CENTER, spaceBefore=9, spaceAfter=4)
H2 = ParagraphStyle("h2", fontName="TNR-I", fontSize=10, leading=11.5, alignment=TA_LEFT, spaceBefore=5, spaceAfter=2)
CAP = ParagraphStyle("cap", fontName="TNR", fontSize=8, leading=9.4, alignment=TA_JUSTIFY, spaceBefore=2, spaceAfter=6)
TCAP = ParagraphStyle("tcap", fontName="TNR", fontSize=8, leading=9.4, alignment=TA_CENTER, spaceAfter=3, keepWithNext=1)
CELL = ParagraphStyle("cell", fontName="TNR", fontSize=7.2, leading=8.4, alignment=TA_LEFT)
CELLC = ParagraphStyle("cellc", parent=CELL, alignment=TA_CENTER)
ITEM = ParagraphStyle("item", parent=BODY, firstLineIndent=0, leftIndent=11, spaceAfter=2.5)
REF = ParagraphStyle("ref", fontName="TNR", fontSize=7.8, leading=8.9, alignment=TA_JUSTIFY, leftIndent=19, firstLineIndent=-19, spaceAfter=1.5)
TITLE = ParagraphStyle("title", fontName="TNR", fontSize=23, leading=26, alignment=TA_CENTER, spaceAfter=10)
AU = ParagraphStyle("au", fontName="TNR", fontSize=9.5, leading=11.4, alignment=TA_CENTER)

# ------------------------------------------------------------------ references (all 2022 or later, checked against Crossref)
REFS = {
    "shet": "A. Shet <i>et al.</i>, “Impact of the SARS-CoV-2 pandemic on routine immunisation services: Evidence of disruption and recovery from 170 countries and territories,” <i>Lancet Glob. Health</i>, vol. 10, no. 2, pp. e186–e194, Feb. 2022, doi: 10.1016/S2214-109X(21)00512-X.",
    "kang": "G. Kang, “The SARS-CoV2 pandemic and routine immunisation,” <i>Lancet Glob. Health</i>, vol. 10, no. 2, pp. e155–e156, Feb. 2022, doi: 10.1016/S2214-109X(21)00543-X.",
    "evans22": "B. Evans and T. Jombart, “Worldwide routine immunisation coverage regressed during the first year of the COVID-19 pandemic,” <i>Vaccine</i>, vol. 40, no. 26, pp. 3531–3535, Jun. 2022, doi: 10.1016/j.vaccine.2022.01.044.",
    "evans23": "B. Evans, O. Keiser, L. Kaiser, and T. Jombart, “Analysis of global routine immunisation coverage shows disruption and stagnation during the first two-years of the COVID-19 pandemic with tentative recovery in 2022,” <i>Vaccine: X</i>, vol. 15, Art. no. 100383, Dec. 2023, doi: 10.1016/j.jvacx.2023.100383.",
    "ghaznavi": "C. Ghaznavi <i>et al.</i>, “Estimating global changes in routine childhood vaccination coverage during the COVID-19 pandemic, 2020–2021,” <i>Vaccine</i>, vol. 41, no. 28, pp. 4151–4157, Jun. 2023, doi: 10.1016/j.vaccine.2023.05.034.",
    "rachlin": "A. Rachlin, M. C. Danovaro-Holliday, P. Murphy, S. V. Sodha, and A. S. Wallace, “Routine vaccination coverage—Worldwide, 2021,” <i>MMWR Morb. Mortal. Wkly. Rep.</i>, vol. 71, no. 44, pp. 1396–1400, Nov. 2022, doi: 10.15585/mmwr.mm7144a2.",
    "kaur": "G. Kaur <i>et al.</i>, “Routine vaccination coverage—Worldwide, 2022,” <i>MMWR Morb. Mortal. Wkly. Rep.</i>, vol. 72, no. 43, pp. 1155–1161, Oct. 2023, doi: 10.15585/mmwr.mm7243a1.",
    "lal": "A. Lal, C. Lim, G. Almeida, and J. Fitzgerald, “Minimizing COVID-19 disruption: Ensuring the supply of essential health products for health emergencies and routine health services,” <i>Lancet Reg. Health Am.</i>, vol. 6, Art. no. 100129, Feb. 2022, doi: 10.1016/j.lana.2021.100129.",
    "martins": "J. P. Martins, G. A. Alatzatianos, T. M. Camargo, and F. A. L. Marson, “Overview of childhood vaccination coverage in Brazil and the impact of the COVID-19 pandemic: Is our children’s health at risk? A review of pre-COVID-19 periods and during the COVID-19 pandemic,” <i>Vaccine: X</i>, vol. 17, Art. no. 100430, Mar. 2024, doi: 10.1016/j.jvacx.2024.100430.",
    "engelbert": "M. Engelbert, M. Jain, A. Bagai, and S. S. Parsekar, “Improving routine childhood immunisation outcomes in low-income and middle-income countries: An evidence gap map,” <i>BMJ Open</i>, vol. 12, no. 11, Art. no. e058258, Nov. 2022, doi: 10.1136/bmjopen-2021-058258.",
    "wonodi": "C. Wonodi and B. A. Farrenkopf, “Defining the zero dose child: A comparative analysis of two approaches and their impact on assessing the zero dose burden and vulnerability profiles across 82 low- and middle-income countries,” <i>Vaccines</i>, vol. 11, no. 10, p. 1543, Sep. 2023, doi: 10.3390/vaccines11101543.",
    "dimitrova": "A. Dimitrova, G. Carrasco-Escobar, R. Richardson, and T. Benmarhnia, “Essential childhood immunization in 43 low- and middle-income countries: Analysis of spatial trends and socioeconomic inequalities in vaccine coverage,” <i>PLOS Med.</i>, vol. 20, no. 1, Art. no. e1004166, Jan. 2023, doi: 10.1371/journal.pmed.1004166.",
    "saikia": "N. Saikia, K. Kumar, J. K. Bora, S. Mondal, S. Phad, and S. Agarwal, “What determines the district-level disparities in immunization coverage in India: Findings from five rounds of the National Family Health Survey,” <i>Vaccines</i>, vol. 11, no. 4, p. 851, Apr. 2023, doi: 10.3390/vaccines11040851.",
    "fahmy": "K. Fahmy, Q. Hasan, M. Sharifuzzaman, and Y. Hutin, “Analyzing subnational immunization coverage to catch up and reach the unreached in seven high-priority countries in the Eastern Mediterranean Region, 2019–2021,” <i>Vaccines</i>, vol. 12, no. 3, p. 285, Mar. 2024, doi: 10.3390/vaccines12030285.",
    "gohari": "K. Gohari, A. Kazemnejad, A. Sheidaei, and S. Hajari, “Clustering of countries according to the COVID-19 incidence and mortality rates,” <i>BMC Public Health</i>, vol. 22, Art. no. 632, Apr. 2022, doi: 10.1186/s12889-022-13086-z.",
    "ikotun": "A. M. Ikotun, A. E. Ezugwu, L. Abualigah, B. Abuhaija, and J. Heming, “K-means clustering algorithms: A comprehensive review, variants analysis, and advances in the era of big data,” <i>Inf. Sci.</i>, vol. 622, pp. 178–210, Apr. 2023, doi: 10.1016/j.ins.2022.11.139.",
    "ezugwu": "A. E. Ezugwu <i>et al.</i>, “A comprehensive survey of clustering algorithms: State-of-the-art machine learning applications, taxonomy, challenges, and future research prospects,” <i>Eng. Appl. Artif. Intell.</i>, vol. 110, Art. no. 104743, Apr. 2022, doi: 10.1016/j.engappai.2022.104743.",
    "greenacre": "M. Greenacre, P. J. F. Groenen, T. Hastie, A. Iodice D’Enza, A. Markos, and E. Tuzhilina, “Principal component analysis,” <i>Nat. Rev. Methods Primers</i>, vol. 2, Art. no. 100, Dec. 2022, doi: 10.1038/s43586-022-00184-w.",
    "warrens": "M. J. Warrens and H. van der Hoef, “Understanding the adjusted Rand index and other partition comparison indices based on counting object pairs,” <i>J. Classif.</i>, vol. 39, no. 3, pp. 487–509, Jul. 2022, doi: 10.1007/s00357-022-09413-z.",
    "ros": "F. Ros, R. Riad, and S. Guillaume, “PDBI: A partitioning Davies-Bouldin index for clustering evaluation,” <i>Neurocomputing</i>, vol. 528, pp. 178–199, Apr. 2023, doi: 10.1016/j.neucom.2023.01.043.",
    "chicco": "D. Chicco, A. Campagner, A. Spagnolo, D. Ciucci, and G. Jurman, “The Silhouette coefficient and the Davies-Bouldin index are more informative than Dunn index, Calinski-Harabasz index, Shannon entropy, and Gap statistic for unsupervised clustering internal evaluation of two convex clusters,” <i>PeerJ Comput. Sci.</i>, vol. 11, Art. no. e3309, Nov. 2025, doi: 10.7717/peerj-cs.3309.",
    "wuenic": "WHO and UNICEF, “WHO/UNICEF estimates of national immunization coverage (WUENIC),” WHO Immunization Data portal. Accessed: Nov. 18, 2026. [Online]. Available: https://immunizationdata.who.int",
    "owid": "Our World in Data, “Immunization, child mortality, income, health workforce, fertility and population series (grapher CSV downloads),” Accessed: Nov. 18, 2026. [Online]. Available: https://ourworldindata.org",
    "sklearn": "scikit-learn developers, “scikit-learn 1.6.1: Machine learning in Python—User guide and API reference,” 2025. [Online]. Available: https://scikit-learn.org/1.6/",
}
order = []


def R(text):
    """Replace {key,key2} markers with IEEE numbers assigned in order of first citation."""
    def sub(m):
        nums = []
        for k in m.group(1).split(","):
            if k not in order:
                order.append(k)
            nums.append(order.index(k) + 1)
        return ", ".join(f"[{x}]" for x in nums)
    return re.sub(r"\{([a-z0-9_,]+)\}", sub, text)


def P(t, st=BODY):
    return Paragraph(R(t), st)


def eqimg(tex, name):
    fig = plt.figure(figsize=(4, 0.6))
    fig.text(0.0, 0.5, f"${tex}$", fontsize=11, va="center", ha="left")
    buf = io.BytesIO()
    fig.savefig(buf, dpi=300, format="png", bbox_inches="tight", pad_inches=0.02, transparent=True)
    plt.close(fig)
    buf.seek(0)
    w, h = PILImage.open(buf).size
    buf.seek(0)
    k = min(1.0, 205 / (w / 300 * 72))
    return Image(buf, width=w / 300 * 72 * k, height=h / 300 * 72 * k)


eq_no = [0]


def EQ(tex):
    eq_no[0] += 1
    t = Table([[eqimg(tex, f"e{eq_no[0]}"), Paragraph(f"({eq_no[0]})", ParagraphStyle("en", fontName="TNR", fontSize=10, alignment=2))]],
              colWidths=[212, 40])
    t.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("TOPPADDING", (0, 0), (-1, -1), 1), ("BOTTOMPADDING", (0, 0), (-1, -1), 3)]))
    return t


def FIG(file, caption, h=None):
    path = os.path.join(PAP, file)
    w, hh = PILImage.open(path).size
    width = 245
    return KeepTogether([Image(path, width=width, height=width * hh / w), Paragraph(R(caption), CAP)])


tab_no = [0]
ROMAN = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII"]


def TABLE(title, rows, widths, align=None, bold_rows=()):
    tab_no[0] += 1
    cap = [Paragraph(f"TABLE {ROMAN[tab_no[0] - 1]}", ParagraphStyle("tc", parent=TCAP, spaceAfter=0)), Paragraph(title.upper(), TCAP)]
    body = []
    for i, r in enumerate(rows):
        row = []
        for j, c in enumerate(r):
            st = CELLC if (align and align[j] == "c") or (i == 0) else CELL
            txt = R(str(c))
            if i == 0 or i in bold_rows:
                txt = f"<b>{txt}</b>"
            row.append(Paragraph(txt, st))
        body.append(row)
    t = Table(body, colWidths=widths, repeatRows=1)
    t.setStyle(TableStyle([("LINEABOVE", (0, 0), (-1, 0), 0.8, colors.black), ("LINEBELOW", (0, 0), (-1, 0), 0.5, colors.black),
                           ("LINEBELOW", (0, -1), (-1, -1), 0.8, colors.black), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                           ("TOPPADDING", (0, 0), (-1, -1), 1.6), ("BOTTOMPADDING", (0, 0), (-1, -1), 1.6),
                           ("LEFTPADDING", (0, 0), (-1, -1), 2.5), ("RIGHTPADDING", (0, 0), (-1, -1), 2.5)]))
    return KeepTogether(cap + [t, Spacer(1, 7)])


def sec(t):
    return Paragraph(t.upper(), H1)


def sub(t):
    return Paragraph(t, H2)


def item(label, text):
    return Paragraph(R(f"{label} {text}"), ITEM)


# ------------------------------------------------------------------ content
story = []
story.append(Paragraph("Post-COVID Childhood Immunisation Recovery Assessment Using Unsupervised Machine Learning: A K-Means Clustering Comparative Analysis of "
                       f"{N} Countries", TITLE))
au = lambda name, em: Paragraph(f"<font size=11>{name}</font><br/>Department of Computer Science &amp; Engineering<br/>Lovely Professional University<br/>Phagwara, Punjab, India<br/>{em}", AU)
t = Table([[au("Shubhudeep Singh", "shubhdeep119@gmail.com"), au("Hitesh Kumar", "hitesh@gmail.com")]], colWidths=[261, 261])
t.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP")]))
story += [t, FrameBreak()]

abstract = (
    "<i>Abstract—</i>Routine childhood immunisation was disrupted worldwide during the COVID-19 pandemic, yet countries differed sharply in how much coverage they lost "
    "and how much they have regained. Comparing such heterogeneous trajectories with league tables hides the difference between a country that collapsed and a country that "
    "has always been low. This paper presents an empirical, unsupervised machine learning framework that groups "
    f"{N} countries by the shape of their recovery. Using WHO/UNICEF estimates of DTP3 and measles (MCV1) coverage, we construct six trajectory features describing coverage "
    "before (2019), during (2020–2022) and after (to 2024) the disruption, and benchmark partitional K-Means configurations "
    "(K = 2, 3, 4, 5, 6) across three feature-space formulations: Model A (6 features), Model B (5 correlation-pruned features) and Model C (5 features without the noisiest trend feature). "
    "Validation via Within-Cluster Sum of Squares (WCSS), Silhouette Analysis, Davies-Bouldin Index (DBI) and 20-seed pairwise Adjusted Rand Index (ARI) shows that Model C with K = 3 is the statistically tightest "
    f"solution (Silhouette = {C3.Silhouette:.4f}, DBI = {C3.DBI:.4f}, mean ARI = {C3.Mean_ARI:.4f}), but it merges five severe backsliders with 17 mid-level countries. "
    f"Model A with K = 4 (Silhouette = {A4.Silhouette:.4f}, DBI = {A4.DBI:.4f}) is therefore adopted as the operational baseline. It separates "
    f"{n[S]} stable high performers (mean DTP3 {d19[S]:.0f}% to {d24[S]:.0f}%), {n[M]} mid-level countries with slow recovery ({d19[M]:.0f}% to {d24[M]:.0f}%), "
    f"{n[L]} low but improving countries ({d19[L]:.0f}% to {d24[L]:.0f}%) and {n[B]} severe backsliders ({d19[B]:.0f}% to {d24[B]:.0f}%: Sudan, Lebanon, Myanmar, Mozambique and Vanuatu). "
    f"{below_prev} of {N} countries remain below their 2019 DTP3 level and {below_tgt} are below the 90% benchmark. The study provides an objective, reproducible basis for matching the "
    "type of immunisation support to the type of recovery problem, without arbitrary indicator weights or causal claims.")
story.append(Paragraph(R(abstract), ABS))
story.append(Paragraph("<i>Index Terms—</i>Childhood Immunisation, COVID-19 Recovery, K-Means Clustering, Unsupervised Machine Learning, Cluster Validation, Public Health Analytics.", ABS))

# I
story += [sec("I. Introduction"), sub("A. Background and Institutional Context"),
    P("Routine childhood immunisation is among the most cost-effective public health interventions. The third dose of the diphtheria-tetanus-pertussis vaccine (DTP3) is the standard indicator "
      "of whether a national programme can reach the same child repeatedly during infancy, and the first dose of measles-containing vaccine (MCV1) provides a second, independent contact point. "
      "WHO and UNICEF jointly publish annual national coverage estimates (WUENIC) that reconcile administrative reports, surveys and expert review {wuenic}. "
      "The COVID-19 pandemic strained clinics, supply chains, health workers and household mobility, and global analyses documented widespread disruption of routine services and an uneven, "
      "incomplete recovery {shet,evans22,evans23,ghaznavi}. Annual worldwide reviews continue to track the aftermath {rachlin,kaur}."),
    P("Countries entered the pandemic with different coverage levels and different health-system capacity, so the same shock produced different trajectories. "
      "Some held their coverage, some regained it, some were already declining before 2020, and a few lost a large share that they have not yet recovered. "
      "Unsupervised learning, and in particular partitional K-Means clustering {ikotun}, offers a way to uncover these latent recovery types without prescribing normative scores."),
    sub("B. Problem Statement and Research Gap"),
    P("National averages and league tables compress these differences. A ranking of 2024 coverage places Sudan, whose DTP3 coverage fell from 93% to 39%, "
      "beside Papua New Guinea, whose coverage rose from 35% to 42%, although the two countries need very different support. "
      "Funders and ministries must decide which countries to help first and which programme to fund, and the evidence base on possible interventions is broad {engelbert}. "
      "Existing global analyses mostly estimate how much coverage was lost {ghaznavi} or study inequality inside selected countries {dimitrova,saikia,fahmy}. "
      "Cluster analysis has been applied to countries for other health outcomes, such as COVID-19 incidence and mortality {gohari}, but to our knowledge it has not been used to "
      "group countries by post-pandemic immunisation trajectories while also reporting validation, stability and a policy reading of the groups."),
    P("A further difficulty is methodological. Composite scores need arbitrary weights, and a single high-dimensional ranking cannot show that a country is low because it never improved, "
      "or because it collapsed. There is a need for a data-driven segmentation that is objective, reproducible, and honest about its uncertainty."),
    sub("C. Research Objectives and Key Contributions"),
    P("To address this gap, the paper makes four contributions:", BODY),
    item("1)", "<i>Trajectory-Based Multi-Model Formulation:</i> We construct six features describing the level, shock, net change and pre-pandemic trend of DTP3 and MCV1 coverage, and "
               "evaluate three feature-space formulations (Models A, B and C)."),
    item("2)", "<i>Rigorous Cluster Validation:</i> We evaluate K = 2 to 6 with WCSS, silhouette, DBI and 20-seed pairwise ARI {ezugwu,warrens,ros,chicco}."),
    item("3)", f"<i>Empirical Divergence and Gap Analysis:</i> We identify four recovery groups, including a group of {n[B]} severe backsliders that coarser partitions hide."),
    item("4)", "<i>Decision Support:</i> We convert the groups into fixed descriptive bands, a transparent priority score, look-alike peer countries and a public dashboard."),
    sub("D. Paper Organization"),
    P("Section II reviews related work. Section III describes the data. Section IV presents the methodology and validation metrics. Section V reports the experimental design, "
      "Section VI the empirical results, and Section VII discusses policy implications. Sections VIII and IX give the limitations and conclusion.")]

# II
story += [sec("II. Related Work"), sub("A. Pandemic Disruption and Recovery of Routine Immunisation"),
    P("Shet <i>et al.</i> assembled evidence of disruption and recovery from 170 countries and territories {shet}, and an accompanying commentary discussed the pandemic's consequences for routine immunisation {kang}. "
      "Evans and Jombart reported that worldwide routine coverage regressed during the first pandemic year {evans22}; a follow-up analysis described disruption and stagnation over the first two years, "
      "with tentative recovery in 2022 {evans23}. Ghaznavi <i>et al.</i> estimated global changes in routine childhood coverage for 2020–2021 {ghaznavi}, and the annual MMWR reports summarise worldwide coverage for 2021 and 2022 {rachlin,kaur}. "
      "Supply-side work highlights the need to secure essential health products during emergencies {lal}, and country reviews such as Brazil's compare pre-pandemic and pandemic-period coverage {martins}."),
    sub("B. Inequality, Zero-Dose Children and Targeting"),
    P("Wonodi and Farrenkopf compared two definitions of the zero-dose child across 82 low- and middle-income countries {wonodi}. Dimitrova <i>et al.</i> analysed spatial trends and socioeconomic inequalities in "
      "vaccine coverage across 43 countries {dimitrova}, Saikia <i>et al.</i> examined district-level disparities in India using five survey rounds {saikia}, and Fahmy <i>et al.</i> analysed subnational coverage in seven "
      "high-priority countries {fahmy}. These studies establish that national figures conceal inequality, which motivates the limitation discussed in Section VIII."),
    sub("C. Unsupervised Machine Learning and Cluster Validation"),
    P("K-Means partitions observations by minimising within-cluster squared distance; recent reviews survey its variants and its sensitivity to initialisation, to the choice of K and to non-spherical clusters {ikotun,ezugwu}. "
      "Principal component analysis (PCA) is the standard tool for projecting standardised features onto a few orthogonal axes for visual inspection {greenacre}. "
      "Internal validity indices such as the Davies-Bouldin index have continued to be refined {ros}, and the silhouette coefficient and DBI have been compared with other internal indices {chicco}, "
      "although that comparison was made on two convex clusters. Agreement between two partitions is conventionally measured with the adjusted Rand index {warrens}. "
      "Together these tools justify a validation protocol that combines compactness, separation and stability."),
    sub("D. Summary of Related Works"),
    P("Table I synthesises the contributions and the gap that this paper addresses."),
    TABLE("Synthesis of Related Literature", [
        ["Ref.", "Domain", "Focus relevant to this study"],
        ["{shet}", "Disruption", "Disruption and recovery of routine services in 170 countries and territories."],
        ["{evans22}, {evans23}", "Disruption", "Regression in 2020–2021, stagnation over two years and tentative recovery in 2022."],
        ["{ghaznavi}", "Estimation", "Global changes in routine childhood coverage, 2020–2021."],
        ["{rachlin}, {kaur}", "Surveillance", "Annual worldwide coverage reports for 2021 and 2022."],
        ["{lal}, {martins}", "Systems", "Essential product supply during emergencies; Brazil before and during the pandemic."],
        ["{wonodi}", "Zero dose", "Two zero-dose definitions compared across 82 countries."],
        ["{dimitrova}, {saikia}, {fahmy}", "Inequality", "Spatial, district-level and subnational coverage gaps."],
        ["{engelbert}", "Interventions", "Evidence map of ways to improve routine immunisation."],
        ["{gohari}", "Clustering", "Clustering of countries by COVID-19 incidence and mortality."],
        ["{ikotun}, {ezugwu}", "Algorithms", "K-Means variants and clustering taxonomy."],
        ["{ros}, {chicco}, {warrens}", "Validation", "Davies-Bouldin, silhouette and adjusted Rand index."],
        ["<b>This work</b>", "Clustering", "Recovery-trajectory grouping with validation, stability and policy bands."]],
        [60, 52, 140])]

# III
story += [sec("III. Dataset and Data Preprocessing"), sub("A. Authoritative Coverage and Context Indicators"),
    P("Coverage data are the WHO/UNICEF WUENIC estimates of DTP3 and MCV1 for 2000–2025 {wuenic}. They were downloaded programmatically from the Our World in Data CSV service {owid} on "
      "18 November 2026 with a repeatable script, so the full analysis can be re-run. Context indicators, used only after clustering to describe the groups, are under-5 mortality (latest value 2010–2019), "
      "GDP per person in purchasing-power terms (latest value from 2015), doctors per 1,000 people and births attended by skilled health staff (latest values from 2005), "
      "total fertility rate (from 2015) and the rural share of the population (2024)."),
    sub("B. Data Sanitization and Small-Population Filter"),
    P(f"The source contains 201 countries with DTP3 values; regional aggregates are removed. A country is retained only if every value needed for the six features is observed, which leaves 200 countries. "
      f"Percentages for very small populations rest on a handful of children and swing sharply between years, so the {200 - N} countries with fewer than 100,000 inhabitants (or no population figure) are excluded, "
      f"leaving N = {N}. No clustering feature is imputed. Among the retained countries the context series are missing for {miss['gdp_pc']} (GDP) and {miss['skilled_birth']} (skilled birth attendance) "
      "countries; these gaps are left blank and ignored when group medians are computed."),
    sub("C. Feature Construction and Standardization"),
    P("Let c<sub>i,t</sub> denote the coverage of country i in year t. Six features are built: DTP3 and MCV1 coverage in 2019 (the last year before the pandemic); "
      "the worst DTP3 loss during the disruption,"),
    EQ(r"s_i = \min_{t \in \{2020, 2021, 2022\}} c_{i,t} - c_{i,2019}"),
    P("the net change that remains in 2024 for DTP3 and, analogously, for MCV1,", BODY0),
    EQ(r"\Delta_i = c_{i,2024} - c_{i,2019}"),
    P("and the least-squares slope of DTP3 over 2010–2019, which captures whether a country was already improving or declining. "
      "Because the features have different ranges, each column is standardised to zero mean and unit variance,", BODY0),
    EQ(r"z_{ij} = \frac{x_{ij} - \mu_j}{\sigma_j}"),
    P("so that no feature dominates the Euclidean distance.", BODY0)]

# IV
story += [sec("IV. Research Methodology and System Architecture"), sub("A. System Architecture Overview"),
    P("The end-to-end framework in Fig. 1 ingests the raw series, cleans and filters them, constructs and standardises the features, evaluates three feature-space models over K = 2 to 6, "
      "selects an operational baseline, and then profiles the groups, computes priorities and publishes a dashboard."),
    FIG("fig1_architecture.png", "Fig. 1. System architecture: from raw WUENIC and context series to validated recovery groups and a public dashboard."),
    sub("B. K-Means Clustering Mathematical Formulation"),
    P("Let X = {x<sub>1</sub>, ..., x<sub>N</sub>} be the standardised feature vectors, with N = " + str(N) + ". K-Means partitions X into K clusters C = {C<sub>1</sub>, ..., C<sub>K</sub>} by minimising "
      "the Within-Cluster Sum of Squares (WCSS),"),
    EQ(r"J(\mathcal{C}) = \sum_{k=1}^{K} \sum_{x_i \in C_k} \left\| x_i - \mu_k \right\|_2^2"),
    P("where the centroid of cluster C<sub>k</sub> is its mean,", BODY0),
    EQ(r"\mu_k = \frac{1}{|C_k|} \sum_{x_i \in C_k} x_i"),
    sub("C. Optimization Algorithm and Convergence"),
    P("Optimisation uses Lloyd's algorithm: each point is assigned to its nearest centroid, centroids are recomputed, and the two steps repeat until assignments stop changing {ikotun}. "
      "Initial centroids are chosen with k-means++ to spread them apart, and each model is run with 20 initialisations; the run with the lowest WCSS is kept. "
      "The random state is fixed at 42, and the whole analysis was verified to produce identical labels when repeated."),
    sub("D. Feature Space Pruning Strategies"),
    P("To test how sensitive the groups are to feature redundancy and noise, three formulations are compared. <b>Model A</b> keeps all six features. "
      "<b>Model B</b> removes redundancy: the only feature pair with |r| &gt; 0.85 is DTP3 and MCV1 in 2019 (r = 0.865), so MCV1 2019 is dropped, leaving five features. "
      "<b>Model C</b> removes the pre-pandemic trend, which is estimated from only ten annual values and is the noisiest feature, leaving five features.")]

story += [sub("E. Cluster Validation Metrics"), P("Three criteria are used to judge a partition.", BODY0),
    item("1)", "<i>Silhouette Coefficient (s):</i> for observation i, let a(i) be its mean distance to the other members of its cluster and b(i) its mean distance to the nearest other cluster. Then"),
    EQ(r"s(i) = \frac{b(i) - a(i)}{\max\{a(i),\, b(i)\}}"),
    P("and the reported score is the mean over all i, from −1 to 1; higher is better.", BODY0),
    item("2)", "<i>Davies-Bouldin Index (DBI):</i> the average, over clusters, of the worst ratio of within-cluster scatter to between-centroid distance {ros},"),
    EQ(r"\mathrm{DBI} = \frac{1}{K} \sum_{k=1}^{K} \max_{l \neq k} \frac{\sigma_k + \sigma_l}{d(\mu_k, \mu_l)}"),
    P("where lower values indicate better separation.", BODY0),
    item("3)", "<i>Adjusted Rand Index (ARI) Stability:</i> each model is run from 20 different random seeds, and the mean pairwise ARI over the 190 pairs of runs measures stability {warrens},"),
    EQ(r"\mathrm{ARI} = \frac{\mathrm{RI} - E[\mathrm{RI}]}{\max(\mathrm{RI}) - E[\mathrm{RI}]}"),
    P("where 1 means identical partitions from every initialisation.", BODY0),
    sub("F. Decision-Support Quantities"),
    P("To turn groups into a ranked list, each country receives a priority score that adds the gap to the 90% benchmark in 2024 and any coverage still lost since 2019,"),
    EQ(r"P_i = \max(0,\, 90 - c_{i,2024}) + \max(0,\, -\Delta_i)"),
    P("which is large only for countries that are both low and slipping. The score is a transparent screening aid, not a funding formula.", BODY0)]

# V
tbl2 = [["Model", "Feat.", "K", "WCSS", "Silh.", "DBI", "Mean ARI"]]
for r in ev.itertuples():
    tbl2.append([r.Model, r.Features, r.K, f"{r.WCSS:.2f}", f"{r.Silhouette:.4f}", f"{r.DBI:.4f}", f"{r.Mean_ARI:.4f}"])
bold_rows = [i for i, r in enumerate(ev.itertuples(), 1) if (r.Model, r.K) in (("C", 3), ("A", 4))]
story += [sec("V. Experimental Design and Results"), sub("A. Experimental Environment"),
    P("All experiments run in Python 3.12 with scikit-learn 1.6.1 {sklearn}, NumPy 2.2 and pandas 2.2, with random state 42. The pipeline, a six-test automated suite (data cleanliness, known real-world facts such as Sudan's loss, "
      "naming rules and reproducibility), the figures of this paper and the interactive dashboard are in the public repository https://github.com/Bhubhhu/Kmeans_Clustering. "
      "The dashboard is deployed at https://kmeansclustering-ahoo9tc9xfihmse9ivmvci.streamlit.app/."),
    sub("B. Comprehensive Model Evaluation Across Configurations"),
    P("Table II reports WCSS, silhouette, DBI and 20-seed pairwise ARI for all 15 combinations of model and K. Bold rows are discussed below."),
    TABLE("Model Evaluation Metrics Across Partitional Configurations", tbl2, [34, 30, 22, 38, 38, 38, 52], align="c" * 7, bold_rows=bold_rows),
    sub("C. Selection of the Operational Baseline Configuration"),
    P(f"Model C with K = 3 attains the best silhouette ({C3.Silhouette:.4f}), the lowest DBI among K &le; 4 ({C3.DBI:.4f}) and a mean ARI of {C3.Mean_ARI:.4f}. In purely statistical terms it is the tightest solution. "
      f"However, in both Model A (K = 3, silhouette {A3.Silhouette:.4f}) and Model C (K = 3) the five countries with the largest losses are merged with 17 mid-level countries into one cluster of 22, "
      f"so the most urgent cases disappear into a larger group that needs a different kind of help."),
    P(f"We therefore adopt <b>Model A with K = 4</b> (silhouette {A4.Silhouette:.4f}, DBI {A4.DBI:.4f}, mean ARI {A4.Mean_ARI:.4f}) as the operational baseline. This is a judgement based on usefulness rather than on the highest score, and the choice is stated openly. "
      "Its structure is robust to feature pruning: the adjusted Rand index between the Model A partition and the Model B and Model C partitions at K = 4 is 0.864 and 0.851, respectively.")]

# VI
g3 = [(c, [summ.loc[a, c] if c in summ.columns else None for a in (S, M, L, B)]) for c in ()]
means = df.groupby("archetype")[["dtp3_2019", "mcv1_2019", "dtp3_drop", "dtp3_net", "mcv1_net", "trend_pre", "dtp3_2024", "mcv1_2024", "child_mortality", "physicians", "skilled_birth"]].mean()
labels = {"dtp3_2019": "DTP3 coverage 2019 (%)", "mcv1_2019": "MCV1 coverage 2019 (%)", "dtp3_drop": "DTP3 shock drop (pp)", "dtp3_net": "DTP3 net change (pp)",
          "mcv1_net": "MCV1 net change (pp)", "trend_pre": "DTP3 trend 2010-19 (pp/yr)", "dtp3_2024": "DTP3 coverage 2024 (%)", "mcv1_2024": "MCV1 coverage 2024 (%)",
          "child_mortality": "Under-5 death risk (%)", "physicians": "Doctors per 1,000", "skilled_birth": "Skilled births (%)"}
gaps = (means.max() - means.min()).sort_values(ascending=False)
t3 = [["#", "Indicator", "S", "M", "L", "B", "Gap"]]
for rk, c in enumerate(gaps.index, 1):
    v = [means.loc[a, c] for a in (S, M, L, B)]
    t3.append([rk, labels[c]] + [f"{x:.1f}" for x in v] + [f"{gaps[c]:.1f}"])
t3.append(["", "Countries"] + [str(n[a]) for a in (S, M, L, B)] + [""])
story += [sec("VI. Empirical Results and Comparative Analysis"), sub("A. Baseline Group Profiles and Empirical Divide"),
    P(f"Table III gives the group means of the baseline (S = stable high performers, M = mid-level with slow recovery, L = low but improving, B = COVID backsliders), ranked by the gap between the highest and lowest group mean. "
      f"The three largest divides are {labels[gaps.index[0]]}, {labels[gaps.index[1]]} and {labels[gaps.index[2]]}: the backsliders lost {abs(means.loc[B, 'dtp3_net']):.1f} points of DTP3 on average, "
      f"while the low but improving group gained {means.loc[L, 'dtp3_net']:.1f}."),
    TABLE("Baseline Group Profiles (Model A, K = 4) and Absolute Gaps", t3, [16, 92, 25, 25, 25, 25, 24], align="ccccccc"),
    sub("B. Dimensionality Reduction and PCA Visualization"),
    P("To inspect the groups, the standardised six-dimensional features are projected onto two principal components {greenacre}. PC1 explains 35.21% and PC2 31.78% of the variance, "
      "67.0% in total (Fig. 2). The stable group forms a compact core, the backsliders lie far from it along the shock axis, and the mid-level and low groups spread between them. "
      "Groups touch at their borders, which reflects the gradual change from strong to weak coverage. PCA is used for visualisation only; the clusters are found in the full six-dimensional space."),
    FIG("fig2_pca.png", "Fig. 2. Two-dimensional PCA projection of 182 countries coloured by the baseline group (PC1 = 35.21%, PC2 = 31.78%)."),
    sub("C. Trajectories Before, During and After the Disruption"),
    P(f"Fig. 3 shows the mean DTP3 coverage of each group. The stable group stayed near {ym.loc[S, 2024]:.0f}% throughout. The backsliders averaged {ym.loc[B, 2019]:.1f}% in 2019, "
      f"fell to {ym.loc[B, 2021]:.1f}% in 2021, rose to {ym.loc[B, 2022]:.1f}% in 2022, dropped again to {ym.loc[B, 2024]:.1f}% in 2024 and stood at {ym.loc[B, 2025]:.1f}% in 2025, the newest and most revisable year. "
      f"The mid-level group was already declining before the pandemic, from {ym.loc[M, 2010]:.1f}% in 2010 to {ym.loc[M, 2019]:.1f}% in 2019, and then fell to {ym.loc[M, 2021]:.1f}% in 2021 with almost no recovery. "
      f"The low but improving group rose from {ym.loc[L, 2021]:.1f}% in 2021 to {ym.loc[L, 2024]:.1f}% in 2024 and now exceeds the mid-level group."),
    FIG("fig3_trajectories.png", "Fig. 3. Mean DTP3 coverage of the four groups, 2010–2025. The shaded band marks the 2020–2022 disruption."),
    sub("D. Health-System and Socio-Economic Context of the Groups"),
    P("Fig. 4 shows standardised group means of all indicators, including the context series that were not used for clustering. The stable group combines high skilled birth attendance, "
      f"more doctors ({means.loc[S, 'physicians']:.1f} per 1,000) and lower child mortality. The low but improving group has the opposite profile ({means.loc[L, 'physicians']:.1f} doctors per 1,000, "
      f"{means.loc[L, 'skilled_birth']:.0f}% skilled births), showing that improvement is possible with thin health systems. The backsliders also have few doctors ({means.loc[B, 'physicians']:.1f} per 1,000) and the highest rural share, "
      "which is consistent with fragile gains, but with only five countries these differences are indicative rather than conclusive."),
    FIG("fig5_heatmap.png", "Fig. 4. Standardised group means (z-scores) of the clustering features, 2024 coverage and context indicators. Colour shows level relative to all countries, not desirability."),
    sub("E. Priority Countries"),
    P("Fig. 5 ranks the twelve countries with the highest priority score. Sudan and Lebanon lead, followed by Yemen, Azerbaijan and Kazakhstan. The list contains countries from three groups, "
      "including Central African Republic and Papua New Guinea, which are improving but still reach only 42% of children."),
    FIG("fig4_priority.png", "Fig. 5. The twelve highest-priority countries: DTP3 coverage in 2019 (grey) and 2024 (coloured by group)."),
    sub("F. Multi-Tier Partition Dynamics Across K = 2 to 5")]
mt = [["Country", "K=2", "K=3", "K=4", "K=5", "Group"]]
short = {S: "S", M: "M", L: "L", B: "B"}
for r in mem.itertuples(index=False):
    mt.append([r[0], r[1], r[2], r[3], r[4], short[r[5]]])
sz = {(r.Model, r.K): r.Sizes for r in sizes.itertuples()}
t5 = [["K", "Model A", "Model B", "Model C"]] + [[k, sz[("A", k)], sz[("B", k)], sz[("C", k)]] for k in range(2, 7)]
story += [P("Table IV lists the cluster index of the twelve priority countries in Model A for K = 2 to 5 (indices are ordered by cluster size and carry no meaning of their own), "
            "and Table V gives the partition sizes of all models. At K = 2, Sudan, Lebanon, Myanmar and Romania sit in the large cluster of 145 countries together with the stable group; "
            "at K = 3 they share the smallest cluster (22 countries) with mid-level countries such as Yemen and Kazakhstan; only at K = 4 do Sudan, Lebanon and Myanmar form a cluster of their own, "
            "together with Mozambique and Vanuatu. At K = 5 and above the partitions break into small groups (the smallest has eight countries at K = 5)."),
          TABLE("Cluster Membership of the Twelve Priority Countries (Model A)", mt, [76, 25, 25, 25, 25, 76]),
          TABLE("Partition Size Distributions (Largest Cluster First)", t5, [24, 76, 76, 76], align="cccc")]

# VII
bt = bands
bt_rows = [["DTP3 2024 band", "S", "M", "L", "B", "Total"]]
for idx, r in bt.iterrows():
    bt_rows.append([idx, int(r[S]), int(r[M]), int(r[L]), int(r[B]), int(r["Total"])])
story += [sec("VII. Discussion and Policy Implications"), sub("A. Fixed Descriptive Performance Bands"),
    P("To avoid imposing statistical thresholds, countries are also placed in four fixed descriptive bands of 2024 DTP3 coverage (Table VI). "
      f"The bands are not inferred from the clusters. Cross-tabulating them with the groups shows that all {int(bt.loc['Critical (<60%)', 'Total'])} countries in the critical band belong to the "
      "backsliders, mid-level or low groups, and that 98 of 101 countries meeting the benchmark belong to the stable group."),
    TABLE("Descriptive Bands of 2024 DTP3 Coverage by Baseline Group", bt_rows, [84, 28, 28, 28, 28, 36], align="cccccc"),
    sub("B. Prioritization of Immunisation Interventions"),
    P("The groups suggest different priorities, and the paper presents them as hypotheses for planners rather than as prescriptions."),
    item("1)", f"<i>For severe backsliders ({n[B]} countries):</i> catch-up vaccination for the cohorts missed in 2020–2022 and rapid restoration of routine delivery, since these countries were high before the shock."),
    item("2)", f"<i>For mid-level countries ({n[M]}):</i> because many were already declining before 2020, sustained recovery work such as defaulter tracking, reminders and outreach so that children complete started schedules."),
    item("3)", f"<i>For low but improving countries ({n[L]}):</i> protect the recent gains and extend routine delivery to children who have never been reached."),
    item("4)", f"<i>For stable high performers ({n[S]}):</i> maintain the programme and look for weak districts hidden inside the national average {{dimitrova,saikia}}."),
    sub("C. Methodological Treatment of Small Groups and Peers"),
    P("The group of five backsliders is small, so its averages move with each member; it is best read as a short emergency list rather than as a population. "
      "For every country the dashboard also lists up to three look-alike peers: the nearest countries in standardised feature space that regained at least three more percentage points. "
      "Planners can ask what those countries did differently, which is cheaper than designing a programme from scratch. Micro-states are excluded rather than imputed, because their coverage is noisy by construction.")]

# VIII / IX
story += [sec("VIII. Research Limitations"),
    item("1)", "<i>National Averages:</i> Country-level figures hide districts with many unvaccinated children, which subnational studies show to be substantial {saikia,fahmy}. The results are a first filter, not a district plan."),
    item("2)", "<i>Estimated Inputs:</i> WUENIC values are modelled estimates that can be revised, especially for recent years. Using 2025 instead of 2024 raises the backsliders' mean from 60.0% to 68.2%, although they remain far below 2019."),
    item("3)", "<i>Description, Not Causation:</i> Conflict, economic crisis, funding cuts or data problems may explain a collapse, but none is in the data, and this paper does not test causes."),
    item("4)", "<i>Soft Boundaries and a Judgement on K:</i> Countries change gradually from strong to weak coverage, K = 3 scores a higher silhouette than K = 4, and the choice of K = 4 is justified by usefulness."),
    item("5)", "<i>Two Vaccines Only:</i> The source provided DTP3 and MCV1 but not DTP1, so zero-dose children {wonodi} cannot be counted directly, and newer vaccines are not covered."),
    item("6)", "<i>Partitional Geometry:</i> K-Means assumes compact groups and uses Euclidean distance, so alternative methods such as hierarchical or mixture models could draw the boundaries differently {ikotun,ezugwu}."),
    sec("IX. Conclusion and Future Scope"),
    P(f"This paper developed an objective, unsupervised framework for assessing how childhood immunisation recovered after COVID-19 in {N} countries. Using six trajectory features and three feature-space models, "
      f"K = 2 to 6 were evaluated with WCSS, silhouette, DBI and 20-seed ARI. The statistically tightest solution (Model C, K = 3) hides the most severe cases, so Model A with K = 4 was adopted. "
      f"It identifies {n[S]} stable high performers, {n[M]} mid-level countries with slow recovery, {n[L]} low but improving countries and {n[B]} severe backsliders; {below_prev} countries remain below their 2019 level and {below_tgt} below the 90% benchmark."),
    P("Future work will add district-level data to expose gaps inside countries, include DTP1 to measure zero-dose children directly, cluster the full 2000–2025 time series rather than six summary features, "
      "use soft assignments for countries on group borders, and refresh the analysis whenever new WUENIC estimates are published.")]

story.append(sec("References"))
refs_start = len(story)


# ------------------------------------------------------------------ build
class Doc(BaseDocTemplate):
    pass


W, H = 612, 792
LM, RM, TM, BM, GAP = 45, 45, 50, 55, 18
CW = (W - LM - RM - GAP) / 2
doc = Doc(PDF, pagesize=(W, H), leftMargin=LM, rightMargin=RM, topMargin=TM, bottomMargin=BM,
          title="Post-COVID Childhood Immunisation Recovery Assessment", author="Shubhudeep Singh, Hitesh Kumar")
TITLE_H = 215
first = PageTemplate(id="first", frames=[
    Frame(LM, H - TM - TITLE_H, W - LM - RM, TITLE_H, id="t", leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0),
    Frame(LM, BM, CW, H - TM - TITLE_H - BM, id="c1", leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0),
    Frame(LM + CW + GAP, BM, CW, H - TM - TITLE_H - BM, id="c2", leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)])
later = PageTemplate(id="later", frames=[
    Frame(LM, BM, CW, H - TM - BM, id="l1", leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0),
    Frame(LM + CW + GAP, BM, CW, H - TM - BM, id="l2", leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)])
doc.addPageTemplates([first, later])
from reportlab.platypus import NextPageTemplate  # noqa: E402
story.insert(1, NextPageTemplate("later"))

# reference list (only cited keys, in citation order)
unused = [k for k in REFS if k not in order]
assert not unused, f"uncited references: {unused}"
for i, k in enumerate(order, 1):
    story.append(Paragraph(f"[{i}]&nbsp;&nbsp;{REFS[k]}", REF))
story = [x for f in story for x in ((CondPageBreak(62), f) if isinstance(f, Paragraph) and f.style.name in ("h1", "h2") else (f,))]
doc.build(story)
print("wrote", PDF, "| references:", len(order))
