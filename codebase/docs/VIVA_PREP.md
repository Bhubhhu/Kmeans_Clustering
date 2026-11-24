# Viva preparation: post-COVID vaccination recovery clustering

Answers are in simple words. Numbers come from `codebase/outputs/`. Learn the numbers in **bold**.

## The one-minute summary (memorise this)

> "After COVID, some countries recovered their child vaccination levels and some did not. Money is limited, so one global plan wastes it. We took real WHO/UNICEF data for **182 countries** and described each one by **6 numbers** about its trajectory: its 2019 level, how hard it fell, how much it regained, and its trend before COVID. K-Means found **4 groups**: **125** stable high performers, **33** mid-level with slow recovery, **19** low but improving, and **5** severe backsliders like Sudan and Lebanon. **105** countries are still below their 2019 level and **81** are below the 90% target. Each group gets a different suggested response, and our dashboard shows the map, a priority list and look-alike countries to learn from. The groups are a guide, not exact labels."

---

## A. The problem and why it is real

**1. What problem does your project solve?**
After COVID, child vaccination fell in most countries. Some bounced back, some did not. Funders and health ministries must decide who to help first and with what. Our groups help match the type of help to the type of problem.

**2. Why is one global plan not enough?**
A country that was doing well and suddenly collapsed needs catch-up campaigns. A country that was always low needs steady outreach. Same money, very different needs.

**3. What is DTP3 and why use it?**
It is the third dose of the diphtheria-tetanus-pertussis vaccine. A child must be reached three times, so it shows how well a country's routine service works. The global target (Immunisation Agenda 2030) is 90%.

**4. Why measles (MCV1) as well?**
It is a second, different vaccine. It checks that the pattern is not just one vaccine's quirk.

**5. Who would use your result?**
Health ministries, funders such as Gavi, WHO and UNICEF, and researchers.

**6. Why clustering and not classification?**
Nobody has labelled countries as "backslider" or "recovering". With no labels, we let the data show the groups. That is unsupervised learning.

**7. Why is a simple ranking of coverage not enough?**
Sudan (fell from 93% to 39%) and Papua New Guinea (rose from 35% to 42%) would sit side by side in a league table. Clustering the shape of the trajectory separates them.

---

## B. Data

**8. Where is your data from?**
WHO/UNICEF coverage estimates (WUENIC) for DTP3 and measles, plus World Bank, UN and WHO context indicators. We download it with `src/fetch_data.py` through the Our World in Data CSV service, which republishes the official series. Be honest about that last part.

**9. Why did you change from your first dataset?**
The first file was not real data (for example India was in the Europe region with high income). The teacher wanted a real problem, so we rebuilt on real, downloaded data.

**10. How many countries and how did you get there?**
201 countries have DTP3 data, 200 have a complete history for all features, and **182** remain after removing very small countries.

**11. Why remove very small countries?**
Countries with under 100,000 people (Nauru, Cook Islands) have percentages based on a handful of children. They swing wildly from year to year and would create fake "collapses".

**12. How did you handle missing values?**
For the six clustering features, a country must have all values, otherwise it is left out. We do not invent them. For context indicators (doctors, income), we use the latest value in a recent window and leave gaps blank.

**13. Why is 2024 the "latest year"?**
It is the latest year we treat as stable. 2025 exists but is the newest and may be revised. Using 2025, the backsliders' average rises from about 60% to 68%. We say this in the report.

---

## C. Features and scaling

**14. What are your six features?**
DTP3 in 2019, measles in 2019, worst DTP3 drop in 2020-22, net change in DTP3 from 2019 to 2024, net change in measles, and the DTP3 trend over 2010-19.

**15. Why these features?**
They describe a story: where the country started, how hard it was hit, whether it recovered, and whether it was already sliding before COVID.

**16. Why did you not cluster on income or region?**
So the groups reflect behaviour and are not just a copy of how rich a country is. Context is added afterwards to describe the groups.

**17. Why standardise (z-score)?**
K-Means uses distances. A feature with bigger numbers or a bigger spread would dominate. Z-score puts all six on the same scale (average 0, spread 1).

