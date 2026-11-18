"""Builds PPT_Presentation.pptx from the real outputs.  Run: python docs/build_deck.py"""
import json
import os

import pandas as pd
from PIL import Image as PILImage
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.util import Inches, Pt

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT, FIG = os.path.join(ROOT, "outputs"), os.path.join(ROOT, "outputs", "figures")
PPTX = os.path.join(os.path.dirname(ROOT), "PPT_Presentation.pptx")

summ = pd.read_csv(os.path.join(OUT, "archetype_summary.csv")).set_index("archetype")
kval = pd.read_csv(os.path.join(OUT, "k_validation.csv"))
meth = pd.read_csv(os.path.join(OUT, "method_comparison.csv"))
info = json.load(open(os.path.join(OUT, "summary.json")))
order = ["Stable high performers", "Mid-level, slow recovery", "Low but improving", "COVID backsliders"]
COLORS = {"Stable high performers": "2A9D8F", "Mid-level, slow recovery": "E9A23B", "Low but improving": "3B82C4", "COVID backsliders": "D1495B"}
DARK, TEAL, GREY = RGBColor(0x1F, 0x4E, 0x5F), RGBColor(0x2A, 0x9D, 0x8F), RGBColor(0x55, 0x55, 0x55)

prs = Presentation()
prs.slide_width, prs.slide_height = Inches(13.333), Inches(7.5)
BLANK = prs.slide_layouts[6]


def add_text(slide, x, y, w, h, text, size=18, bold=False, color=RGBColor(0x22, 0x22, 0x22), align=PP_ALIGN.LEFT):
    tb = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = tb.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.alignment = align
    r = p.add_run()
    r.text = text
    r.font.size, r.font.bold, r.font.color.rgb, r.font.name = Pt(size), bold, color, "Calibri"
    return tb


def new_slide(title, notes=""):
    s = prs.slides.add_slide(BLANK)
    bar = s.shapes.add_shape(1, 0, 0, prs.slide_width, Inches(0.18))
    bar.fill.solid(); bar.fill.fore_color.rgb = TEAL; bar.line.fill.background()
    add_text(s, 0.6, 0.4, 12.1, 0.9, title, 30, True, DARK)
    if notes:
        s.notes_slide.notes_text_frame.text = notes
    return s


def bullets(slide, items, x=0.7, y=1.5, w=12, size=20, gap=10):
    tb = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(5.3))
    tf = tb.text_frame
    tf.word_wrap = True
    for i, it in enumerate(items):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.space_after = Pt(gap)
        head, _, rest = it.partition("|")
        if rest:
            r = p.add_run(); r.text = "• " + head; r.font.bold = True
            r2 = p.add_run(); r2.text = rest
            runs = [r, r2]
        else:
            r = p.add_run(); r.text = "• " + it; runs = [r]
        for rr in runs:
            rr.font.size, rr.font.name = Pt(size), "Calibri"
            rr.font.color.rgb = RGBColor(0x22, 0x22, 0x22)


def picture(slide, name, x, y, w=None, h=None):
    iw, ih = PILImage.open(os.path.join(FIG, name)).size
    if w and not h:
        h = w * ih / iw
    if h and not w:
        w = h * iw / ih
    slide.shapes.add_picture(os.path.join(FIG, name), Inches(x), Inches(y), Inches(w), Inches(h))
    return w, h


def table(slide, rows, x, y, w, col_w, size=14, row_h=0.5):
    shp = slide.shapes.add_table(len(rows), len(rows[0]), Inches(x), Inches(y), Inches(w), Inches(row_h * len(rows)))
    t = shp.table
    for j, cw in enumerate(col_w):
        t.columns[j].width = Inches(cw)
    for i, r in enumerate(rows):
        for j, v in enumerate(r):
            c = t.cell(i, j)
            c.text = str(v)
            for p in c.text_frame.paragraphs:
                for run in p.runs:
                    run.font.size, run.font.name = Pt(size), "Calibri"
                    run.font.bold = i == 0
                    run.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF) if i == 0 else RGBColor(0x22, 0x22, 0x22)
            c.fill.solid()
            c.fill.fore_color.rgb = DARK if i == 0 else (RGBColor(0xF1, 0xF7, 0xF6) if i % 2 else RGBColor(0xFF, 0xFF, 0xFF))
    return t


