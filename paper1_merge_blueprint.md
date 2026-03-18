# Paper 1 Merge Blueprint — RNPDNO EDA (Counts Only)

**Target journal:** Journal of Quantitative Criminology (Q1, Springer)  
**Working title:** *Spatial Dynamics of Disappearances in Mexico, 2015–2025: A Municipal-Level Analysis by Outcome Status*  
**Temporal resolution:** Monthly (132 periods, Jan 2015 – Dec 2025)  
**Spatial units:** 2,475 INEGI municipalities  
**Metric scope:** Raw case counts only. Population-normalized rates reserved for Paper 2.  
**Data:** 4 RNPDNO CSVs (total, not located, located alive, located dead)  
**Companion:** Data descriptor submitted independently to Data in Brief.

---

## 1. Series Architecture

| Paper | Target | Core contribution | RNPDNO role |
|-------|--------|-------------------|-------------|
| Data descriptor (submitted) | Data in Brief | Dataset release + schema + pipeline | The dataset itself |
| **Paper 1 (this paper)** | JQC | Outcome-status spatial heterogeneity across 4 categories, monthly, 2015–2025 | Primary and sole data source |
| Paper 2 (future) | JQC or similar | Dual-metric divergence (cases vs. rates), Jaccard framework, policy misallocation | Primary data source + CONAPO population |
| Paper 3 (future) | Econometrics journal | Non-stationary panel: RNPDNO + SESNSP + Banxico + CDC WONDER | One of 5+ data sources |

**Decision gate:** If Paper 1 on counts alone is insufficient for Q1 after seeing results, fold in rates (collapse Paper 1 + Paper 2 into single paper = Option A fallback).

---

## 2. Core Argument

Prior spatial analysis of disappearances in Mexico treats them as a monolithic phenomenon. The RNPDNO registry distinguishes four outcome categories: total registered, disappeared and not located, located alive, and located deceased. These categories reflect fundamentally different processes — active search failure, resolution through recovery, and lethal outcomes — yet no study has examined whether they produce distinct spatial clustering patterns.

We demonstrate that outcome statuses are **not spatially interchangeable**: they cluster in different municipalities, exhibit different temporal dynamics, and follow different regional trajectories. This has direct implications for resource allocation — forensic search teams (targeting "located dead" hotspots) and prevention programs (targeting "not located" concentrations) should not use the same geographic prioritization.

---

## 3. Research Questions

**RQ1 — Spatial concentration:** How geographically concentrated are disappearances, and does concentration differ across outcome statuses?

**RQ2 — Spatial clustering:** Do the four outcome statuses produce distinct spatial cluster geographies? Which municipalities are hotspots for one status but not others?

**RQ3 — Temporal dynamics:** How has the spatial distribution of each outcome status evolved from 2015 to 2025? Do Norte and Bajío exhibit divergent temporal trajectories by outcome?

**RQ4 — Sex disaggregation:** Do male and female disappearances exhibit different spatial-temporal patterns across outcome statuses?

---

## 4. Section-by-Section Plan

### 4.1 Introduction (~1500 words)

**Structure:**
1. Mexico's disappearance crisis — scale (250k+ registered), humanitarian stakes
2. Prior spatial work — Sherman (hotspot policing), Anselin (LISA), Vilalta/Osorio/Atuesta (Mexico-specific)
3. Gap: all prior work treats disappearances as monolithic — no outcome-status decomposition
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
6. NO population data in this paper — counts only.

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
6. Regional composition analysis: count HH municipalities by region, χ² test for distributional change 2015 vs. 2024.
7. Trend analysis: OLS slopes (municipalities/year in HH clusters) by region × status.
8. Sex disaggregation: repeat LISA using male and female columns separately.

**What to DROP:**
- Jaccard similarity (Paper 2)
- Spearman/Kendall correlation (Paper 2)
- Persistence classification with 75th percentile threshold (Paper 2)
- CONAPO population interpolation (Paper 2)
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
- **Figure 1:** Monthly national time series, 4 panels (one per status), disaggregated by sex. Adapts data descriptor's Figure 1 but for all 4 statuses.
- **Table 2:** Summary statistics by outcome status (cross-sectional, cumulative, and per-month)

