# Paper 1 Blueprint — RNPDNO Spatial Analysis (Counts Only)

**Target journal:** Journal of Quantitative Criminology (Q1, Springer)
**Working title:** *Spatial Dynamics of Disappearances in Mexico, 2015–2025: A Municipal-Level Analysis by Outcome Status*
**Temporal resolution:** Monthly (132 periods, Jan 2015 – Dec 2025)
**Spatial units:** 2,475 INEGI municipalities
**Metric scope:** Raw case counts only. Population-normalized rates reserved for Paper 2.
**Data:** 4 RNPDNO CSVs (total, not located, located alive, located dead)
**Companion:** Data descriptor submitted independently to Data in Brief.

### Cross-sectional reference period: JUNE

December cross-sections are problematic (seasonal dip, year-end registry lag, Dec 2025 incomplete). All cross-sectional snapshots use **June**. Study period remains Jan 2015 – Dec 2025 (132 months) for time-series/trend analyses.

- **Latest snapshot:** Jun 2025 (Tables 4, 5, 7; Figures 5, 7, 8, 9)
- **Bookend comparison:** Jun 2015 vs. Jun 2025
- **Lorenz curves:** Jun 2015, Jun 2019, Jun 2025
- **Trends (full 132 months, unchanged):** Tables 1–3, 6; Figures 1–4, 6

---

## 1. Series Architecture

| Paper | Target | Core contribution | RNPDNO role |
|-------|--------|-------------------|-------------|
| Data descriptor (submitted) | Data in Brief | Dataset release + schema + pipeline | The dataset itself |
| **Paper 1 (this paper)** | JQC | Outcome-status spatial heterogeneity across 4 categories, monthly, 2015–2025 | Primary and sole data source |
| Paper 2 (future) | Econometrics journal | Non-stationary panel: RNPDNO + SESNSP + Banxico + CDC WONDER | One of 5+ data sources |


---

## 2. Core Argument

There has never been a spatial analysis of disappearances in Mexico, the database to this extent was uknown. The RNPDNO registry distinguishes four outcome categories: total registered, disappeared and not located, located alive, and located deceased. These categories reflect fundamentally different processes — active search failure, resolution through recovery, and lethal outcomes — yet no study has examined whether they produce distinct spatial clustering patterns.

We demonstrate that outcome statuses are **not spatially interchangeable**: they cluster in different municipalities, exhibit different temporal dynamics, and follow different regional trajectories. This has direct implications for resource allocation — forensic search teams (targeting "located dead" hotspots) and prevention programs (targeting "not located" concentrations) should not use the same geographic prioritization.

---

## 3. Research Questions

**RQ1 — Spatial concentration:** How geographically concentrated are disappearances, and does concentration differ across outcome statuses?

**RQ2 — Spatial clustering:** Do the four outcome statuses produce distinct spatial cluster geographies? Which municipalities are hotspots for one status but not others?

**RQ3 — Temporal dynamics:** How has the spatial distribution of each outcome status evolved from 2015 to 2025? Do Centro, Norte and Bajío exhibit divergent temporal trajectories by outcome?

**RQ4 — Sex disaggregation:** Do male and female disappearances exhibit different spatial-temporal patterns across outcome statuses?

---

## 4. Section-by-Section Plan

### 4.1 Introduction (~1500 words)

**Structure:**
1. Mexico's disappearance crisis — scale (250k+ registered), humanitarian stakes
2. Prior spatial work — Sherman (hotspot policing), Anselin (LISA), Vilalta/Osorio/Atuesta (Mexico-specific)
3. Gap: all prior work treats disappearances as monolithic, no full analysis of all the municipalities, no 11 year analysis — no outcome-status decomposition
4. Why outcome status matters: different processes → different geographies → different policy needs
5. Dataset contribution: first machine-readable national RNPDNO extraction (cite DiB descriptor)
6. Four research questions

