# Phase 8 — Executive Summary

Generated: 2026-03-18
Source phases: 01-07 in reports/paper1_verification/
Study period: January 2015 - December 2025 (132 months)
N = 2,478 municipalities | 4 disappearance statuses | 3 sex categories

---

## The 10 Headline Numbers

**1. How many municipalities in the analytical sample?**
N = 2,478 — the complete national universe as of the 2020 census administrative geography. The shapefile, panel, and spatial weights matrix all agree exactly. 52 municipalities (2.1%) have zero Queen contiguity neighbors (islands/enclaves) and are retained in descriptives but do not drive any HH classification.

---

**2. What is the Jaccard index between Not Located and Located Dead HH sets in Dec 2025?**
Jaccard = 0.0345 (intersection=2, union=58).
The located-dead HH set (7 municipalities in Norte region) shares only 2 municipalities with the not-located HH set (53 municipalities, primarily the CDMX metropolitan area). This is the paper's primary non-interchangeability headline for the Dec 2025 reference.
Located Alive vs Located Dead Jaccard = 0.0727 in Dec 2025. All LD pairwise Jaccard values < 0.14 across all reference periods.

---

**3. Which region has the largest positive HH trend slope for each status?**

| Status | Region | Slope/yr | p-value | Sig |
|--------|--------|----------|---------|-----|
| Total | Centro | +2.764 | 0.0008 | * |
| Not Located | Centro | +4.183 | 0.0000 | * |
| Located Alive | Centro | +3.041 | 0.0005 | * |
| Located Dead | Centro | +0.864 | 0.0000 | * |

Centro has the largest absolute slope for all four statuses, driven by the expanding CDMX metropolitan hotspot. Norte has the highest slope for Located Alive among non-Centro regions (+1.098/yr, p<0.0001).

---

**4. Is the "rising Bajio" hypothesis supported?**
NO — formally rejected.
Total Bajio HH municipalities declined at -1.030 municipalities/year (p=0.0120, *), falling from 12 to 9 between December 2015 and December 2025 while other regions grew. No outcome status shows a significant positive Bajio trend (NL: p=0.657, LA: p=0.332, LD: p=0.675). The Bajio region is losing its share of national hotspot municipalities. Key number: Bajio Total slope = -1.030 munis/yr (p=0.0120).

---

**5. Does Centro show significant HH expansion? At monthly resolution? At annual?**
Yes at monthly; yes at annual (with Dec 2025 endpoint).

- Monthly (NW HAC, n=132): Significant for all 4 statuses (p=0.0000-0.0008).
- Annual (HC3, n=11): Significant for all 4 statuses (Total p=0.0223, NL p=0.0000, LA p=0.0183, LD p=0.0000).

With the full 2025 endpoint, the V-shape anomaly (Centro 2016-2018 dip) is overcome and annual slopes are now significant for all statuses. Inflection year for Centro Not Located: annual mean HH rises from 7.1 (2018) to 18.0 (2019) onward.

---

**6. What percentage of municipalities account for 50% of Not Located cases in Dec 2025?**
1.49% of municipalities (37 out of 2,478) contain 50% of all Not Located cases in December 2025 (total=852 cases that month).
Weisburd's (2015) law of crime concentration benchmark: 4-6%.
All four disappearance statuses are 2.7-17x more concentrated than the benchmark: Total=1.57%, Not Located=1.49%, Located Alive=1.09%, Located Dead=0.36%.
Located Dead is the most extreme: half of all fatal outcomes concentrated in approximately 9 municipalities nationally.

---

**7. Are male and female HH sets geographically distinct for Not Located?**
Moderately distinct — Jaccard = 0.3382 (Dec 2025).
Male Not Located: 54 HH municipalities. Female Not Located: 37 HH municipalities (1.46x fewer). Intersection: 23. Located Alive male/female Jaccard = 0.4590 (more similar); Located Dead male/female Jaccard = 0.0000 (no female HH municipalities — see Q8).

---