**Source:** Data descriptor Figure 1 approach, extended to all statuses.

#### §3.2 Geographic Concentration (RQ1) (~600 words)

**Content:**
- Gini and HHI time series for each status across 132 months
- Compare concentration levels across statuses: is Located Dead more concentrated than Not Located?
- Lorenz curves for selected time points (2015-01, 2020-01, 2024-12)
- Key finding: different statuses may have different inequality structures

**Outputs:**
- **Figure 2:** Gini time series (4 lines, one per status). Adapts Paper 1's Figure 1 right panel.
- **Figure 3:** Lorenz curves, 4 statuses × 3 time points (2015, 2020, 2024).
- **Table 3:** Concentration summary (Gini, HHI ranges and trends by status).

**Source:** Paper 1 §3.2.1 logic, recomputed per-status at monthly resolution.

#### §3.3 Spatial Clustering (RQ2) (~800 words)

**Content:**
- Global Moran's I time series by status (132 months × 4 statuses)
- Compare clustering strength across statuses
- LISA classification for recent cross-section (2024-12): HH/LL/HL/LH counts by status
- Cross-tabulation: municipalities that are HH for one status but not others
- Connected-component HH cluster maps

**Outputs:**
- **Figure 4:** Moran's I time series (4 lines). Adapts Paper 1's Figure 2.
- **Figure 5:** 4-panel LISA maps (one per status, 2024-12). Adapts Paper 1's Figure 3 approach.
- **Table 4:** LISA classification counts by status.
- **Table 5:** Cross-tabulation of HH membership across statuses (e.g., how many municipalities are HH for Located Dead AND HH for Not Located?)

**Source:** Paper 1 §3.2.2–3.2.3 + Paper 2 §3.2 logic.

#### §3.4 Temporal Dynamics (RQ3) (~1000 words)

**This is the core section — absorbs Paper 2's main contribution.**

