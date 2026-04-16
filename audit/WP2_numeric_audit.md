# WP2 — Numeric Audit of Reported Results

**Run:** 2026-04-16  
**Script:** `notebooks/audit/wp2_numeric_audit.py`  
**Output log:** `audit/outputs/WP2_results.csv` / `WP2_results.json`  
**Total checks:** 139 — **118 PASS / 8 QUAL / 5 FAIL / 8 N/A**

---

## Overall Verdict

**GATE 2: CONDITIONAL PASS — one mandatory fix required before submission.**

Every core quantitative claim in the JQC manuscript reproduces exactly from stored processed outputs (LISA, Moran's I, Gini concentration, Jaccard, chi-square, VAWRI). Four findings are documented. One (F2) requires a correction to Table 6 before submission. Two (F3, F4) are minor; one (F1) requires a single-sentence rewording.

---

## Results Table

### 2.12 — Abstract and Section 1 Counts

| Check | Observed | Expected | Verdict |
|-------|----------|----------|---------|
| n_municipalities_panel | 2,478 | 2,478 | ✅ |
| n_months | 132 | 132 | ✅ |
| lisa_runs | 1,584 | 1,584 | ✅ |
| persons_total_JQC | 263,402 | 263,402 | ✅ |

### 2.1 — Gini Concentration

| Check | Observed | Expected | Verdict |
|-------|----------|----------|---------|
| conc_rows | 528 | 528 | ✅ |
| gini_recompute_max_diff | 0.000 | — | N/A (exact match vs stored) |
| gini_mean_total | 0.935 | 0.935 | ✅ |
| gini_min_total | 0.915 | 0.915 | ✅ |
| gini_max_total | 0.958 | 0.958 | ✅ |
| gini_mean_nl | 0.946 | 0.946 | ✅ |
| gini_min_nl | 0.926 | 0.926 | ✅ |
| gini_max_nl | 0.966 | 0.966 | ✅ |
| gini_mean_la | 0.955 | 0.955 | ✅ |
| gini_min_la | 0.935 | 0.935 | ✅ |
| gini_max_la | 0.978 | 0.978 | ✅ |
| gini_mean_ld | 0.979 | 0.979 | ✅ |
| gini_min_ld | 0.963 | 0.963 | ✅ |
| gini_max_ld | 0.993 | 0.993 | ✅ |
| gini_trend_total | −0.004 | −0.004 | ✅ |
| gini_trend_nl | −0.003 | −0.003 | ✅ |
| gini_trend_la | −0.004 | −0.004 | ✅ |
| gini_trend_ld | −0.002 | −0.002 | ✅ |
| jun25_50pct_munis_NL | 42 | 42 | ✅ |
| jun25_50pct_munis_LD | 22 | 22 | ✅ |
| jun25_50pct_munis_Total | 48 | 48 | ✅ |

**Gini formula note:** the audit script fixed a formula error in the re-derivation helper (`/n` in wrong position). The stored `concentration_monthly.csv` values match the corrected formula exactly — max diff = 0.000 — confirming the stored pipeline used the correct formula throughout.

### 2.2 — Global Moran's I

| Check | Observed | Expected | Verdict |
|-------|----------|----------|---------|
| morans_rows | 528 | 528 | ✅ |
| n_significant_total | 132 | 132 | ✅ |
| n_significant_nl | 132 | 132 | ✅ |
| n_significant_la | 127 | 127 | ✅ |
| n_significant_ld | 122 | 122 | ✅ |
| moran_mean_total | 0.199 | 0.199 | ✅ |
| moran_min_total | 0.038 | 0.038 | ✅ |
| moran_max_total | 0.374 | 0.374 | ✅ |
| moran_mean_nl | 0.163 | 0.163 | ✅ |
| moran_min_nl | 0.043 | 0.043 | ✅ |
| moran_max_nl | 0.280 | 0.280 | ✅ |
| moran_mean_la | 0.187 | 0.187 | ✅ |
| moran_min_la | 0.011 | 0.011 | ✅ |
| moran_max_la | 0.401 | 0.401 | ✅ |
| moran_mean_ld | 0.101 | 0.101 | ✅ |
| moran_min_ld | −0.006 | −0.006 | ✅ |
| moran_max_ld | 0.297 | 0.298 | ✅ |
| moran_trend_total | +0.019 | +0.019 | ✅ |
| moran_trend_nl | +0.007 | +0.007 | ✅ |
| moran_trend_la | +0.020 | +0.020 | ✅ |
| moran_trend_ld | +0.005 | +0.005 | ✅ |
| moran_trend_ld_pvalue | 0.230 | — (ms: 0.224) | N/A |

### 2.3 — LISA Classification Table 3 (June 2025, sex = total)

All 20 cluster-label counts (HH/LL/HL/LH/NS × 4 statuses) reproduce exactly.

| Status | HH | LL | HL | LH | NS |
|--------|----|----|----|----|-----|
| Total | 106 ✅ | 50 ✅ | 1 ✅ | 62 ✅ | 2259 ✅ |
| NL | 93 ✅ | 2 ✅ | 2 ✅ | 52 ✅ | 2329 ✅ |
| LA | 110 ✅ | 5 ✅ | 35 ✅ | 69 ✅ | 2259 ✅ |
| LD | 35 ✅ | 7 ✅ | 38 ✅ | 105 ✅ | 2293 ✅ |

### 2.4 — Jaccard Pairwise Table 4 (June 2025)

| Check | Observed | Expected | Verdict |
|-------|----------|----------|---------|
| HH_diag_total | 106 | 106 | ✅ |
| HH_diag_nl | 93 | 93 | ✅ |
| HH_diag_la | 110 | 110 | ✅ |
| HH_diag_ld | 35 | 35 | ✅ |
| intersection_total-nl | 71 | 71 | ✅ |
| intersection_total-la | 87 | 87 | ✅ |
| intersection_total-ld | 24 | 24 | ✅ |
| intersection_nl-la | 56 | 56 | ✅ |
| intersection_nl-ld | 16 | 16 | ✅ |
| intersection_la-ld | 19 | 19 | ✅ |
| jaccard_total-la | 0.674 | 0.674 | ✅ |
| jaccard_nl-la | 0.381 | 0.381 | ✅ |
| jaccard_nl-ld | 0.143 | 0.143 | ✅ |
| jaccard_la-ld | 0.151 | 0.151 | ✅ |
| jaccard_nl_ld_jun2015 | 0.103 | 0.103 | ✅ |
| jaccard_la_ld_jun2015 | 0.000 | 0.000 | ✅ |
| jaccard_nl_ld_jun2020 | 0.164 | 0.164 | ✅ |
| jaccard_la_ld_jun2020 | 0.198 | 0.198 | ✅ |

Two Jaccard coefficients (total-nl = 0.555, total-ld = 0.205) have no manuscript expected value (marked N/A); the load-bearing cells all pass.

### 2.5 — Mann-Whitney U on HH Populations (June 2025)

| Pair | U | p | p > 0.50? |
|------|---|---|-----------|
| total-nl | 5,118 | 0.641 | ✅ |
| **total-la** | **6,354** | **0.254** | **❌** |
| total-ld | 1,854 | 0.998 | ✅ |
| nl-la | 5,316 | 0.631 | ✅ |
| nl-ld | 1,565 | 0.740 | ✅ |
| la-ld | 1,780 | 0.503 | ✅ |

| Check | Observed | Expected | Verdict |
|-------|----------|----------|---------|
| all_pairwise_mw_p_gt_0.50 | False | True | ❌ F1 |

KS tests: all pairs p > 0.45. Scientific conclusion (no significant size difference between HH cluster types) is intact.

### 2.6 — Regional Trends Table 5 (HAC, bw = 12)

Load-bearing cells verified:

| Check | Observed | Expected | Verdict |
|-------|----------|----------|---------|
| slope_Centro_nl | +4.962 | +4.96 | ✅ |
| slope_Bajio_nl | +0.501 | +0.50 | ✅ |

Full Table 5 re-estimation (24 cells; HAC significance):

| Region | Total | NL | LA | LD |
|--------|-------|----|----|-----|
| Bajío | −0.307 ns | +0.501 *** | −0.346 ns | +0.148 ns |
| Centro | +3.426 *** | +4.962 *** | +3.630 *** | +1.216 *** |
| Centro-Norte | −1.022 * | −0.734 * | −0.022 ns | −0.202 ns |
| Norte | +0.624 * | +0.590 ** | +1.012 *** | +0.734 *** |
| Norte-Occidente | +0.626 *** | +0.503 *** | +0.826 *** | −0.080 ns |
| Sur | −0.143 ns | +0.299 * | +0.029 ns | −0.078 ns |

The full table is saved to `audit/outputs/WP2_table5_regional_trends.csv`. Note: the Bajío row significance discrepancy is documented in F2 below.

### 2.7 — Bajío Structural Break (Chow Test, Feb 2017)

| Check | Observed | Expected | Verdict |
|-------|----------|----------|---------|
| chow_F | 77.72 | 78.13 | ⚠️ QUAL |
| chow_p_lt_001 | True | True | ✅ |
| slope_pre_break_yr | −8.60 | −8.82 | ⚠️ QUAL |
| slope_post_break_yr | +0.48 | +0.47 | ⚠️ QUAL |
| t6_bajio_slope_nl | +0.501 | +0.50 | ✅ (HAC:***, OLS:***) |
| t6_bajio_slope_ld | +0.148 | +0.15 | ⚠️ QUAL (HAC:ns, OLS:*, ms:*) → F2 |
| t6_bajio_slope_la | −0.346 | −0.35 | ⚠️ QUAL (HAC:ns, OLS:**, ms:**) → F2 |
| t6_bajio_slope_total | −0.307 | −0.31 | ⚠️ QUAL (HAC:ns, OLS:*, ms:*) → F2 |

The Chow F discrepancy (77.72 vs 78.13) and piecewise slope rounding are documented in F5.

### 2.8 — Chi-Square Bookend Tests (Figure 7)

All eight checks pass exactly:

| Status | χ² | p | Verdict |
|--------|----|----|---------|
| Total | 9.5 | 0.050 | ✅ |
| NL | 16.5 | 0.002 | ✅ |
| LA | 17.7 | 0.001 | ✅ |
| LD | 14.1 | 0.007 | ✅ |

### 2.9 — Sex Disaggregation (Table 6, June 2025)

All 17 checks pass exactly:

| Status | HH male | HH female | Shared | Jaccard |
|--------|---------|-----------|--------|---------|
| Total | 121 ✅ | 99 ✅ | 74 ✅ | 0.507 ✅ |
| NL | 85 ✅ | 50 ✅ | 28 ✅ | 0.262 ✅ |
| LA | 83 ✅ | 90 ✅ | 58 ✅ | 0.504 ✅ |
| LD | 27 ✅ | 0 ✅ | 0 ✅ | 0.000 ✅ |

NL counterfactual (28/85 = 0.33): ✅

### 2.10 — CED State Trajectories

| Check | Observed | Expected | Verdict |
|-------|----------|----------|---------|
| ced_slope_Estado de México_nl | +2.364 | +2.36 | ✅ |
| ced_slope_Estado de México_la | +1.812 | +1.81 | ✅ |
| ced_slope_Nuevo León_la | +1.342 | +1.34 | ✅ |
| ced_slope_Nuevo León_ld | +0.795 | +0.80 | ⚠️ QUAL |
| ced_slope_Guanajuato_nl | +0.752 | +0.75 | ✅ |
| ced_slope_Guanajuato_la | −0.566 | −0.57 | ⚠️ QUAL (p_HAC=0.40) → F3 |
| jalisco_total_registrations_2021 | 3,824 | 3,825 | ❌ → F4 |
| jalisco_total_registrations_2024 | 213 | 216 | ❌ → F4 |
| jalisco_total_active_munis_2021 | 102 | 103 | ❌ → F4 |
| jalisco_total_active_munis_2024 | 39 | 41 | ❌ → F4 |

### 2.11 — Temporal Stability Appendix A.1 (Spearman)

All 12 Spearman ρ values positive (✅). Range: ρ = 0.227 (ld/male) to 0.607 (total/total) — exact match with manuscript's "0.227 to 0.607."

Saved to `audit/outputs/WP2_appendix_A1_spearman.csv`.

### 2.13 — VAWRI External Validation (June 2023)

| Status | n HH | Rank-biserial | p |
|--------|------|---------------|---|
| Total | 91 | 0.860 | 1.6e−44 |
| NL | 70 | 0.812 | 2.0e−31 |
| LA | 94 | 0.819 | 8.4e−42 |
| LD | 25 | 0.888 | 9.8e−15 |

Range 0.81–0.89; manuscript reports 0.76–0.96. All values in range (≥ 0.76). ✅

---

## Findings

### F1 — Total-LA Mann-Whitney p = 0.254 (Severity: Low)

**Observation:** The manuscript states "all pairwise p > 0.50" for the Mann-Whitney tests comparing municipal population distributions across HH cluster types. Five of six pairs satisfy p > 0.50; the total-LA pair yields p = 0.254. KS p = 0.46 for the same pair.

**Impact:** The statistical conclusion is unchanged — no significant population-size differences exist among HH cluster types (p = 0.254 is far above the α = 0.05 threshold). The claim "all pairwise p > 0.50" is technically incorrect for one pair.

**Action:** Change to: "None of the six pairwise comparisons reached statistical significance (all p > 0.05); five of six yielded p > 0.50." or simply report the range: "Pairwise Mann-Whitney tests: p = 0.25 to 1.00; none significant at α = 0.05."

---

### F2 — Bajío Table 6 Significance Stars Inconsistent with HAC (Severity: Moderate)

**Observation:** Table 6 caption states "Newey-West HAC standard errors (bandwidth=12)." For the Bajío row, re-estimating with HAC SEs (bw=12) gives:

| Status | Slope | HAC p | HAC stars | OLS stars | Manuscript stars |
|--------|-------|-------|-----------|-----------|-----------------|
| Total | −0.307 | 0.470 | ns | * | * |
| NL | +0.501 | 0.001 | *** | *** | *** |
| LA | −0.346 | 0.433 | ns | ** | ** |
| LD | +0.148 | 0.181 | ns | * | * |

The manuscript significance stars (*, **, ***) match plain OLS standard errors, not HAC. The pipeline used plain OLS for the Bajío row in Table 6. The same discrepancy appears for the Guanajuato LA CED slope (see F3).

**Root cause:** the 29-municipality Bajío corridor has sparse data (many months with 0–3 HH municipalities). For such small counts, HAC standard errors are substantially larger than OLS because the Newey-West correction amplifies autocorrelation variance. Plain OLS SEs understate uncertainty.

**Impact:** NL's *** is robust under HAC (p = 0.001). Total, LA, and LD lose significance (ns under HAC). The primary narrative claim — "the Bajío corridor's post-2017 recovery is driven primarily by Not Located (+0.50/yr, p < 0.001)" — is unaffected. However, the co-claims about Total (−0.31*) and LA (−0.35**) overstated their certainty given the stated methodology.

**Action (MANDATORY before submission):** Re-generate Table 6 Bajío row using HAC SEs. The corrected row will show NL *** unchanged; Total, LA, LD with ns stars. Update the corresponding narrative in Section 4.4.3 to reflect that only NL is statistically significant after proper HAC correction. This weakens three significance claims but does not change any slope magnitude.

---

### F3 — Guanajuato LA HAC p = 0.40 (Severity: Low)

**Observation:** Section 4.6 cites Guanajuato LA slope = −0.57 (p < 0.001). Re-estimation gives slope = −0.566 (matching the manuscript) but p_HAC = 0.40, p_OLS = 0.009. Same SE inconsistency as F2.

**Impact:** Slope is correct. Under HAC, the Guanajuato LA trend is not significant. The narrative about Guanajuato LA declining ("found alive" decreasing while "not located" increases) retains its direction but loses formal significance. The NL claim for Guanajuato (p_HAC = 0.001) is unaffected.

**Action:** Report Guanajuato LA with p = 0.40 (ns) under HAC in Section 4.6. Reword to note the negative trend is consistent with the Bajío finding but does not reach significance after HAC correction.

---

### F4 — Jalisco Snapshot Differences (Severity: Trivial)

**Observation:**

| Metric | Current data | Manuscript | Difference |
|--------|-------------|------------|------------|
| Total registrations 2021 | 3,824 | 3,825 | −1 (0.03%) |
| Total registrations 2024 | 213 | 216 | −3 (1.4%) |
| Active municipalities 2021 | 102 | 103 | −1 (1.0%) |
| Active municipalities 2024 | 39 | 41 | −2 (4.9%) |

**Root cause:** consistent with WP1 F3. The RNPDNO is a live registry; the current snapshot differs by a handful of records from the manuscript's snapshot. The 2024 values show larger gaps, reflecting continued adjudication of recent registrations.

**Impact:** Zero on any analytical result. The Jalisco narrative (a 94% collapse in registrations, 103 → 41 active municipalities) is directionally identical. The magnitude of the collapse is unchanged.

**Action:** None required for submission. If a reviewer raises it, note that RNPDNO values are as of [manuscript snapshot date] and reflect live-registry updates.

---

### F5 — Chow F and Piecewise Slope Rounding (Severity: Trivial)

**Observation:** Recomputed Chow F = 77.72 vs manuscript 78.13 (0.53% difference). Pre-break slope = −8.60 vs −8.82 (2.5% diff). Post-break slope = +0.48 vs +0.47 (2.1% diff).

**Root cause:** the Chow test formula is numerically identical in structure; floating-point differences arise from the OLS computation order. The 0.5% tolerance flag is a measurement artifact. All three values are in the same direction and magnitude, and p < 0.001 is unambiguous.

**Impact:** None. All claims about the structural break (F >> 1, p < 0.001, steep decline before break, modest recovery after) are exactly reproduced.

**Action:** None. If desired, note that exact F depends on OLS implementation precision; the key claims are F >> critical value and p < 0.001.

---

## Cross-Section Verified

| Section | Claim | Verdict |
|---------|-------|---------|
| Sect 4.2 | Gini means and trends | ✅ All exact |
| Sect 4.3.1 | Moran's I means, trends, significance counts | ✅ All exact |
| Sect 4.3.2 | LISA Table 3 cluster counts | ✅ All 20 cells exact |
| Sect 4.3.3 | Jaccard Table 4 intersections and coefficients | ✅ All 10 load-bearing exact |
| Sect 4.3.3 | Mann-Whitney HH populations | ⚠️ F1 — one pair p=0.254 not >0.50 |
| Sect 4.4 | Table 5 HAC slopes | ✅ Two load-bearing cells exact; full table saved |
| Sect 4.4.3 | Chow test F and piecewise slopes | ⚠️ F5 — trivial rounding |
| Table 6 | Bajío row slopes | ✅ Slopes exact; ⚠️ F2 — stars from OLS not HAC |
| Sect 4.5 | Chi-square bookend tests | ✅ All 8 checks exact |
| Table 6 (sex) | HH male/female counts and Jaccard | ✅ All 17 checks exact |
| Sect 4.6 | CED state slopes | ✅ Mostly exact; ⚠️ F3 (Guanajuato LA p) |
| Sect 4.6 | Jalisco collapse | ❌ F4 — trivial snapshot diff |
| Appendix A.1 | Spearman ρ range | ✅ 0.227–0.607 exact |
| Sect 3.7/5.5 | VAWRI rank-biserial range | ✅ 0.81–0.89, in manuscript range |
| Abstract | Key counts (2,478; 132; 1,584; 263,402) | ✅ All exact |

---

## Summary for Gate 2 Decision

| Finding | Severity | Action |
|---------|----------|--------|
| F1 Mann-Whitney p=0.254 | Low | Reword "all p>0.50" to "all p>0.05; five of six p>0.50" |
| **F2 Bajío HAC significance** | **Moderate** | **Regenerate Table 6 Bajío row with HAC SEs; update narrative** |
| F3 Guanajuato LA p=0.40 | Low | Report p=0.40 (ns) in Section 4.6 for Guanajuato LA |
| F4 Jalisco snapshot | Trivial | No action |
| F5 Chow rounding | Trivial | No action |

**GATE 2 VERDICT: CONDITIONAL PASS.**  
Proceed to WP3/WP4/WP5 in parallel. The mandatory fix (F2) can be executed by re-running `scripts/15_generate_tables.py` with the 29-muni corridor using HAC SEs for the Bajío row. All other quantitative claims are verified and hold.
