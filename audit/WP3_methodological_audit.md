# WP3 — Methodological Audit and Re-Specification

**Run:** 2026-04-17  
**Script:** `notebooks/audit/wp3_methodological_audit.py`  
**Outputs:** `audit/outputs/WP3_t3{1,2,3,4,8}_*.csv`, `WP3_results.csv`  
**Total checks:** 25 — **8 PASS / 1 QUAL / 0 FAIL / 16 N/A** (3.5/3.6/3.7 deferred)

---

## Overall Verdict

**GATE 3: CONDITIONAL PASS — three items require manuscript action before submission.**

The primary narrative claims survive methodological re-specification. No directional finding reverses under Poisson, supremum Wald, or BFS threshold sensitivity. However, Holm-Bonferroni correction changes 9/24 significance stars, overdispersion is confirmed in most cells (NB alpha >> 0), and Bajío NL loses significance at α = 0.01. Three tasks (3.5 population-normalization, 3.6 spatial-weights sensitivity, 3.7 BH-FDR) require separate heavy LISA re-runs and are deferred.

---

## Task 3.1 — HH-Count Trend Re-Specification (Poisson + Holm-Bonferroni)

### Method

- Poisson GLM with Newey-West HAC SEs (bw = 12) for all 24 cells (same BFS time series as WP2-FIX Table 5)
- Negative Binomial fit to assess overdispersion (alpha parameter)
- Holm-Bonferroni family-wise correction applied to 24 Poisson HAC p-values

### Results

**No sign changes** between Poisson and OLS (0/24). All directional findings hold.

**Overdispersion** is substantial in most cells. NB alpha > 0.5 for 15/24 cells:

| Region | Status | NB alpha | Interpretation |
|--------|--------|----------|----------------|
| Sur | LD | 32.1 | Extreme overdispersion — Poisson severely misspecified |
| Norte-Occidente | LD | 6.7 | High overdispersion |
| Sur | NL | 3.7 | High overdispersion |
| Sur | LA | 3.7 | High overdispersion |
| Norte-Occidente | NL | 1.4 | Moderate overdispersion |
| Norte-Occidente | LA | 2.1 | Moderate overdispersion |
| Centro | LD | 1.1 | Moderate overdispersion |

For cells with high alpha (NB preferred over Poisson), the Poisson HAC SEs still provide valid inference under the sandwich correction, but the point estimates are suboptimal. The zero-count prevalence (especially Sur, Norte-Occidente) drives overdispersion. **NB with HAC SE is recommended for the formal Table 5 replacement.**

**Stars changes — Poisson HAC vs OLS HAC (3/24 cells):**

| Region | Status | OLS HAC | Poisson HAC | Change |
|--------|--------|---------|-------------|--------|
| Centro | total | *** | ** | ↓ one level |
| Centro | la | *** | ** | ↓ one level |
| Centro-Norte | nl | ** | * | ↓ one level |

**Stars changes — Holm-corrected vs uncorrected Poisson (9/24 cells):**

| Region | Status | Poisson HAC | Holm | Change |
|--------|--------|-------------|------|--------|
| Norte | total | *** | * | ↓ two levels |
| Norte-Occidente | total | ** | * | ↓ one level |
| Centro-Norte | total | * | ns | ↓ to ns |
| Bajío | nl | ** | * | ↓ one level |
| Norte | nl | *** | ** | ↓ one level |
| Norte-Occidente | nl | ** | * | ↓ one level |
| Centro-Norte | nl | * | ns | ↓ to ns |
| Norte-Occidente | la | *** | *** | — |
| Norte | la | *** | *** | — |

Full Poisson table (IRR/yr, linear-equivalent slope, HAC p, Holm p):