**18. Are any features related to each other?**
Yes. For example, the 2019 DTP3 and 2019 measles values move together. That is a small weakness, because "starting level" is counted twice.

---

## D. K-Means and choosing K

**19. How does K-Means work?**
1. Pick K starting centres.
2. Put each country with its nearest centre.
3. Move each centre to the average of its group.
4. Repeat until nothing changes.

**20. What does k-means++ do?**
It picks starting centres that are far from each other, which gives better and steadier results. We also run it 30 times and keep the best.

**21. What are K-Means' weaknesses?**
You must choose K, it likes round groups of similar size, and extreme values pull the centres.

**22. How did you choose K = 4?**
We tried K = 2 to 8 and looked at the elbow, silhouette, Davies-Bouldin and stability. K = 4 has silhouette **0.42**, Davies-Bouldin **1.31** and stability **0.91**. Most importantly, it splits one large middle group into two that need different help.

**23. K = 3 has a higher silhouette (0.46). Why not K = 3?**
This is the likely tricky question. Say it openly: silhouette alone likes fewer, bigger groups. K = 3 merges the severe backsliders (needing urgent catch-up) with the mid-level countries (needing steady recovery). That would hide the most urgent cases. K = 4 is a judgement based on usefulness, and the report says so.

**24. What is the elbow method?**
WCSS is the total spread inside the groups. It always falls as K grows. We look for the bend where adding more groups stops helping much.

**25. What is the silhouette score?**
For each country: does it fit its own group better than the nearest other group? It goes from -1 to 1, and closer to 1 is better.

**26. What is Davies-Bouldin?**
It measures how much groups overlap. Lower is better.

**27. What is seed stability (ARI)?**
We run K-Means from 15 different random starts and compare the groups using the adjusted Rand index. 1 means identical groups every time. At K = 4 it is 0.91, so the result is steady.

**28. Is a silhouette of 0.42 good?**
It is moderate. It means there is real structure, but the boundaries are soft. That fits the data: countries change gradually from strong to weak.

---

## E. Comparing methods

**29. Which other methods did you try and why?**
Ward hierarchical clustering and a Gaussian mixture, on the same data and K = 4. This shows whether the groups belong to the data or are just an effect of K-Means.

**30. What were the results?**

| Method | Silhouette | Davies-Bouldin | Agreement with K-Means (ARI) |
|---|---|---|---|
| K-Means | 0.42 | 1.31 | 1.00 |
| Ward hierarchical | 0.31 | 1.33 | 0.48 |
| Gaussian mixture | 0.24 | 1.68 | 0.41 |

K-Means gave the cleanest groups.

**31. Hierarchical agrees only 0.48 with K-Means. Is that a problem?**
It tells us the boundaries are soft, so the groups are practical categories, not exact ones. The big picture (stable countries versus the rest) is shared by all methods.

**32. What is the difference between K-Means and hierarchical clustering?**
K-Means needs K up front and moves centres until stable. Hierarchical starts with every country alone and merges the closest pairs step by step, building a tree. Once merged, it cannot undo a merge.

**33. What is Mini-Batch K-Means? Did you use it?**
It is a faster K-Means that updates the centres using small random samples of the data. It is for millions of rows. We have 182 rows, so we used normal K-Means, which is more accurate.

**34. Why not DBSCAN?**
It needs dense groups with gaps between them. Our countries form a smooth spread, so DBSCAN would likely give one big blob and some "noise".

---

## F. PCA

**35. What is PCA and why did you use it?**
It squeezes six numbers into two so we can draw the countries on a flat picture. The two components keep about **67%** of the variation (35% + 32%).

**36. Did you cluster on the PCA picture?**
No. Clusters are found using all six features. PCA is only for drawing.

**37. Does PCA reduce rows or columns?**
Columns (features): 6 become 2. All 182 countries (rows) stay.

**38. Does the PCA plot prove the groups are real?**
No. It shows they look separate in 2D, but the groups overlap at the edges because change is gradual.

---

## G. Results

**39. Describe your four groups.**

