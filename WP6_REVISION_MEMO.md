# WP6 — Revision Memo

**Target:** Journal of Quantitative Criminology
**Status:** Pre-submission, final revision
**Execution:** Claude Code computes → Marco writes backwards (conclusion → intro)
**Governing document for all remaining work**

---

## PHASE 1: CLAUDE CODE COMPUTATIONS

No manuscript editing until all five tasks complete. Each task produces a CSV output in `audit/outputs/`.

### CC-1: Table 5 with Proportions (PRIORITY)

**Problem:** Current Table 5 uses raw HH municipality counts, which are not comparable across regions of different sizes (Centro ~600 munis vs Bajío 29). Additionally, significance stars used OLS SEs despite HAC caption.

**Specification:**
- Dependent variable: (BFS-filtered HH municipalities in region / total municipalities in region) × 100, per month
- 6 regions × 4 statuses = 24 cells
- Primary model: OLS with Newey-West HAC SEs (bw=12)
- Robustness: Poisson with HAC SEs
- Family-wise correction: Holm-Bonferroni across 24 tests
- Use `data/processed/lisa_monthly_results.parquet` + `data/processed/municipality_classification_v2.csv`
- Bajío: use `data/external/bajio_corridor_municipalities.csv` (29 municipalities)
- Total municipalities per region: count from `municipality_classification_v2.csv` (for 5 CESOP regions) and from the CSV (29 for Bajío)
- Slopes expressed as percentage points per year (slope × 12)

**Output:** `audit/outputs/WP6_table5_proportions.csv` with columns: Region, Status, N_munis_region, OLS_slope, OLS_SE, OLS_p, HAC_SE, HAC_p, HAC_stars, Poisson_IRR, Poisson_HAC_p, Holm_p, Holm_stars

**Also produce:** `audit/outputs/WP6_table5_raw_counts.csv` — same table but with raw count slopes (the WP2-FIX corrected version) for appendix comparison

### CC-2: Municipality-Level Persistence Table

**Problem:** Regional trend regressions mask which specific municipalities are chronically embedded in HH clusters. Persistence is more informative than slopes for small regions like Bajío.

**Specification:**
- For each municipality × status × sex (total only), compute: number of months classified HH (BFS-filtered) out of 132, expressed as proportion
- Filter: persistence > 0.25 (HH in ≥33 of 132 months)
- Include: cvegeo, municipality name, state, region, status, months_HH, persistence_score
- Sort by persistence descending within each status

**For the Bajío corridor specifically:**
- Separate table for all 29 corridor municipalities, all 4 statuses, no persistence threshold
- Include pre-break persistence (Jan 2015 – Dec 2016, 24 months) and post-break persistence (Jan 2017 – Dec 2025, 108 months) separately

**Output:**
- `audit/outputs/WP6_persistence_national.csv`
- `audit/outputs/WP6_persistence_bajio.csv`

### CC-3: Corrected Bajío Piecewise Slopes

**Problem:** The post-2017 slope p = 0.046 is a legacy ghost. Need definitive piecewise slopes under HAC with the 29-municipality definition on the proportion series.

**Specification:**
- Break at January 2017 (index 24, confirmed by supremum Wald)
- Dependent variable: proportion of 29 corridor municipalities classified HH (BFS), per month
- Pre-break: Jan 2015 – Dec 2016 (24 months)
- Post-break: Jan 2017 – Dec 2025 (108 months)
- 4 statuses, OLS + HAC (bw=12) for each segment
- Also report the supremum Wald: sup-F = 78.12, Andrews 1993 CV ≈ 5.76

**Output:** `audit/outputs/WP6_bajio_piecewise.csv` with columns: Status, Period, Slope_pct_yr, HAC_SE, HAC_p, HAC_stars

### CC-4: Corrected CED State Slopes

**Problem:** Guanajuato LA p < 0.001 is wrong (HAC p = 0.40). Several CED state slopes used OLS SEs.

**Specification:**
- 8 states × 4 statuses = 32 slopes
- Dependent variable: count of HH municipalities per state per month (raw counts are appropriate here — states are not being compared against each other, and HH count within a single state has a natural interpretation)
- OLS + HAC (bw=12)
- Use `data/processed/lisa_monthly_results.parquet`, filter by cve_estado