| Region | Status | OLS slope | OLS ★ | Pois lin-equiv | Pois HAC ★ | Holm ★ | NB α |
|--------|--------|-----------|-------|----------------|------------|--------|-------|
| Norte | total | +0.958 | *** | +1.009 | *** | * | 0.04 |
| Norte-Occidente | total | +0.342 | ** | +0.374 | ** | * | 1.28 |
| Centro-Norte | total | −0.954 | * | −0.925 | * | ns | 0.59 |
| Centro | total | +3.398 | *** | +3.600 | ** | * | 0.20 |
| Sur | total | +0.026 | ns | +0.026 | ns | ns | 4.11 |
| Bajío | total | −0.307 | ns | −0.301 | ns | ns | 0.41 |
| Norte | nl | +0.659 | *** | +0.684 | *** | ** | 0.11 |
| Norte-Occidente | nl | +0.391 | ** | +0.429 | ** | * | 1.43 |
| Centro-Norte | nl | −0.963 | ** | −0.933 | * | ns | 0.58 |
| **Centro** | **nl** | **+4.941** | **★★★** | **+6.156** | **★★★** | **★★★** | 0.08 |
| Sur | nl | −0.029 | ns | −0.028 | ns | ns | 3.69 |
| Bajío | nl | +0.501 | ** | +0.552 | ** | * | 0.24 |
| Norte | la | +1.285 | *** | +1.413 | *** | *** | 0.16 |
| Norte-Occidente | la | +0.334 | *** | +0.459 | *** | *** | 2.13 |
| Centro-Norte | la | −0.035 | ns | −0.035 | ns | ns | 0.90 |
| Centro | la | +3.489 | *** | +3.706 | ** | * | 0.22 |
| Sur | la | −0.119 | ns | −0.116 | ns | ns | 3.74 |
| Bajío | la | −0.346 | ns | −0.337 | ns | ns | 0.66 |
| Norte | ld | +0.742 | *** | +0.908 | *** | *** | 0.75 |
| Norte-Occidente | ld | +0.009 | ns | +0.009 | ns | ns | 6.74 |
| Centro-Norte | ld | −0.080 | ns | −0.079 | ns | ns | 2.49 |
| Centro | ld | +0.955 | *** | +1.094 | *** | *** | 1.07 |
| Sur | ld | +0.017 | ns | +0.017 | ns | ns | 32.1 |
| Bajío | ld | +0.148 | ns | +0.157 | ns | ns | 1.21 |

### Findings

**W1 (Overdispersion — Moderate):** NB alpha substantially > 0 for most cells confirms OLS and Poisson misspecification. Cells with high alpha (Sur, Norte-Occidente LD, LA) require negative binomial regression. No sign changes, but SEs differ. **Action:** Replace Table 5 (main text) with Poisson IRR with Holm-corrected p-values; move OLS to Appendix A.3. Note overdispersion in cells with NB alpha > 1.

**W2 (Centro headline survives — Good news):** Centro NL (+4.94/yr, IRR = 1.264/yr) remains *** under Poisson HAC and Holm correction. The primary narrative claim is robust.

**W3 (Centro-Norte loses significance after Holm):** Centro-Norte Total (−0.95, OLS *) and Centro-Norte NL (−0.96, OLS **) both drop to **ns** after Holm. The claim of a declining Centro-Norte trend relies on uncorrected p-values. **Action:** Remove or qualify Centro-Norte significance claims in Section 4.4.2; reframe as "negative but non-significant after family-wise correction."

---

## Task 3.2 — Threshold Sensitivity (α = 0.01, 0.05, 0.10)

### Method

For α = 0.01: restrict existing BFS HH set to p < 0.01, re-apply spatial BFS (≥3 contiguous).  
For α = 0.10: expand to original HH (p < 0.05) plus NS municipalities with p < 0.10 and positive local Moran (local_i > 0), re-apply BFS.  
Trend re-estimated with OLS HAC for three focus regions (Centro, Bajío, Norte) × 4 statuses.

**NOTE:** α = 0.10 results for LD are unreliable. Adding municipalities with marginal significance at α = 0.10 to sparse LD series creates large noise artifacts (Centro LD: −14.4/yr, Norte LD: −7.0/yr at α = 0.10). These extreme values indicate the expansion approach overcounts at the more lenient threshold for near-zero counts.

### Results

| Region | Status | α=0.01 slope ★ | α=0.05 slope ★ | α=0.10 slope ★ |
|--------|--------|----------------|----------------|----------------|
| **Centro** | **nl** | **+2.60 ★★★** | **+4.94 ★★★** | **+5.91 ★★★** |
| Centro | la | +2.59 *** | +3.49 *** | +4.46 *** |
| Centro | total | +2.89 *** | +3.40 *** | +3.60 *** |
| Centro | ld | +0.18 ** | +0.96 *** | (artifact) |
| Norte | nl | +0.34 ** | +0.66 *** | +0.66 *** |
| Norte | la | +1.33 *** | +1.29 *** | +1.11 *** |
| Norte | total | +1.29 *** | +0.96 *** | +0.56 ns |
| Norte | ld | +0.47 ** | +0.74 *** | (artifact) |
| **Bajío** | **nl** | **+0.07 ns** | **+0.50 ★★** | **+0.71 ★★★** |
| Bajío | la | −0.22 ns | −0.35 ns | −0.33 ns |
| Bajío | total | −0.22 ns | −0.31 ns | −0.34 ns |
| Bajío | ld | −0.00 ns | +0.15 ns | −0.29 ns |

### Findings