| Group | Countries | DTP3 2019 → 2024 |
|---|---|---|
| Stable high performers | 125 | 94% → 93% |
| Mid-level, slow recovery | 33 | 79% → 72% |
| Low but improving | 19 | 64% → 73% |
| COVID backsliders | 5 | 88% → 60% |

**40. Who are the backsliders?**
Sudan (93% to 39%), Lebanon (83% to 49%), Myanmar, Mozambique and Vanuatu. They were high before COVID and have not recovered.

**41. How are the groups named?**
By code, from each group's own averages: largest net loss is "backsliders", highest coverage now is "stable", lowest 2019 coverage is "low but improving", the rest "mid-level". Names never depend on the arbitrary cluster number.

**42. What is surprising in the results?**
The mid-level group was already sliding before COVID (about 84% in 2010 to 79% in 2019). So its problem is older than the pandemic.

**43. What did you find in the health-system context?**
Stable countries have more doctors (2.4 per 1,000, 99% skilled births). Low-but-improving countries have only about 0.2 doctors per 1,000, yet are gaining. The backsliders have few doctors and a high rural share (65%). Only 5 countries, so this is indicative, not proven.

**44. Why use context afterwards and not in the clustering?**
Clustering on context would group countries by wealth. We wanted groups by behaviour first, and then ask what they have in common.

---

## H. Real-world use

**45. What is the priority score?**
Points below the 90% target in 2024, plus points still lost since 2019. It highlights countries that are both low and slipping. It is a starting list, not a funding formula.

**46. What help does each group get?**
- Backsliders: urgent catch-up for children missed in 2020-22 and restore routine services.
- Mid-level: defaulter tracking, reminders and outreach so children finish schedules.
- Low but improving: protect the gains, and reach children never vaccinated.
- Stable: maintain, and look for weak districts hidden inside the average.

**47. What are the look-alike peers?**
For each country, the nearest countries in the six-feature space that regained at least 3 more points. Planners can ask what those countries did differently.

**48. Give a worked example.**
Nigeria (66% to 63%) is in the mid-level group. It was already low and has barely recovered, so a long-term recovery plan fits better than an emergency campaign.

**49. What does the dashboard do?**
World map by group, a country report with a coverage chart, a priority list you can download, group profiles, and a method page with limits.

---

## I. Limitations and tricky questions

**50. What are the main limitations?**
- National averages hide weak districts.
- The inputs are estimates and recent years can be revised.
- Groups show what happened, not why (conflict or funding cuts are not in the data).
- The backslider group is tiny (5 countries).
- Boundaries between groups are soft.
- Only two vaccines, so zero-dose children cannot be counted directly.

**51. Can you say why Sudan collapsed?**
No. The data shows what happened, not why. Causes like conflict or economic crisis are outside our data and we did not test them.

**52. Can this tool decide where to send money?**
No. It is a first filter. Decisions need local knowledge and district-level data.

**53. Could the labels harm a country?**
Yes, if used to rank or blame. Labels like "backslider" are meant to direct support, not to judge.

**54. How would you improve it?**
Add district-level data, add DTP1 to count zero-dose children, cluster the whole time series (not six summary numbers), add soft assignments for border countries, and refresh the analysis each year.

**55. Is your result reproducible?**
Yes. One script downloads the data, one script runs the pipeline with fixed random seeds, and our test confirms the groups are identical on a second run. The tests also check known facts, for example that Sudan's coverage fell by more than 30 points.

**56. What would change if you used 2025 instead of 2024?**
The backsliders would look better (about 68% instead of 60%), but they would still be about 20 points below 2019. Group membership could shift slightly.

**57. A country is on the edge between two groups. What do you do?**
Check how close it is to the other group's centre and flag it as borderline. This is why we say groups are a guide, not exact labels.

**58. Is this really unsupervised learning if you named the groups?**
Yes. The algorithm found the groups without any labels. We named them afterwards, from their numbers, to make them understandable.

---

## Honest points to state yourself (do not wait to be asked)

1. K = 3 scores slightly higher than K = 4, and we chose K = 4 for usefulness.
2. The backslider group has only 5 countries.
3. The data comes through Our World in Data, which republishes the official WHO/UNICEF figures.
4. We cannot explain *why* a country fell, only that it did.
