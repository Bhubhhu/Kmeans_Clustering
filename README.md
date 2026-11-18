# Which countries are still behind on childhood vaccination after COVID-19?

Unsupervised clustering of 182 countries by how their DTP3 and measles vaccination coverage behaved
before, during and after the 2020-22 disruption, with a dashboard that suggests what kind of help each
group needs.

## The real-world problem
Routine childhood vaccination fell almost everywhere in 2020-22. Some countries bounced back, some are
still below their 2019 level, and a few collapsed. Donors and health ministries have limited money, so a
single global response is wasteful. This project finds groups of countries with a similar recovery
pattern so that each group can get a different kind of support (for example urgent catch-up
campaigns vs. steady outreach).

## Data (all real, public)
Downloaded by `codebase/src/fetch_data.py` from the Our World in Data CSV endpoint and saved in `codebase/data/raw/`:

| Series | Original source |
|---|---|
| DTP3 and measles (MCV1) coverage, 1980-2025 | WHO/UNICEF WUENIC estimates |
| Under-5 mortality, GDP per person, doctors, skilled birth attendance, fertility, population | UN, World Bank, WHO |

## Method
1. **Features (what happened):** DTP3 and MCV1 in 2019, worst DTP3 drop in 2020-22, net change in DTP3 and MCV1 from 2019 to 2024, DTP3 trend 2010-19. Standardised (z-score).
2. **Data quality:** countries under 100,000 people are excluded (their percentages rest on very few children).
3. **Clustering:** K-Means (k-means++, 30 restarts), K = 4. Checked for K = 2-8 with WCSS, silhouette, Davies-Bouldin and seed stability (ARI), and against Ward hierarchical clustering and a Gaussian mixture.
4. **Profiling (why / who):** context indicators are used only afterwards to describe each group.
5. **Naming:** group names are generated from each group's own averages, not from its numeric id.
6. **Peers:** for each country, the nearest look-alike countries that regained more coverage.
7. **PCA** is used only to draw a 2D picture.

## Result
| Group | Countries | DTP3 2019 | DTP3 2024 |
|---|---|---|---|
| Stable high performers | 125 | 94% | 93% |
| Mid-level, slow recovery | 33 | 79% | 72% |
| Low but improving | 19 | 65% | 73% |
| COVID backsliders (e.g. Sudan, Lebanon, Myanmar) | 5 | 88% | 60% |

105 of 182 countries are still below their 2019 DTP3 level and 81 are below the 90% target.
Final model: silhouette 0.42, Davies-Bouldin 1.31.

## Limits
National averages hide weak districts; WUENIC values are estimates; groups describe what happened, not
why; the backslider group is small; K = 3 has a slightly higher silhouette but K = 4 separates two groups that need different help.

## Run it
```bash
cd codebase
pip install -r requirements.txt
python src/pipeline.py        # rebuilds outputs/ from data/raw/
python -m pytest tests -q     # 6 tests
streamlit run app.py          # dashboard
```
To re-download the raw data: `python src/fetch_data.py`.

## Structure
```text
codebase/
  app.py                # Streamlit dashboard (map, country report, priority list, groups, method)
  src/fetch_data.py     # downloads the real data
  src/pipeline.py       # features, clustering, validation, naming, PCA, outputs
  tests/test_pipeline.py
  data/raw/             # downloaded CSVs
  outputs/              # generated tables
  static/world_110m.json  # bundled map outline (no CDN needed)
  .streamlit/config.toml
```