**Output:** `audit/outputs/WP6_ced_state_slopes.csv` with columns: State, Status, Slope, HAC_SE, HAC_p, HAC_stars, OLS_p

### CC-5: Corrected Mann-Whitney

**Problem:** "All pairwise p > 0.50" is wrong. Need definitive values using BFS-filtered HH sets.

**Specification:**
- June 2025, total sex, BFS-filtered HH sets for all 4 statuses
- For each of 6 pairwise comparisons: Mann-Whitney U, p-value
- Also: KS test p-value
- Use INEGI 2020 municipal populations merged by cvegeo

**Output:** `audit/outputs/WP6_mannwhitney.csv` with columns: Pair, U, MW_p, KS_p

---

## PHASE 2: WRITING SEQUENCE (BACKWARDS)

Marco writes. Claude Code assists with LaTeX. M-RESEARCH reviews each section before proceeding to the next.

### W-1: Conclusion (conclusion.tex)

Write from verified CC-1 through CC-5 outputs. Five empirical findings restated with corrected numbers.

**Changes from current draft:**
- Finding 3 (Centro NL): update slope from +4.96 to proportional equivalent from CC-1
- Finding 4 (Bajío): rewrite entirely. Lead with structural break (sup-F = 78.12, January 2017). Report NL post-break proportion trend from CC-3. Report persistence profile from CC-2. Delete p = 0.046. Delete claims about Total/LA/LD significance.
- Finding 5 (VAWRI): unchanged
- Operational implication: sharpen — "HH classification serves as a comparative instrument for demonstrating spatial non-interchangeability; operational resource targeting requires municipality-level analysis"
- Add sentence: "These findings rest on raw counts, proportional trends, and a descriptive design that cannot identify causal mechanisms"

### W-2: Discussion (discussion.tex)

**Section 5.1 (Non-interchangeability):** Add Jaccard permutation sentence: "All six pairwise Jaccard values significantly exceed the random permutation expectation (1,000 draws; all p < 0.001, z > 14), confirming overlap is well above chance while remaining far below identity."

**Section 5.2 (Regional dynamics):**
- Centro: update slope to proportional value from CC-1. Retain three competing hypotheses. Verify all three are hedged as hypotheses.
- Norte: update slopes from CC-1.
- Bajío (Section 5.2.3): rewrite.
  - Lead with structural break (sup-F, Andrews CV)
  - Persistence profile of corridor municipalities from CC-2 (Irapuato persistent LD, León persistent NL, etc.)
  - NL proportion trend from CC-3 as corroboration
  - Connection to Cadena Vargas & Garrocho and fuel-infrastructure hypothesis
  - Explicitly note small-N limitation
- Centro-Norte: qualify — "negative direction consistent but non-significant after Holm correction and reporting-lag truncation"
- Sur: remove significance claim (Sur NL was +0.30*** under old specification; corrected BFS gives −0.029 ns)

**Section 5.3 (CED alignment):**
- Guanajuato LA: change from p < 0.001 to ns under HAC (p = 0.40). Reword: "the negative direction is consistent with the Not Located rise but does not reach significance after HAC correction"
- Guanajuato NL: verify from CC-4 (HAC p = 0.0013, which is ** not ***)
- "Eightfold increase since 2017" — confirmed from Article 34 decision, attribution correct
- Tabasco: confirmed from Article 34 decision + visit report

**Section 5.4 (Sex patterns):** unchanged

**Section 5.5 (External validation):** unchanged

**Section 5.6 (Institutional context):** add hedge per WP5 M4: "While this trend is consistent with a failure to contain the territorial growth of violence, it may also partly reflect improved registration"

**Section 5.7 (Limitations):**
- Item 1: unchanged (raw counts)
- Item 2: unchanged (ecological fallacy)
- Item 3: add sentence about 75 cross-status inconsistencies (WP1 F2)
- Item 4: unchanged (spatial weights)
- Item 5: unchanged (descriptive design)
- Item 6: unchanged (perpetrator heterogeneity)
- Item 7: change "0.72" to "0.73" (WP1 F4)
- Item 8: unchanged (cross-section sensitivity)
- Item 9: unchanged (registration vs event geography)
- NEW Item 10: "Regional trend slopes (Table 5) use proportions to enable cross-region comparison, but the Bajío corridor (29 municipalities) has limited statistical power for trend detection; the persistence analysis in Table X provides a municipality-level complement"