**Source material:**
- Paper 1 §1: literature citations (Sherman [2], Anselin [3], Chainey [4], Ratcliffe [5], Vilalta [6,7], Osorio [8], Atuesta [9], Weisburd [10])
- Paper 1 §1.1: policy stakes framing
- NEW: outcome-status decomposition motivation (no source — write fresh)

**What to DROP from Paper 1 intro:**
- All dual-metric / rate-based framing
- Jaccard similarity discussion
- Correlation paradox preview
- "Population confounding" language — that's Paper 2's territory

### 4.2 Data (~800 words)

**Structure:**
1. RNPDNO: 4 CSVs, cite data descriptor for full schema. Brief: municipality-month cells, 12-column schema, cvegeo join key, status_id codes (0, 7, 2, 3).
2. Row counts: total = 57,366 rows; not located = 34,665; located alive = 37,363; located dead = 9,883.
3. Sentinel geocodes: 4,162 rows (12,206 persons) with unresolvable geography — excluded from spatial analysis.
4. INEGI Marco Geoestadístico 2025: 2,475 municipalities, EPSG:6372 projection.
5. Regional classification: 5 regions (Sur, Centro, Centro-Norte, Norte, Norte-Occidente) per CESOP/Mexicoencifras scheme. Bajío sub-flag for Centro + Centro-Norte municipalities.
6. You can use population data bands if strictly necessary to explain the phenomena. \begin{tabular}{lcrr}
\toprule
\textbf{Population category} & \textbf{Range (inhabitants)} & \textbf{N} & \textbf{\% of municipalities} \\
\midrule
Community       & $< 2{,}500$                  & 365  & 14.9 \\
Rural           & $2{,}500$--$15{,}000$        & 927  & 37.8 \\
Semi-urban      & $15{,}000$--$50{,}000$       & 720  & 29.3 \\
Small city      & $50{,}000$--$150{,}000$      & 278  & 11.3 \\
Medium city     & $150{,}000$--$500{,}000$     & 114  &  4.6 \\
City            & $500{,}000$--$1{,}000{,}000$ &  37  &  1.5 \\
Large city      & $> 1{,}000{,}000$            &  14  &  0.6 \\
\bottomrule
\end{tabular}

**Key table:**

> **Table 1:** Dataset summary by outcome status

| File | status_id | Rows | Persons | Temporal coverage |
|------|-----------|------|---------|-------------------|
| rnpdno_total.csv | 0 | 57,366 | [sum] | Jan 2015 – Dec 2025 |
| rnpdno_disappeared_not_located.csv | 7 | 34,665 | [sum] | Jan 2015 – Dec 2025 |
| rnpdno_located_alive.csv | 2 | 37,363 | [sum] | Jan 2015 – Dec 2025 |
| rnpdno_located_dead.csv | 3 | 9,883 | [sum] | Jan 2015 – Dec 2025 |

**Source material:**
- Data descriptor (BaseDatosDesapariciones_3.pdf): schema, row counts, sentinel geocodes, processing pipeline
- Paper 1 §2.1: INEGI, projection
- Mexicoencifras.txt: regional classification scheme

### 4.3 Methods (~1200 words)

**Structure:**
1. Spatial weights: Queen contiguity, row-standardized. 53 island municipalities.
2. Global spatial autocorrelation: Moran's I (equation from Paper 1 §2.2.2). Conditional permutation (999 iterations).
3. Local spatial autocorrelation: LISA / Local Moran's I (equation from Paper 1 §2.2.3). HH/LL/HL/LH classification at α = 0.05.
4. Connected-component HH clusters: minimum size = 3 municipalities (from Paper 2 §2.2).
5. Concentration metrics: Gini coefficient, HHI (equations from Paper 1 §2.3).
6. Regional composition analysis: count HH municipalities by region, χ² test for distributional change Jun 2015 vs. Jun 2025. Add and report intermediate chi-squared tests (e.g., Jun 2015 vs. Jun 2019, Jun 2019 vs. Jun 2025) to test whether the shift was gradual.
  abrupt. Or even a trend test across all 11 points.