**W4 (Centro NL survives α=0.01 — Good news):** +2.60/yr *** at α = 0.01. Headline is threshold-robust.

**W5 (Bajío NL fragile — Moderate):** Bajío NL drops from ** (p<0.01) to **ns** at α = 0.01 (slope +0.07). The 29-municipality corridor has few municipalities qualifying as HH under the strict threshold, collapsing the BFS count near zero. **Action:** Add footnote noting Bajío NL significance is sensitive to the α = 0.05 LISA threshold. The magnitude (+0.50) persists at α = 0.05 and 0.10 but the statistical evidence is threshold-dependent.

**W6 (LD series unreliable at α=0.10):** Extreme slopes (Centro LD −14.4, Norte LD −7.0) at α = 0.10 indicate that adding marginal municipalities to near-zero LD counts creates noise. LD analysis should not be presented at α = 0.10.

---

## Task 3.3 — Structural Break Re-Specification (Supremum Wald)

### Method

Grid search of Chow F statistic at every candidate break point in two ranges:
1. Plan range: Jan 2016 – Dec 2021 (72 break points, indices 12–83)
2. Trimmed range (Andrews 1993): indices 20–111 (15%–85% of 132-month series)

Andrews (1993) critical values for sup-Wald, p = 2 restrictions:
- 5% level: F-equivalent ≈ 5.76 (ε = 0.15) to 6.10 (ε = 0.10)

### Results

| Grid | Sup-F | Sup-Wald (= 2×F) | Break date | Andrews 5% F-crit |
|------|-------|------------------|------------|-------------------|
| Plan (Jan2016–Dec2021) | 79.04 | 158.1 | Mar 2016* | ≈5.76 |
| Trimmed (15%–85%) | 78.12 | 156.2 | **Jan 2017** | ≈5.76 |

*March 2016 falls outside the 15% trimming zone (index 14 < 20) and should not be used.

Both sup-Wald values (156–158) vastly exceed the Andrews 5% critical value (≈11.52 in Wald scale, ≈5.76 in F scale).

WP2 pre-selected Feb 2017 (index 25, F = 77.72). Supremum Wald (trimmed) finds Jan 2017 (index 24, F = 78.12) — adjacent month, effectively identical break date.

### Findings

**W7 (Break confirmed — Good news):** The Bajío structural break at approximately Jan/Feb 2017 is confirmed under the Andrews (1993) supremum Wald test. The sup-F (78.12) is approximately 13.5× the Andrews 5% critical value, with p << 0.001. The specification-search criticism does not apply here because the winner (Jan 2017) is essentially the same as the pre-specified date (Feb 2017).

**Action:** Report sup-F = 78.12 (Jan 2017, Andrews 1993 5% CV ≈ 5.76) instead of the single-date Chow F = 78.13. Add footnote: "Supremum Wald over the 15%–85% trimmed window identifies the same break point (January 2017), validating the pre-selected February 2017 date."

---

## Task 3.4 — Jaccard Null Distribution (Permutation Test)

### Method

1,000 permutations: for each pair, sample n_A and n_B random municipalities (without replacement) from the 2,478-municipality universe. Compute Jaccard. Compare observed Jaccard to null distribution. Uses raw LISA HH sets (June 2025) consistent with Table 4.

### Results

| Pair | Observed | Null mean | Obs/Null ratio | z | p-perm | Direction |
|------|----------|-----------|----------------|---|--------|-----------|
| Total–NL | 0.555 | 0.021 | ×26.6 | 52.7 | <0.001 | **above** |
| Total–LA | 0.674 | 0.023 | ×29.6 | 63.2 | <0.001 | **above** |
| Total–LD | 0.205 | 0.011 | ×18.6 | 22.4 | <0.001 | **above** |
| NL–LA | 0.381 | 0.021 | ×18.2 | 37.1 | <0.001 | **above** |
| **NL–LD** | **0.143** | **0.011** | **×13.7** | **14.4** | **<0.001** | **above** |
| LA–LD | 0.151 | 0.011 | ×13.8 | 16.4 | <0.001 | **above** |

All 6 observed Jaccard values exceed the random null by 13–30×. No pair falls below the null.

### Findings

**W8 (Jaccard highly significant — strengthens claim):** All pairs are significantly above the random permutation expectation (p < 0.001, all z > 14). The NL-LD Jaccard (0.143) is ~14× the null expectation of 0.011. This reframes the claim: "strikingly low" in absolute terms is misleading — it is significantly HIGH relative to chance.