g = lambda a, k: summ.loc[a, k]

# 1 title
s = prs.slides.add_slide(BLANK)
bg = s.shapes.add_shape(1, 0, 0, prs.slide_width, prs.slide_height); bg.fill.solid(); bg.fill.fore_color.rgb = DARK; bg.line.fill.background()
add_text(s, 0.9, 2.0, 11.5, 2.0, "Which countries are still behind on childhood vaccination after COVID-19, and what do they need?", 38, True, RGBColor(255, 255, 255))
add_text(s, 0.9, 4.3, 11.5, 0.6, "Clustering countries by their vaccination recovery pattern", 22, False, RGBColor(0xBF, 0xE3, 0xDD))
add_text(s, 0.9, 5.6, 11.5, 0.5, "Problem ID BMGF-GAVI-WHO-CLUST-2026   |   RegNo1 (12104501), RegNo2 (12104502), RegNo3 (12104503)", 14, False, RGBColor(0xDD, 0xDD, 0xDD))
s.notes_slide.notes_text_frame.text = ("Our project is about a real problem: after COVID, some countries recovered their child vaccination levels and some did not. "
                                       "We used clustering to find which countries are in which situation, so help can be matched to need.")

# 2 problem
s = new_slide("The real-world problem", "Vaccination fell almost everywhere in 2020-22. But money and staff are limited, so one global plan wastes resources. "
                                       "A country that collapsed needs catch-up campaigns; a country that was always low needs something different.")
bullets(s, ["Vaccination fell almost everywhere in 2020-22.|  Some countries bounced back, some did not, a few collapsed.",
            "Funders and ministries have limited money.|  One global response wastes it.",
            "The decision:|  which countries first, and what kind of help?",
            "Our approach:|  group countries by how their coverage behaved before, during and after COVID, then match help to each group.",
            "Why clustering?|  Nobody has labelled countries as 'recovering' or 'backsliding', so we let the data show the groups."])

# 3 data
s = new_slide("Real data, downloaded and repeatable", "All data is real and public. One script downloads it, so anyone can repeat our work. "
                                                      "We removed micro-states under 100,000 people because their percentages depend on a few children.")
table(s, [["What", "Source"],
          ["DTP3 and measles coverage, 1980-2025", "WHO/UNICEF WUENIC estimates"],
          ["Child mortality, doctors, skilled birth care, fertility", "UN, WHO, World Bank"],
          ["GDP per person, rural share of population", "World Bank, UN"]], 0.7, 1.6, 12, [6, 6], 18, 0.65)
bullets(s, [f"{info['countries']} countries|  after cleaning (201 with DTP3 data, 200 with complete history, then micro-states removed).",
            "Micro-states under 100,000 people left out|  because their percentages rest on very few children."], y=4.5, size=19)

# 4 pipeline
s = new_slide("How the project works", "This is the whole pipeline: real data, features that describe the trajectory, standardise, K-Means, "
                                       "name the groups using their own numbers, profile them with context, and publish a dashboard.")
picture(s, "fig_pipeline.png", 0.6, 1.9, w=12.1)
bullets(s, ["Clustering uses only what happened|  (coverage trajectory). Health-system context is added afterwards to describe the groups."], y=4.8, size=20)

# 5 features
s = new_slide("Six features describe each country's trajectory", "Each country gets six numbers: where it was in 2019, how hard it fell, how much it has regained, "
                                                                 "and whether it was already improving or sliding before COVID. We scale them so none dominates.")
table(s, [["Feature", "Meaning"],
          ["DTP3 and measles in 2019", "Starting point before COVID"],
          ["Worst DTP3 drop 2020-22", "How hard the shock hit"],
          ["Net change 2019 to 2024 (DTP3, measles)", "Still lost, or regained"],
          ["DTP3 trend 2010-19", "Already improving or sliding?"]], 0.7, 1.6, 12, [5.8, 6.2], 18, 0.7)