7. Trend analysis: OLS slopes (municipalities/year in HH clusters) by region × status.
8. Sex disaggregation: repeat LISA using male and female columns separately.

**What to DROP:**
- monthly population interpolation (Paper 2)
- Anything rate-based

**Equations to include (from Paper 1):**
- Moran's I (Eq. 2 in Paper 1)
- Local Moran's I_i (Eq. 3 in Paper 1)
- HHI (Eq. 4 in Paper 1)
- Gini (Eq. 5 in Paper 1)

### 4.4 Results

#### §3.1 Descriptive Overview (~400 words)

**Content:**
- National monthly time series for each status (total, not located, located alive, located dead)
- Sex disaggregation of time series (male/female/undefined)
- Summary statistics by status: min, median, mean, max, SD, skewness

**Outputs:**
- **Figure 1:** Monthly national time series, 4 panels (one per status), disaggregated by sex. Full 132 months.
- **Table 2:** Summary statistics by outcome status (cross-sectional, cumulative, and per-month)

**Source:** Data descriptor Figure 1 approach, extended to all statuses.

#### §3.2 Geographic Concentration (RQ1) (~600 words)

**Content:**
- Gini and HHI time series for each status across 132 months
- Compare concentration levels across statuses: is Located Dead more concentrated than Not Located?
- Lorenz curves for Jun 2015, Jun 2019, Jun 2025
- Key finding: different statuses may have different inequality structures

**Outputs:**
- **Figure 2:** Gini time series (4 lines, one per status). Full 132 months.
- **Figure 3:** Lorenz curves, 4 statuses × 3 time points (Jun 2015, Jun 2019, Jun 2025).
- **Table 3:** Concentration summary (Gini, HHI ranges and trends by status).

**Source:** Paper 1 §3.2.1 logic, recomputed per-status at monthly resolution.

#### §3.3 Spatial Clustering (RQ2) (~800 words)

**Content:**
- Global Moran's I time series by status (132 months × 4 statuses)
- Compare clustering strength across statuses
- LISA classification for Jun 2025: HH/LL/HL/LH counts by status
- Cross-tabulation: municipalities that are HH for one status but not others
- Connected-component HH cluster maps

**Outputs:**
- **Figure 4:** Moran's I time series (4 lines). Full 132 months.
- **Figure 5:** 4-panel LISA maps (one per status, Jun 2025).
- **Table 4:** LISA classification counts by status (Jun 2025).
- **Table 5:** Cross-tabulation of HH membership across statuses (Jun 2025).

**Source:** Paper 1 §3.2.2–3.2.3 + Paper 2 §3.2 logic.

#### §3.4 Temporal Dynamics (RQ3) (~1000 words)

**This is the core section — absorbs Paper 2's main contribution.**

**Content:**
- Regional HH heatmap: 11 yearly June snapshots (Jun 2015–Jun 2025), 4 panels by status — replaces old Table 6
- χ² tests for distributional change (Jun 2015 vs. Jun 2025)
- Temporal trend in HH cluster size: Norte vs. Bajío, by status (monthly)
- OLS trend slopes by region × status
- Spatial comparison maps: Jun 2015 vs. Jun 2025 for Located Alive and Located Dead
- Key narratives:
  - Centro: fastest-growing hotspot region
  - Norte: Located Dead consolidation
  - Bajío: Located Alive decline, Located Dead rise

**Outputs:**
- **Figure 6:** HH municipality count over time, Norte vs. Bajío, 4-panel by status. Full 132 months.
- **Figure 7:** LISA maps, Jun 2015 vs. Jun 2025, for Located Alive and Located Dead.
- **Figure 9:** Regional HH heatmap — 2×2 grid (4 statuses), y-axis = 6 regions, x-axis = 11 years (Jun 2015–Jun 2025), color = HH count, annotated cells. Chi² bookend result in title/caption.
- **Table 6:** OLS trend slopes by region × status. Full 132 months.