**Content:**
- Regional composition of HH clusters: 2015 vs. 2024, by status (Paper 2's Table 1)
- χ² tests for distributional change
- Temporal trend in HH cluster size: Norte vs. Bajío, by status (Paper 2's Figure 1, monthly)
- OLS trend slopes (Paper 2's Table 2, recomputed monthly)
- Spatial comparison maps: 2015 vs. 2024 (Paper 2's Figure 3)
- Key narratives:
  - Norte: Located Dead emergence (+2.29*** municipalities/year in Paper 2)
  - Bajío: Located Alive collapse (-2.19* municipalities/year in Paper 2)
  - Not Located: regional redistribution

**Outputs:**
- **Table 6:** Regional composition of HH municipalities, 2015 vs. 2024, by status. = Paper 2's Table 1 (recomputed monthly).
- **Table 7:** OLS trend slopes by region × status. = Paper 2's Table 2 (recomputed monthly).
- **Figure 6:** HH municipality count over time, Norte vs. Bajío, 4-panel by status. = Paper 2's Figure 1 (monthly resolution).
- **Figure 7:** LISA maps, 2015-01 vs. 2024-12, for Located Alive and Located Dead. = Paper 2's Figure 3 (monthly).

**Source:** Paper 2 Tables 1–2, Figures 1 and 3. Recompute at monthly resolution.

#### §3.5 Sex Disaggregation (RQ4) (~600 words)

**Content:**
- LISA for male vs. female counts, by status (at least for Not Located and Located Dead)
- Compare HH geographies: do female Located Dead hotspots differ from male?
- Moran's I by sex × status
- If the database `undefined` column is non-trivial, discuss its spatial distribution

**Outputs:**
- **Figure 8:** Male vs. female HH maps for selected statuses (2-panel or 4-panel).
- **Table 8:** HH counts by sex × status.
- Brief comparison statistics (overlap counts).

**Source:** New computation. Uses `male` and `female` columns from all 4 CSVs.

### 4.5 Discussion (~1500 words)

**Structure:**
1. **Outcome-status spatial heterogeneity:** The four statuses are NOT spatially interchangeable. Summarize key divergences.
2. **Regional dynamics narrative:** Norte's Located Dead emergence vs. Bajío's Located Alive decline — what does this mean? Cartel territorial shifts? Differential state search capacity? Frame as hypotheses, not causal claims.
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

### Tables (8)

| # | Content | Source |
|---|---------|--------|
| T1 | Dataset summary by status (rows, persons, coverage) | Data descriptor |
| T2 | Summary statistics by status | New computation |
| T3 | Concentration metrics by status (Gini, HHI) | Paper 1 §3.2.1 logic |
| T4 | LISA classification counts by status (2024-12) | Paper 1 Table 2 logic |
| T5 | Cross-tabulation of HH membership across statuses | New |
| T6 | Regional composition of HH clusters, 2015 vs. 2024 | Paper 2 Table 1 |
| T7 | OLS trend slopes, region × status | Paper 2 Table 2 |
| T8 | HH counts by sex × status | New |

### Figures (8)

| # | Content | Source |
|---|---------|--------|
| F1 | Monthly national time series, 4 panels by status, sex-disaggregated | Data descriptor Fig 1 extended |
| F2 | Gini time series, 4 statuses | Paper 1 Fig 1 logic |
| F3 | Lorenz curves, 4 statuses × 3 years | New |
| F4 | Moran's I time series, 4 statuses | Paper 1 Fig 2 logic |
| F5 | LISA maps, 4-panel by status (2024-12) | Paper 1 Fig 3 logic |
| F6 | HH count over time, Norte vs. Bajío, 4-panel | Paper 2 Fig 1 |
| F7 | LISA maps 2015 vs. 2024, Located Alive + Located Dead | Paper 2 Fig 3 |
| F8 | Male vs. female HH maps | New |

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

**Estimated wall time:** Depends on pipeline. At ~2 sec/run → ~53 minutes. At ~5 sec/run → ~2.2 hours.

### Other Computations

- Gini/HHI: 1,584 scalar computations (trivial)
- Moran's I: computed alongside LISA (no additional cost)
- Connected-component clustering: post-processing on LISA output
- OLS trends: trivial once HH counts are tabulated
- χ² tests: trivial

### Data Requirements

- 4 RNPDNO CSVs (already available)
- INEGI Marco Geoestadístico 2025 shapefile (for spatial weights + mapping)
- Regional classification lookup (from Mexicoencifras or custom mapping)
- NO population data needed

---

## 7. Migration Checklist

### From Paper 1 — KEEP

- [ ] Literature citations: Sherman, Anselin, Vilalta, Osorio, Atuesta, Weisburd, Chainey, Ratcliffe, Prieto Curiel
- [ ] Moran's I equation (Eq. 2)
- [ ] LISA equation (Eq. 3)
- [ ] HHI equation (Eq. 4)
- [ ] Gini equation (Eq. 5)
- [ ] Spatial weights specification (§2.2.1)
- [ ] Concentration dynamics approach (§3.2.1)
- [ ] Spatial autocorrelation time series approach (§3.2.2)
- [ ] LISA mapping approach (§3.2.3)
- [ ] Limitations: ecological fallacy, spatial weights, zero-infilling (§4.5)
- [ ] Reproducibility statement (§2.7)

### From Paper 1 — DROP

- [ ] All rate-based analysis
- [ ] Jaccard similarity (§2.4.1)
- [ ] Spearman/Kendall rank correlation (§2.4.2)
- [ ] Persistence classification (§2.5)
- [ ] CONAPO population data (§2.1)
- [ ] Top-20 rankings (§3.3)
- [ ] Correlation paradox framing
- [ ] "Population confounding" language
- [ ] Female-specific as separate RQ (demoted to sex disaggregation within broader RQ4)

### From Paper 2 — KEEP

- [ ] Regional classification + Bajío sub-flag
- [ ] Connected-component HH clusters (min size = 3)
- [ ] Regional composition table (Table 1)
- [ ] OLS trend slopes (Table 2)
- [ ] Norte vs. Bajío temporal plots (Figure 1)
- [ ] 2015 vs. 2024 LISA comparison maps (Figure 3)
- [ ] χ² test for distributional change

### From Paper 2 — DROP

- [ ] Jaccard similarity between case/rate HH sets (Figure 2)
- [ ] All rate-based LISA
- [ ] Placeholder sections (Introduction, Discussion, Conclusion)

---

## 8. Risk Assessment

### Desk Rejection Risks

| Risk | Severity | Mitigation |
|------|----------|------------|
| "Purely descriptive, no methodological advance" | HIGH | Frame as empirical contribution establishing baseline facts for outcome-disaggregated spatial analysis. JQC publishes spatial empirics regularly. Cite 2021 Geography special issue. |
| "No population normalization" | MEDIUM | Acknowledge explicitly in limitations. Frame as deliberate scope decision: counts capture system burden; rates capture individual risk — different policy questions. Paper 2 forthcoming. |
| "Dataset novelty carries the paper, not analysis" | MEDIUM | The analysis is non-trivial: 4-way cross-tabulation of LISA classifications, temporal trend decomposition by region × status, sex disaggregation. The dataset is cited via DiB, not the contribution itself. |

### Reviewer Objection Predictions

| Likely objection | Pre-emptive defense |
|------------------|---------------------|
| "Why not normalize by population?" | §4 Limitations: explicitly scoped to counts. Cite companion Paper 2 (in preparation). Counts are the relevant metric for system burden / workload allocation. |
| "What explains the regional shifts?" | §4 Discussion: frame as hypotheses (cartel migration, state capacity, administrative factors). This paper documents patterns; causal analysis deferred. |
| "Why monthly instead of quarterly/annual?" | §3 Methods: monthly resolution exploits full temporal granularity of the dataset. Sensitivity to aggregation window could be supplementary. |
| "53 island municipalities — does this matter?" | Online supplement: re-run excluding islands, report change in results. |
| "Why these 5 regions?" | Cite CESOP/Mexicoencifras official classification. Sensitivity with alternative regionalization in supplement. |

---

## 9. Timeline Estimate

| Task | Effort | Dependencies |
|------|--------|-------------|
| Refactor LISA pipeline for monthly × 4 statuses × 3 sex categories | 2–3 days | Existing pipeline |
| Run all 1,584 LISA computations | 1–3 hours | Pipeline ready |
| Compute Gini/HHI/Moran's I time series | 1 hour | Data loaded |
| Generate all 8 figures (publication quality, 300 DPI) | 2–3 days | Results ready |
| Compile all 8 tables | 1 day | Results ready |
| Write Introduction | 1–2 days | Outline approved |
| Write Data + Methods | 1 day | Equations from Paper 1 |
| Write Results | 2–3 days | Figures + tables ready |
| Write Discussion + Conclusion | 1–2 days | Results written |
| Online supplement (robustness checks) | 1–2 days | Main results stable |
| Internal review cycle | 2–3 days | Full draft |
| **Total** | **~2–3 weeks** | |

---

## 10. Option A Fallback Trigger

If after computing results the paper feels thin (e.g., outcome statuses show minimal spatial divergence, or results are unsurprising), the fallback is:

1. Add CONAPO population data
2. Compute rates per 100,000 for all 4 statuses
3. Run dual-metric LISA (cases + rates) for all 4 statuses
4. Add Jaccard similarity framework
5. Add persistence classification
6. Paper becomes: "Outcome-Status and Metric-Dependent Spatial Heterogeneity in Mexico's Disappearance Crisis"

This roughly doubles computational load (1,584 → 3,168 LISA runs) and adds ~3,000 words, but produces a substantially stronger single paper.

**Decision point:** After §3.3 (Spatial Clustering) results are computed. If cross-tabulation of HH membership across statuses shows >60% overlap (i.e., statuses cluster in the same places), the outcome-decomposition story is weak and we trigger Option A.