### W-3: Results

**Section 4.1 (Descriptive):** unchanged — all verified in WP2

**Section 4.2 (Concentration, RQ1):** unchanged — all Gini/HHI verified

**Section 4.3 (Clustering, RQ2):**
- Table 3: unchanged (LISA counts verified)
- Table 4: unchanged (Jaccard verified)
- Add permutation null result: one sentence after the Jaccard discussion
- Mann-Whitney: change "all pairwise p > 0.50" to corrected wording from CC-5. Fix in both abstract and here.
- Spearman stability: unchanged

**Section 4.4 (Temporal dynamics, RQ3):**
- Table 5: replace entirely with proportional version from CC-1
- Section 4.4.1 (Centro expansion): update slope to proportional value. Note proportional trend is robust under Poisson and Holm.
- Section 4.4.2 (Norte): update slopes
- Section 4.4.3 (Bajío): rewrite entirely per W-2 Bajío notes above. Include persistence table reference. Report sup-F instead of Chow F. Break at January 2017.
- Section 4.4.4 (Bookend comparison): update Figure 7 chi-squares (already verified, no change needed). Consider adding June 2019 panel to Figure 6.

**Section 4.5 (Sex disaggregation, RQ4):** unchanged — all verified

**Section 4.6 (CED alignment):** update Guanajuato LA p-value. Update Guanajuato NL stars if needed from CC-4.

### W-4: Methods (methods.tex)

**Section 3.5 (Trend analysis):** rewrite to reflect proportional specification.
- "We fit OLS regressions of the form y_t = α + βt + ε_t where y_t is the proportion of regional municipalities classified HH..."
- Note Holm-Bonferroni across 24 tests
- Note Poisson robustness in appendix
- Andrews supremum Wald for Bajío structural break (cite Andrews 1993 — add to bib)
- Municipality-level persistence as complementary analysis

**Section 3.8 (CED alignment):** unchanged

### W-5: Data (data.tex)

- Add sentence per WP1 F2: "The four outcome files are not perfectly additive; 75 municipality-month observations show minor discrepancies between the Total file and the sum of component files. All analyses use each outcome file independently."

### W-6: Introduction (introduction.tex)

**"19 of 732 investigations, 9 convictions" — MISATTRIBUTION FIX (verified in WP4):**

The manuscript cites `[14, 15]` jointly (García-Castillo + Guevara Bermúdez) for this claim. The audit found:

- The figures come **entirely** from Guevara Bermúdez & Chávez Vargas 2018, page 166, citing PGR and CJF 2017 data: "se reportaron un total de 732 averiguaciones previas (investigaciones) iniciadas en el fuero federal por el delito de desaparición forzada de 2006 a marzo de 2017, de las cuales la PGR solamente judicializó 19. En total, el Poder Judicial emitió, en ese mismo periodo, 9 sentencias condenatorias"
- García-Castillo et al. 2024 does NOT contain these numbers. It reports different figures: 36 sentences by late 2021 (from the CED 2022 visit report), 141 local convictions 2019-2022 (from Impunidad Cero 2023), and 22 federal sentences.
- The numbers 19, 732, and 9 do not appear anywhere in García-Castillo.

**Two fixes required:**

1. Change citation from `\citep{garcia_castillo_2024, guevara_bermudez_2018}` to `\citep{guevara_bermudez_2018}` for the 19/732/9 claim.

2. Change "732 disappearance investigations" to "732 federal investigations for enforced disappearance" (*averiguaciones previas en el fuero federal*). The current wording implies all disappearance investigations nationwide; the actual source specifies these are federal-level only, for the specific crime of enforced disappearance. State-level investigations added another 1,197 per the same Guevara Bermúdez source.

**Optional:** cite García-Castillo separately in a second sentence for the broader impunity context (e.g., "More recent analyses confirm that the pattern persists, with sentencing remaining extremely rare relative to reported cases \citep{garcia_castillo_2024}").

**Other introduction items:**
- "April 2026" — keep (publication date). Update bib note to "Adopted March 2026; published April 2026."
- Verify "2,458 municipalities" for Cadena Vargas & Garrocho (Marco — check the paper manually)

### W-7: Abstract (main.tex)