**Source:** Paper 2 Tables 1–2, Figures 1 and 3. Recompute at monthly resolution.

#### §3.5 Sex Disaggregation (RQ4) (~600 words)

**Content:**
- LISA for male vs. female counts, by status (at least for Not Located and Located Dead)
- Compare HH geographies: do female Located Dead hotspots differ from male?
- Moran's I by sex × status
- If the database `undefined` column is non-trivial, discuss its spatial distribution

**Outputs:**
- **Figure 8:** Male vs. female HH maps for selected statuses, Jun 2025 (2-panel or 4-panel).
- **Table 7:** HH counts by sex × status (Jun 2025).
- Brief comparison statistics (overlap counts).

**Source:** New computation. Uses `male` and `female` columns from all 4 CSVs.

### 4.5 Discussion (~1500 words)

**Structure:**
1. **Outcome-status spatial heterogeneity:** The four statuses are NOT spatially interchangeable. Summarize key divergences.
2. **Regional dynamics narrative:** Centro's emergence, Norte's Located Dead consolidation, Bajío's Located Alive decline — what does this mean? Cartel territorial shifts? Differential state search capacity? Frame as hypotheses, not causal claims.
3. **Sex patterns:** What do male vs. female spatial differences suggest?
4. **Policy implications (descriptive only):** Forensic teams should be allocated based on Located Dead geography. Prevention resources based on Not Located geography. These may be different places. (Do NOT invoke rate-based arguments — that's Paper 2.)
5. **Limitations:**
   - Raw counts only — no population normalization (explicitly flag as Paper 2's scope)
   - Ecological fallacy (municipality level)
   - Zero-infilling assumption
   - Spatial weights specification
   - Descriptive design — no causal claims
   - Potential underreporting in small/rural municipalities
6. **Future work:** Paper 2 (dual-metric), Paper 3 (econometric), causal designs

**Source material:**
- Paper 1 §4.3: cartel activity, administrative fragmentation (rewrite without rate language)
- Paper 1 §4.5: limitations
- Paper 2 §3.1–3.2 interpretation: regional dynamics narrative
- NEW: outcome-status interpretation

### 4.6 Conclusion (~500 words)

- First national-scale outcome-disaggregated spatial analysis of disappearances
- Key empirical facts established
- Sets up Paper 2 explicitly
- Policy recommendation: outcome-specific geographic targeting

---

## 5. Figure and Table Inventory

### Tables (7)

| # | Content | Cross-section | Source |
|---|---------|---------------|--------|
| T1 | Dataset summary by status (rows, persons, coverage) | Full series | Data descriptor |
| T2 | Summary statistics by status | Full series | New computation |
| T3 | Concentration metrics by status (Gini, HHI) | Full series | Paper 1 §3.2.1 logic |
| T4 | LISA classification counts by status | Jun 2025 | Paper 1 Table 2 logic |
| T5 | Cross-tabulation of HH membership across statuses | Jun 2025 | New |
| T6 | OLS trend slopes, region × status | Full series | Paper 2 Table 2 |
| T7 | HH counts by sex × status | Jun 2025 | New |

### Figures (9)

| # | Content | Time scope | Source |
|---|---------|------------|--------|
| F1 | Monthly national time series, 4 panels by status, sex-disaggregated | Full 132 months | Data descriptor Fig 1 extended |
| F2 | Gini time series, 4 statuses | Full 132 months | Paper 1 Fig 1 logic |
| F3 | Lorenz curves, 4 statuses × 3 snapshots | Jun 2015, Jun 2019, Jun 2025 | New |
| F4 | Moran's I time series, 4 statuses | Full 132 months | Paper 1 Fig 2 logic |
| F5 | LISA maps, 4-panel by status | Jun 2025 | Paper 1 Fig 3 logic |
| F6 | HH count over time, Norte vs. Bajío, 4-panel | Full 132 months | Paper 2 Fig 1 |
| F7 | LISA maps, Located Alive + Located Dead, bookend comparison | Jun 2015 vs. Jun 2025 | Paper 2 Fig 3 |
| F8 | Male vs. female HH maps | Jun 2025 | New |
| F9 | Regional HH heatmap (replaces old Table 6) — 2×2 grid, y=region, x=year, color=HH count, annotated | 11 June snapshots (2015–2025) | New |

---

## 6. Computational Requirements

### LISA Runs

| Variable | Periods | Runs |
|----------|---------|------|
| 4 statuses (total, not located, alive, dead) × total count | 132 | 528 |
| 4 statuses × male count | 132 | 528 |
| 4 statuses × female count | 132 | 528 |
| **Total** | | **1,584** |

Each run: 999 conditional permutations over 2,475 municipalities (~2,422 after sentinel exclusion).

### Data Requirements

- 4 RNPDNO CSVs (already available)
- INEGI Marco Geoestadístico 2025 shapefile (for spatial weights + mapping)
- Regional classification lookup (from Mexicoencifras or custom mapping)
- NO population data needed



## 7. Execution Plan (scripts 14 & 15 updates)

The data pipeline (scripts 10–13) is complete, review. The output scripts need updating:

### A. `scripts/15_generate_tables.py`

1. Set cross-section constants: `XSEC_LATEST = (2025, 6)`, `XSEC_EARLY = (2015, 6)`
2. Update footnote strings: "December 2024/2025" → "June 2025"
3. Remove `make_table6()` (regional composition table → now Figure 9 heatmap)
4. Tables 1, 2, 3, 7 unchanged (full time series)

### B. `scripts/14_generate_figures.py`

1. **Fig 3 Lorenz:** `TIME_POINTS = [(2015, 6, "Jun 2015"), (2019, 6, "Jun 2019"), (2025, 6, "Jun 2025")]`
2. **Fig 5 LISA maps:** year=2025, month=6; title "June 2025"
3. **Fig 7 comparison:** `PERIODS = [(2015, 6, "Jun 2015"), (2025, 6, "Jun 2025")]`
4. **Fig 8 sex maps:** year=2025, month=6; title "June 2025"
5. **NEW Fig 9 — Regional HH heatmap:**
   - Data: `lisa_monthly_results.parquet`, filter sex=="total", cluster_label=="HH", month==6
   - Join with muni_meta for region
   - Count HH municipalities per (year, region, status_id)
   - 2×2 subplot grid (4 statuses)
   - Each panel: heatmap, y=6 regions, x=11 years, color=HH count, annotated cells
   - Chi² bookend test (Jun 2015 vs Jun 2025) in panel title/caption
   - Output: `fig9_regional_hh_heatmap.pdf/.png`
6. Figures 1, 2, 4, 6 unchanged (full time series through Dec 2025)

### C. `manuscript/main.tex`

1. All cross-section references: "December 2024" → "June 2025"
2. Replace Table 6 block with Figure 9 include
3. Update figure/table numbering if renumbering

### D. Execution order

1. Edit `scripts/15_generate_tables.py`
2. Edit `scripts/14_generate_figures.py`
3. Edit `manuscript/main.tex`
4. Run: `conda run -n rnpdno_eda python scripts/15_generate_tables.py`
5. Run: `conda run -n rnpdno_eda python scripts/14_generate_figures.py`
6. Verify outputs

### E. Validation checks

- Table 4 Jun 2025 HH counts: query `lisa_monthly_results.parquet` for year=2025, month=6
- Heatmap: Centro should show clear expansion from ~2019; Bajío decline; Norte consolidation for LA/LD
- Fig 5/7/8 LISA maps should use June data