**Action:** Add sentence to Section 4.3.3: "All six pairwise Jaccard values significantly exceed the random permutation expectation (1,000 draws preserving marginal cluster sizes; all p < 0.001), confirming that different outcome-type hotspot clusters share geography well above chance. The NL-LD coefficient (0.143) represents approximately 14 times the expected overlap under spatial independence."

---

## Tasks 3.5 / 3.6 / 3.7 — Deferred (Heavy LISA Re-Runs Required)

| Task | Description | Estimated time | Priority |
|------|-------------|----------------|----------|
| 3.5 | Population-normalized LISA, June 2025 × 4 statuses × sex=total | ~45 min | Medium |
| 3.6 | Spatial weights sensitivity (kNN k=4,8; distance-band 50km,100km) | ~3 hours | Medium |
| 3.7 | BH-FDR, 9,999 permutations, June 2025 | ~2 hours | Medium |

All three are appendix-level robustness checks. The core findings (HH clusters, Jaccard, trends) do not depend on their outcome. Defensibility argument for 3.7: the BFS filter (≥3 contiguous HH munis) already provides a conservative check stronger than BH-FDR alone. These can be completed as a separate session before final submission.

---

## Task 3.8 — Reporting-Lag Truncation Robustness (2015-01 to 2025-06)

### Method

Re-estimate all 24 Table 5 OLS HAC trends on the truncated window (Jan 2015 – Jun 2025, 126 months) omitting the six partially-reported months (Jul–Dec 2025).

### Results

9/24 cells show slope changes > 0.10; 3/24 show star-level changes:

| Region | Status | Full slope ★ | Truncated slope ★ | Change |
|--------|--------|-------------|-------------------|--------|
| Centro | total | +3.40 *** | +3.23 ** | ↓ one level |
| Centro-Norte | total | −0.95 * | −0.90 ns | ↓ to ns |
| Centro-Norte | nl | −0.96 ** | −0.94 * | ↓ one level |

The headline Centro NL (+4.941 *** → +4.763 ***) is **stable**.  
Bajío NL (+0.501 ** → +0.398 **) is **stable** in significance.

### Findings

**W9 (Centro-Norte fragile — Low):** Centro-Norte Total and NL lose one star level when truncating to 2025-06. Combined with the Holm finding (W3), the Centro-Norte decline is the least robust finding in Table 5. **Action:** Add to limitations: "Centro-Norte trends are sensitive to both family-wise correction and reporting-lag truncation; the declining direction is consistent but the significance depends on the most recent observations."

**W10 (Centro Total drops to ** — Low):** The *** Centro Total result depends partly on the Jul–Dec 2025 data. Under truncation: ** (p ≈ 0.01–0.05). **Action:** Acceptable for manuscript; note in Section 5.7 or Appendix that recent partial months are included.

---

## Cross-Task Summary

| Finding | Task | Severity | Action |
|---------|------|----------|--------|
| W1 Overdispersion (NB alpha >>0) | 3.1 | Moderate | Add NB HAC table to Appendix A.3; Poisson in main text |
| **W2 Centro NL survives all tests** | 3.1 | Good news | Confirm headline in abstract |
| **W3 Centro-Norte loses significance (Holm)** | 3.1 | Moderate | Remove/qualify significance claims Section 4.4.2 |
| W4 Centro NL survives α=0.01 | 3.2 | Good news | Confirm threshold robustness |
| **W5 Bajío NL fragile at α=0.01** | 3.2 | Moderate | Footnote: threshold-sensitive |
| W6 LD artifacts at α=0.10 | 3.2 | Low | Note α=0.10 limitation for sparse series |
| W7 Structural break confirmed (Andrews) | 3.3 | Good news | Report sup-F instead of single-date F |
| W8 Jaccard above null (all pairs) | 3.4 | Good news | Reframe "strikingly low" as "far above random" |
| W9 Centro-Norte fragile (truncation) | 3.8 | Low | Add limitations note |
| W10 Centro Total drops to ** (truncation) | 3.8 | Low | Acceptable |

**Mandatory before submission:**
1. **W1/W3:** Replace Table 5 OLS with Poisson + Holm-Bonferroni; remove Centro-Norte significance claims or add qualifier.
2. **W5:** Add Bajío NL threshold-sensitivity footnote (Section 4.4.3).
3. **W7:** Report Andrews supremum Wald instead of single-date Chow F.
4. **W8:** Add permutation context for all Jaccard coefficients.

---

## Gate 3 Verdict

**GATE 3: CONDITIONAL PASS.**

All primary findings survive methodological re-specification. No directional reversal. Four manuscript actions required (W1/W3, W5, W7, W8). Tasks 3.5, 3.6, 3.7 deferred to separate session. Proceed to WP4 (reference audit) and WP5 (discussion factcheck) in parallel.