Last thing written. Update:
- Mann-Whitney: "all pairwise p > 0.05" (delete "> 0.50")
- Centro NL slope: proportional value from CC-1
- Bajío: mention structural break and NL persistence, not composite trend

### W-8: Appendix (appendix.tex)

Add:
- A.3: Raw-count Table 5 (OLS + HAC) for comparison with proportional Table 5
- A.4: Poisson + NB IRR table (from WP3 Task 3.1)
- A.5: Threshold sensitivity (from WP3 Task 3.2) — note LD unreliable at α = 0.10
- A.6: Reporting-lag truncation comparison (from WP3 Task 3.8)
- Persistence table (national, supplementary material)

---

## PHASE 3: BIBLIOGRAPHY AND HOUSEKEEPING

After all sections are written:

1. Replace `\citep{le_cour_2020}` with `\citep{reyes_robo_2022}` in discussion.tex
2. Fix 19/732/9 citation: `\citep{garcia_castillo_2024, guevara_bermudez_2018}` → `\citep{guevara_bermudez_2018}` in introduction.tex. Change "732 disappearance investigations" → "732 federal investigations for enforced disappearance"
3. Delete duplicate bib entries: `baptista_2026`, `prieto_curiel_cartels_2023`
4. Add Andrews 1993 to bib (for supremum Wald)
5. Add Holm 1979 to bib (for Holm-Bonferroni) if not already present
6. Update `escobar_rnpdno_2026` bib note when accepted
7. Update CED bib note: "Adopted March 2026; published April 2026"
8. Fix `\cite{code_repo}` in declarations or remove unused entry
9. Remove/comment out 45 unused bib entries
10. Verify Cadena Vargas & Garrocho "2,458 municipalities" claim (Marco)

---

## PHASE 4: DEFERRED ITEMS (BEFORE OR AFTER SUBMISSION)

| Item | Effort | Priority | When |
|------|--------|----------|------|
| WP3.5 Population-normalized LISA (June 2025, appendix) | 1 afternoon | Medium | Before submission if time; otherwise R1 |
| WP3.6 Spatial weights sensitivity | 3 hours | Low | R1 |
| WP3.7 BH-FDR 9,999 permutations | 2 hours | Low | R1 |
| Figure 6 June 2019 panel | 1 hour | Low | Before submission if time |
| EDA paper erratum: "2,025 municipalities" includes 66 sentinels | — | Low | When EDA proofs arrive |

---

## EXECUTION CHECKLIST

```
PHASE 1 — Claude Code
[ ] CC-1  Table 5 proportions
[ ] CC-2  Persistence table (national + Bajío)
[ ] CC-3  Bajío piecewise (proportions, HAC)
[ ] CC-4  CED state slopes (HAC)
[ ] CC-5  Mann-Whitney (BFS, definitive)
[ ] Git commit: "audit(WP6): phase 1 computations"

PHASE 2 — Marco writes (backwards)
[ ] W-1  Conclusion
[ ] W-2  Discussion
[ ] W-3  Results
[ ] W-4  Methods
[ ] W-5  Data
[ ] W-6  Introduction
[ ] W-7  Abstract
[ ] W-8  Appendix
[ ] Each section reviewed by M-RESEARCH before next

PHASE 3 — Housekeeping
[ ] le_cour_2020 fix
[ ] 19/732/9 citation fix (Guevara only, not García-Castillo jointly)
[ ] "732 federal investigations for enforced disappearance" wording fix
[ ] Duplicate bib entries deleted
[ ] Andrews 1993 + Holm 1979 added
[ ] CED bib note updated
[ ] Unused entries removed
[ ] Cadena Vargas municipality count verified

PHASE 4 — Deferred
[ ] WP3.5 population-normalized LISA
[ ] WP3.6 spatial weights sensitivity
[ ] WP3.7 BH-FDR
[ ] Figure 6 June 2019 panel
```

---

## STOP CONDITIONS

- If CC-1 proportional slopes flip the sign of any currently significant Centro finding → halt, reassess
- If CC-2 persistence shows no municipality above 0.25 in the Bajío corridor → the Bajío section needs further rethinking
- If CC-4 reveals additional CED state slopes that are wrong → expand the CED rewrite scope
- If CC-5 produces any pairwise MW p < 0.05 → the non-interchangeability finding has a confound

---

**END OF WP6**