bullets(s, ["All features are standardised|  (z-score) so none dominates because of its units."], y=5.4, size=19)

# 6 choosing K
s = new_slide("Choosing the number of groups: K = 4", "We tried K from 2 to 8. K=3 has a slightly higher silhouette (0.46 vs 0.42). We chose K=4 because it splits one big middle group "
                                                      "into two that need different help. This is a judgement and we say it openly.")
picture(s, "fig_validation.png", 0.5, 1.4, w=8.4)
bullets(s, ["Elbow|  flattens after K = 3-4.", f"Silhouette|  {kval.loc[kval.K == 4, 'Silhouette'].iloc[0]} at K = 4 (K = 3 is a bit higher: {kval.loc[kval.K == 3, 'Silhouette'].iloc[0]}).",
            f"Stability|  {kval.loc[kval.K == 4, 'Seed_Stability_ARI'].iloc[0]} (1 = same groups every run).",
            "Why 4?|  It separates severe backsliders from mid-level countries, which need different help."], x=9.0, y=1.5, w=4.1, size=17)

# 7 method check
s = new_slide("Cross-check with two other methods", "K-Means gave the cleanest groups. Ward hierarchical only agrees partly with K-Means, which shows the boundaries between groups are soft "
                                                    "because countries change gradually from strong to weak.")
table(s, [["Method (K = 4)", "Silhouette", "Davies-Bouldin", "Agreement with K-Means"]] +
         [[r.Method, r.Silhouette, r.Davies_Bouldin, r.ARI_vs_KMeans] for r in meth.itertuples()], 0.7, 1.7, 12, [4.2, 2.4, 2.6, 2.8], 18, 0.7)
bullets(s, ["K-Means is the best fit|  for this data (higher silhouette, lower Davies-Bouldin).",
            "Hierarchical agrees only partly (0.48):|  boundaries between groups are soft, so read the groups as practical, not exact, categories."], y=4.6, size=19)

# 8 four groups
s = new_slide("Four groups of countries", "Stable high: 125 countries that stayed near 93%. Mid-level: 33 countries that were already sliding and dropped again. "
                                          "Low but improving: 19 countries gaining from a low base. Backsliders: 5 countries that were high, fell about 28 points and have not recovered.")
rows = [["Group", "Countries", "DTP3 2019", "DTP3 2024", "Change"]] + \
       [[a, int(g(a, "countries")), f"{g(a, 'dtp3_2019'):.0f}%", f"{g(a, 'dtp3_2024'):.0f}%", f"{g(a, 'dtp3_net'):+.0f}"] for a in order]
t = table(s, rows, 0.7, 1.6, 12, [5.2, 1.7, 1.7, 1.7, 1.7], 19, 0.75)
for i, a in enumerate(order, 1):
    c = t.cell(i, 0); c.fill.solid(); c.fill.fore_color.rgb = RGBColor.from_string(COLORS[a])
    for p in c.text_frame.paragraphs:
        for r in p.runs:
            r.font.color.rgb = RGBColor(255, 255, 255); r.font.bold = True
bullets(s, [f"{info['below_pre_covid']} of {info['countries']} countries|  are still below their 2019 DTP3 level.",
            f"{info['below_target']} countries|  are below the 90% target.",
            "Severe backsliders:|  Sudan, Lebanon, Myanmar, Mozambique, Vanuatu."], y=5.6, size=18, gap=4)

# 9 trajectories
s = new_slide("The story in one chart", "Stable countries barely moved. Backsliders fell off a cliff in 2021 and are partly back in 2025. "
                                        "Mid-level countries were already sliding before COVID. Low-but-improving countries have gained since 2021.")
