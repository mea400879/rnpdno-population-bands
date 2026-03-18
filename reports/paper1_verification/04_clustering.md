# Phase 4 — Clustering and Jaccard

Generated: 2026-03-18 | Study period: Jan 2015 - Dec 2025 (132 months)
Reference cross-section: Dec 2025 (year=2025, month=12)

---

## Moran's I Summary

| Status | Sig months (p<0.05) | I range | I mean | Trend slope/month | p-trend | Sig |
|--------|---------------------|---------|--------|------------------|---------|-----|
| Total (0) | 132/132 (100.0%) | 0.0316-0.3823 | 0.1873 | +0.0016 | 0.0000 | *** |
| Not Located (7) | 132/132 (100.0%) | 0.0374-0.2760 | 0.1501 | +0.0008 | 0.0000 | *** |
| Located Alive (2) | 126/132 (95.5%) | 0.0110-0.4242 | 0.1801 | +0.0016 | 0.0000 | *** |
| Located Dead (3) | 115/132 (87.1%) | -0.0118-0.3571 | 0.0960 | +0.0004 | 0.2567 | ns |

Spatial clustering is significant in virtually all months for Total and Not Located (100%), and nearly all months for Located Alive (95.5%). Located Dead has lower and more volatile Moran's I (87.1% significant, includes months with negative I), reflecting sparse case counts. Trend is significantly increasing for Total, NL, and LA; not significant for LD (p=0.257).

---

## LISA Classifications — Dec 2025 (total sex, N=2,478)

| Status | HH | LL | HL | LH | NS |
|--------|----|----|----|----|-----|
| Total (0) | 72 | 40 | 20 | 42 | 2304 |
| Not Located (7) | 53 | 37 | 17 | 45 | 2326 |
| Located Alive (2) | 52 | 45 | 10 | 56 | 2315 |
| Located Dead (3) | 7 | 2327 | 0 | 0 | 122 |

Note: Located Dead shows a striking asymmetry — only 7 HH municipalities but 2,327 LL (cold spots). This reflects extreme concentration: the entire rural landscape is significantly low-low while cases cluster in a tiny subset of municipalities. HH=7 for LD with no HL or LH is the most distinctive pattern.

---

## Jaccard Matrix

### Jan 2015 (HH counts: Total=61, NL=39, LA=44, LD=2)

| | Total | Not Located | Located Alive | Located Dead |
|--|-------|-------------|---------------|--------------|
| **Total** | 61 | 20 / **0.2500** | 44 / **0.7213** | 1 / **0.0161** |
| **Not Located** | | 39 | 10 / **0.1370** | 0 / **0.0000** |
| **Located Alive** | | | 44 | 0 / **0.0000** |
| **Located Dead** | | | | 2 |

### Jan 2020 (HH counts: Total=96, NL=52, LA=79, LD=23)

| | Total | Not Located | Located Alive | Located Dead |
|--|-------|-------------|---------------|--------------|
| **Total** | 96 | 30 / **0.2542** | 72 / **0.6990** | 14 / **0.1333** |
| **Not Located** | | 52 | 16 / **0.1391** | 7 / **0.1029** |
| **Located Alive** | | | 79 | 12 / **0.1333** |
| **Located Dead** | | | | 23 |

### Dec 2025 (HH counts: Total=72, NL=53, LA=52, LD=7)

| | Total | Not Located | Located Alive | Located Dead |
|--|-------|-------------|---------------|--------------|
| **Total** | 72 | 46 / **0.5823** | 46 / **0.5897** | 5 / **0.0676** |
| **Not Located** | | 53 | 28 / **0.3636** | 2 / **0.0345** |
| **Located Alive** | | | 52 | 4 / **0.0727** |
| **Located Dead** | | | | 7 |

*Format: intersection count / Jaccard index*

### Pairwise Jaccard Trend

| Pair | Jan 2015 | Jan 2020 | Dec 2025 | Interpretation |
|------|----------|----------|----------|----------------|
| Total vs Not Located | 0.2500 | 0.2542 | 0.5823 | Convergence: NL now dominates Total HH |
| Total vs Located Alive | 0.7213 | 0.6990 | 0.5897 | High overlap declining slightly |
| Total vs Located Dead | 0.0161 | 0.1333 | 0.0676 | Low throughout; LD geography distinct |
| NL vs Located Alive | 0.1370 | 0.1391 | 0.3636 | Growing moderate overlap |
| NL vs Located Dead | 0.0000 | 0.1029 | 0.0345 | Consistently low; distinct processes |
| LA vs Located Dead | 0.0000 | 0.1333 | 0.0727 | Very low; most distinct pair |

Non-interchangeability is supported by all LD pairs < 0.14 across all reference periods. The critical Located Alive vs Located Dead Jaccard = 0.0727 (Dec 2025) and 0.0000 in Jan 2015 confirms these are fundamentally different spatial processes.

---

## HH Cluster Geography — Dec 2025

### Total (status 0)
- **N clusters:** 8 | **Total HH munis:** 54 (+ 18 singletons = 72 LISA HH total)
- **Cluster sizes:** 21, 11, 5, 4, 4, 3, 3, 3
- **Largest cluster (n=21):** Centro region — CDMX metropolitan area

### Not Located (status 7)
- **N clusters:** 5 | **Total HH munis:** 34 (+ 19 singletons = 53 LISA HH total)
- **Cluster sizes:** 20, 5, 3, 3, 3
- **Largest cluster (n=20):** Centro region — CDMX metropolitan area

### Located Alive (status 2)
- **N clusters:** 4 | **Total HH munis:** 43 (+ 9 singletons = 52 LISA HH total)
- **Cluster sizes:** 20, 12, 7, 4
- **Largest cluster (n=20):** Centro region — CDMX metropolitan area

### Located Dead (status 3)
- **N clusters:** 1 | **Total HH munis:** 3 (+ 4 singletons = 7 LISA HH total)
- **Cluster sizes:** 3
- **Largest cluster (n=3):** Norte region
- **KEY FINDING:** Located Dead primary cluster is in Norte, NOT in CDMX (Centro). This is the strongest geographic evidence of non-interchangeability.

---

## Headline Numbers for Paper

1. Moran's I significant in **100%** of months for Total and Not Located
2. **NL vs Located Dead Jaccard = 0.0345** (Dec 2025) — primary non-interchangeability headline
3. **LA vs Located Dead Jaccard = 0.0727** (Dec 2025)
4. Located Dead primary cluster: **Norte** (3-municipality cluster)
5. Total / NL / LA primary cluster: **Centro** (CDMX metro area, 20-21 munis)
6. All LD Jaccard pairs < 0.14 across all three reference periods
7. Total LISA runs: 2,478 munis x 4 statuses x 3 sex categories x 132 months = **3,925,152**