**8. Is there a statistical power problem for female Located Dead LISA?**
Yes — severe. Results are not interpretable.
Female Located Dead: 2,123 total cases nationally over 132 months (mean 0.0065 cases/municipality/month). 99.42% of municipality-month observations contain zero female Located Dead cases. Maximum in any single municipality-month: 6. In December 2025, female Located Dead LISA produces 0 HH and 2,472 LL — a computational artifact, not a spatial pattern. Male Located Dead (HH=3, Dec 2025) is interpretable but very sparse. Female Located Dead LISA should not be reported as a finding; it must be disclosed as a limitation.

---

**9. Are key findings robust to reference period (Dec 2025 vs Dec 2024)?**
Moderate robustness — overall spatial structure preserved, individual municipality classifications fluctuate.
Jaccard between Dec 2024 and Dec 2025 HH sets: Total=0.3874, NL=0.3232, LA=0.4479, LD=0.0870.
Spearman rank correlation of local_I values (Dec 2024 vs Dec 2025): Total rho=0.4625, NL rho=0.3112, LA rho=0.4142, LD rho=0.2446; all p<0.0001.
The trend slopes, regional narratives, and non-interchangeability arguments are based on the full 132-month series and are not sensitive to cross-section choice. The low LD Jaccard reflects extreme sparseness (only 7 vs 18 HH munis), not structural instability.

---

**10. How many LISA runs were performed in total?**
3,925,152 total LISA observations: 4 statuses x 3 sex categories x 132 months x 2,478 municipalities.
Number of LISA runs: 4 x 3 x 132 = 1,584 runs, each on N=2,478 municipalities.

---

## Files Generated (Phases 1-8)

| File | Content |
|------|---------|
| `01_municipality_reconciliation.md` | N=2,478 confirmed; 52 islands; zero-inflation counts |
| `02_annual_vs_monthly.md` + `.csv` | OLS slopes (NW HAC bw=12) for 20 region x status combos + Bajio |
| `03_concentration.md` + `.csv` | Gini, HHI, Weisburd benchmark for 3 reference periods |
| `04_clustering.md` + `04_jaccard_matrix.csv` | Jaccard matrices for 3 periods; LISA Dec 2025; cluster geography |
| `05_temporal_dynamics.md` + `05_trend_slopes.csv` | 3 narratives with exact Dec 2015 vs Dec 2025 bookmarks |
| `06_sex_disaggregation.md` | Sex composition, M/F Jaccard, female LD power warning |
| `07_robustness.md` | Reference period sensitivity, island, zero-inflation checks |
| `08_executive_summary.md` | This file — 10 headline numbers |

---

## Outstanding Manuscript Issues

1. **LL island artifact (CRITICAL):** 100% of Not Located LL municipalities and 100% of Located Alive LL municipalities in Dec 2025 are islands. Do not interpret LL counts for these statuses as substantive cold-spot findings. Recommend either removing LL from main results tables or adding explicit caveat.

2. **Female Located Dead power:** Must be disclosed as underpowered in methods. Mean 0.0065 cases/muni/month, 99.42% zero muni-months. Do not report female LD LISA maps or HH counts as findings.

3. **Reference period flux:** HH set Jaccard between Dec 2024 and Dec 2025 is 0.32-0.45, indicating notable month-to-month variation. Frame trend-based findings (slopes, regional narratives) as primary; single-month LISA cross-sections as illustrative snapshots.

4. **Centro V-shape:** Annual analysis shows a dip in Centro HH municipalities in 2018 (minimum 12.7 mean monthly munis for Total). This should be acknowledged and explained in the manuscript. The 2019 inflection is the key narrative turning point.

5. **Located Dead Dec 2025 regional shift:** Located Dead HH cluster shifted from Centro (6 munis in Dec 2015) to Norte (7 munis in Dec 2025) with zero Centro HH in Dec 2025. This complete regional realignment for LD is a strong finding but based on very sparse counts (7 total HH munis). Flag uncertainty due to small N.