picture(s, "fig_trajectories.png", 0.4, 1.7, w=8.6)
bullets(s, ["Backsliders|  fell from 88% to 61% in 2021.", "Mid-level|  was already sliding before COVID (84% to 79%).", "Low but improving|  now above mid-level.",
            "2025|  shows a partial rebound for backsliders (68%)."], x=9.2, y=1.6, w=3.9, size=16)

# 10 context
s = new_slide("Who are they? Health-system context", "We did not use these in the clustering. We use them afterwards to understand each group. "
                                                     "Stable countries have more doctors and nearly all births attended. Low-improving and backsliders have few doctors. "
                                                     "With only 5 backsliders these medians are indicative, not conclusive.")
picture(s, "fig_context.png", 0.5, 1.7, w=12.3)
bullets(s, ["Stable high performers:|  2.4 doctors per 1,000, 99% skilled births.", "Low but improving:|  0.2 doctors per 1,000, yet gaining.",
            "Backsliders:|  few doctors and a 65% rural population, so gains were fragile."], y=5.3, size=18, gap=4)

# 11 priority
s = new_slide("A priority list a planner can use", "Priority score is points below the 90% target plus points still lost since 2019. Sudan is first: 93% to 39%. "
                                                    "Central African Republic and Papua New Guinea are improving but still low, so they stay high on the list.")
picture(s, "fig_priority.png", 0.4, 1.5, h=5.0)
bullets(s, ["Priority score|  = points below 90% now + points still lost since 2019.", "Sudan|  93% to 39%, Lebanon 83% to 49%.",
            "Improving is not enough:|  Central African Republic and Papua New Guinea stay near 42%."], x=8.7, y=1.7, w=4.4, size=17)

# 12 real-world use
s = new_slide("What each group needs", "Each group gets a different suggested focus. We also list look-alike countries that regained more coverage, so planners can learn from them.")
table(s, [["Group", "Suggested focus"],
          ["COVID backsliders", "Urgent catch-up: re-vaccinate the cohorts missed in 2020-22; restore routine services"],
          ["Mid-level, slow recovery", "Defaulter tracking, reminders and outreach so children finish their schedules"],
          ["Low but improving", "Protect the gains: fund routine delivery and reach children never vaccinated"],
          ["Stable high performers", "Maintain; look for weak districts hidden in the national average"]], 0.7, 1.6, 12, [3.8, 8.2], 17, 0.85)
bullets(s, ["Dashboard:|  world map, country report with look-alike peers, downloadable priority list.",
            "Users:|  health ministries, funders (Gavi, WHO, UNICEF, foundations), researchers."], y=6.0, size=17, gap=3)

# 13 limits
s = new_slide("Limits and responsible use", "These limits matter. National averages hide weak districts. Data are estimates. Clusters say what happened, not why. "
                                            "Labels should direct support, not blame countries.")
bullets(s, ["National averages hide weak districts.|  This is a first filter, not a district plan.",
            "Inputs are estimates|  and recent years can be revised (2025 differs from 2024).",
            "Groups show what happened, not why.|  Conflict or funding cuts are not in the data.",
            "One group is tiny|  (5 countries), and boundaries between groups are soft.",
            "Only two vaccines available,|  so zero-dose children cannot be counted directly.",
            "Labels are for directing support,|  not for ranking or blaming countries."], size=20, gap=12)

# 14 conclusion
s = new_slide("Conclusion", "Countries did not lose and regain coverage in the same way. Clustering the trajectories gives four groups, each with a different suggested response. "
                            "Future work: district-level data, DTP1 for zero-dose children, full time-series clustering, soft assignments.")
bullets(s, ["Countries did not recover alike.|  Four groups, from 125 stable countries to 5 severe backsliders.",
            "Each group suggests a different response,|  and the dashboard turns it into a map, a ranked list and peers to learn from.",
            "Next:|  district-level data, DTP1 for zero-dose children, full time-series clustering, soft group assignments."], size=22, gap=16)
add_text(s, 0.7, 5.6, 12, 0.5, "Code and data: github.com/Bhubhhu/Kmeans_Clustering", 16, False, GREY)

prs.save(PPTX)
print("wrote", PPTX, len(prs.slides), "slides")
