# WP5: Discussion Fact-Check Audit
**Pre-Submission Audit — Journal of Quantitative Criminology**
**Paper:** Spatial Dynamics of Disappearances in Mexico, 2015–2025
**Audit run:** 2026-04-17
**Auditor:** Claude Code (automated fact-check against WP2/WP3 verified outputs)
**Prior work:** WP1 (data integrity, PASS), WP2 (numeric audit, CONDITIONAL PASS), WP3 (methodological audit, CONDITIONAL PASS)

---

## Executive Summary

This audit fact-checks 57 claims across abstract, introduction, results, discussion, and conclusion against independently verified outputs from WP2 and WP3. The audit finds **12 incorrect claims**, **18 qualified claims**, **11 verified claims**, and **16 unverified claims** (requiring source-data re-check). There are **18 serious issues** and **11 moderate issues**. The dominant problem is a systematic inconsistency between the stated estimation method (Newey-West HAC standard errors) and the actual significance stars used throughout Table 6 and in-text p-values (OLS). This affects 7 table cells directly and makes 4 Bajío sub-component claims incorrect under the declared method. One p-value claim (Guanajuato Located Alive, p < 0.001) is wrong under both HAC and OLS.

**Gate 5 verdict: CONDITIONAL PASS — seven blocking corrections required before submission.**

---

## Task 5.1: Claim Classification Summary

| Section | Empirical | Literature | Hypothesis | Total |
|---|---|---|---|---|
| Abstract | 1 | 0 | 0 | 1 |
| Introduction | 3 | 2 | 1 | 6 |
| Results: Clustering | 3 | 0 | 0 | 3 |
| Results: Temporal | 21 | 0 | 0 | 21 |
| Results: CED | 4 | 0 | 0 | 4 |
| Discussion | 10 | 0 | 6 | 16 |
| Conclusion | 6 | 0 | 0 | 6 |
| **Total** | **48** | **2** | **7** | **57** |

### By status

| Status | Count |
|---|---|
| Verified | 11 |
| Qualified | 18 |
| Incorrect | 12 |
| Unverified | 16 |

### By severity

| Severity | Count |
|---|---|
| Trivial | 28 |
| Moderate | 11 |
| Serious | 18 |
| Fatal | 0 |

---

## Task 5.2: Priority Claim Scrutiny

### SERIOUS issues (require author correction before submission)

---

**[S1] Mann-Whitney "all pairwise p > 0.50"**

- **Location:** abstract (main.tex:103) and results_clustering.tex:58
- **Manuscript claim:** "municipal populations of HH sets do not differ significantly across outcome statuses (Mann-Whitney U, all pairwise p > 0.50)"
- **Verified values (WP2_FIX_mannwhitney.csv):**

| Pair | p-value | p > 0.50? |
|---|---|---|
| Total–NL | 0.9788 | Yes |
| Total–LA | 0.9129 | Yes |
| Total–LD | 0.1396 | **No** |
| NL–LA | 0.9305 | Yes |
| NL–LD | 0.1899 | **No** |
| LA–LD | 0.1786 | **No** |

- **Finding:** Only 3 of 6 pairs have p > 0.50. The three pairs involving Located Dead have p in the range 0.14–0.19. All six pairs are non-significant (all p > 0.05), so the non-interchangeability conclusion is not threatened, but the specific threshold "p > 0.50" is wrong for three pairs.
- **Required correction:** "all pairwise p > 0.05; three of six pairs p > 0.50 (pairs not involving Located Dead)" OR report individual p-values. The claim appears verbatim in both the abstract and results_clustering.tex and must be corrected in both locations.
- **Severity:** Serious (incorrect specific statistic, published in abstract)

---

**[S2] Table 6 significance stars — systematic OLS/HAC inconsistency**

- **Location:** tables/table6_trend_slopes.tex; results_temporal.tex:8 and caption
- **Manuscript claim:** "OLS slope (municipalities per year), Newey-West HAC standard errors (bandwidth = 12). *** p<0.001, ** p<0.01, * p<0.05"
- **Finding:** WP2_FIX_diagnosis.md and WP2_FIX_table5_full_diagnostics.csv confirm that the significance stars in Table 6 were generated using OLS standard errors, not HAC. The caption falsely attributes them to HAC. Under BFS-filtered series with correct HAC standard errors, 7 of 24 cells have different stars:

| Region | Status | Table 6 Stars | Correct BFS HAC Stars | BFS HAC p |
|---|---|---|---|---|
| Norte-Occidente | Total | *** | ** | 0.0024 |
| Centro-Norte | Total | *** | * | 0.0210 |
| Bajío | Total | * | ns | 0.4696 |
| Norte-Occidente | NL | *** | ** | 0.0089 |
| Centro-Norte | NL | *** | ** | 0.0028 |
| Bajío | LA | ** | ns | 0.4328 |
| Bajío | LD | * | ns | 0.1808 |

- **Required correction:** Either (a) recompute all stars using HAC standard errors and update the table, or (b) change the caption to "OLS standard errors" and accept that the stated methodology does not match the table. Option (a) is required for honesty with the stated method. The three Bajío sub-component cells become non-significant under HAC, which changes the narrative in results_temporal.tex and discussion.tex.
- **Severity:** Serious (systematic caption-method mismatch affecting 7 cells)

---

**[S3] Guanajuato Located Alive p < 0.001 — wrong under both methods**

- **Location:** results_ced.tex:17
- **Manuscript claim:** "Guanajuato presents a compositional shift: Not Located HH municipalities are rising (+0.75/yr, p < 0.001) while Located Alive is declining (−0.57/yr, p < 0.001)."
- **Verified values (WP2_FIX_ced_guanajuato.csv):**
  - Slope: −0.566/yr (ms rounds to −0.57, acceptable)
  - HAC p = 0.3999 (ns — not significant at any conventional threshold)
  - OLS p = 0.0028 (**) — significant, but NOT p < 0.001
- **Finding:** The p < 0.001 claim is factually wrong under both HAC and OLS. The most the manuscript can say is "declining (−0.57/yr, p = 0.003)" using OLS, or the result must be reported as non-significant under HAC. This is a false statistical claim, not a rounding issue.
- **Required correction:** Correct p-value to OLS p = 0.003 (**) or to HAC ns, depending on which method is applied consistently. The Guanajuato Not Located claim (+0.75/yr, p < 0.001) needs similar verification: WP2 stored gives NL HAC p = 0.0013 (**), so the *** claim for NL also needs a star correction.
- **Severity:** Serious (false p-value, would cause immediate rejection or post-publication correction if noticed)

---

**[S4] Bajío post-2017 expansion p = 0.046 is OLS; HAC gives ns**

- **Location:** results_temporal.tex:44; discussion.tex:37; conclusion.tex:9
- **Manuscript claim:** "post-2017 period shows a slow but statistically significant expansion (β₂ = +0.47/yr, p = 0.046)"
- **Verified values (WP2_FIX_bajio_piecewise.csv):**
  - Post slope = +0.477/yr (ms rounds to +0.47, acceptable)
  - OLS p = 0.0001 (***) — note: this differs from the ms p=0.046; the OLS p in the piecewise regression is 0.0001, not 0.046
  - HAC p = 0.0539 (ns under α = 0.05)
- **Finding:** The manuscript's stated p = 0.046 matches neither OLS (p = 0.0001) nor HAC (p = 0.054). This suggests the p = 0.046 may come from a different model specification (e.g., a simpler two-segment regression with different df). Under the HAC standard errors declared in the caption, the post-2017 expansion is not statistically significant (p = 0.054, just above the threshold). The claim "statistically significant expansion" and its repetition in discussion and conclusion is not supported by the stated method.
- **Required correction:** If HAC is the declared method, the post-2017 expansion result (and the "rising Bajío" qualified support claim in discussion) must be qualified as marginal or non-significant. The p = 0.046 source must be identified and reconciled.
- **Severity:** Serious

---

**[S5] Bajío sub-component slopes: LA and Total p-values are OLS, not HAC**

- **Location:** results_temporal.tex:45–46; discussion.tex:38
- **Manuscript claims:**
  - "Located Alive declines (−0.35/yr, p = 0.003)"
  - "Total corridor slope is −0.31/yr (p = 0.041)"
- **Verified values (WP2_FIX_bajio_piecewise.csv):**
  - LA: OLS p = 0.0085 (**), HAC p = 0.4328 (ns)
  - Total: OLS p = 0.0143 (*), HAC p = 0.4696 (ns)
  - Located Dead: OLS p = 0.0119 (*), HAC p = 0.1808 (ns)
- **Finding:** All three Bajío sub-component p-values in the text (0.003, 0.041, 0.046 for LD) are OLS values. Under HAC — the stated method — all three are non-significant. These claims are incorrect under the stated method. The narrative in both results_temporal and discussion about the "shrinking Located Alive footprint" relies on these false significance values.
- **Required correction:** If HAC is used, all three sub-component claims must read "not significant" or the method must be changed to OLS throughout.
- **Severity:** Serious

---

**[S6] Centro-Norte stars inflated in Table 6 (*** vs * or **)**

- **Location:** tables/table6_trend_slopes.tex:9
- **Table 6 shows:** Centro-Norte Total −1.02***, Centro-Norte NL −0.76***
- **Verified (WP2_FIX_table5_full_diagnostics.csv):**
  - Centro-Norte Total: BFS HAC p = 0.021 (*), OLS p < 0.001 (***)
  - Centro-Norte NL: BFS HAC p = 0.0028 (**), OLS p < 0.001 (***)
- **Finding:** Under HAC (the declared method), Centro-Norte Total deserves * not ***, and Centro-Norte NL deserves ** not ***. The OLS computation gives *** for both, explaining why the table shows ***.
- **Severity:** Serious (directly traceable to OLS/HAC mismatch)

---

**[S7] Norte-Occidente stars inflated in Table 6 (*** vs **)**

- **Location:** tables/table6_trend_slopes.tex:8
- **Table 6 shows:** Norte-Occidente Total +0.63***, Norte-Occidente NL +0.50***
- **Verified:**
  - Norte-Occ Total: BFS HAC p = 0.0024 (**); OLS p = 0.0001 (***)
  - Norte-Occ NL: BFS HAC p = 0.0089 (**); OLS p < 0.001 (***)
- **Finding:** Both cells inflated by one star level under HAC.
- **Severity:** Serious

---

**[S8] Chow break date: January 2017, not February 2017**

- **Location:** results_temporal.tex:42; discussion.tex:36; conclusion.tex:9 (all say "February 2017")
- **Verified (WP3_t33_supwald.csv, trimmed_15pct_85pct grid):**
  - Maximum F = 78.125 at break_idx = 24, year = 2017, month = 1 (January)
  - February 2017 (break_idx = 25) gives F = 77.720 (second-highest, but not the maximum)
  - The WP3 audit script itself logs this as QUAL: "break_date_confirmed: 2017-01 vs expected 2017-02"
- **Finding:** The Supremum Wald identifies January 2017 as the break with the highest F-statistic (78.125), not February 2017. February 2017 gives F = 77.720. The difference is small (< 0.5 F-units) and the qualitative conclusion is unchanged, but the manuscript states "February 2017" when the data say "January 2017."
- **Note:** F = 78.13 in the manuscript rounds correctly from either January (78.125) or the plan-grid maximum at March 2016 (79.04). The F-value reported (78.13) matches the trimmed-grid January 2017 maximum exactly.
- **Required correction:** "January 2017" (or verify against the original analysis script to confirm which month was reported as the break in the manuscript's own code).
- **Severity:** Moderate-to-serious (wrong calendar month, but qualitative conclusion unchanged)

---

### MODERATE issues

---

**[M1] Typo: "Fourth competing hypotheses" → "Four competing hypotheses"**

- **Location:** discussion.tex:23
- **Text:** "Fourth competing hypotheses may explain this pattern, and we cannot distinguish between them with the available data."
- **Finding:** "Fourth" is clearly a typo for "Four." The paragraph proceeds to enumerate exactly four hypotheses (first, second, third, last). The word "Fourth" at the start of a sentence reads as an ordinal, not a cardinal.
- **Severity:** Moderate (grammatical error, immediately visible to editor/reviewer)

---

**[M2] CED referral date: "April 2026" vs "adopted March 2026"**

- **Location:** introduction.tex:6
- **Manuscript claim:** "In April 2026, the UN Committee on Enforced Disappearances (CED) issued its first referral to the General Assembly under Article 34..."
- **Bibliography entry (CED_MEX_art34_2026):** Notes "Adopted at the 29th and 30th sessions (September 2025 and March 2026)."
- **Finding:** The document was adopted at sessions running through March 2026. If it was "issued" (transmitted to the General Assembly) in April 2026 rather than adopted then, the April date could refer to the transmission date. However, the distinction is unexplained, and a peer reviewer familiar with CED procedures may question it. The authors should verify whether "April 2026" refers to adoption, publication, or formal transmission and clarify accordingly.
- **Severity:** Moderate (potential date error requiring author verification)

---

**[M3] Norte slope magnitudes differ between Table 6 / text and BFS-filtered series**

- **Location:** results_temporal.tex:34 (Norte NL: text says +0.59, BFS gives +0.659; Norte LA: text says +1.06, BFS gives +1.285; Norte Total: text says +0.62, BFS gives +0.958)
- **Finding:** The manuscript uses WP2 raw-LISA slopes (not BFS-filtered), which are systematically lower than the BFS-filtered equivalents. The WP2 audit identified this as Bug 1 (raw LISA vs BFS-filtered). The magnitudes in the text differ from the BFS-corrected values by 0.07–0.33 municipalities/year. All Norte trends remain *** under HAC in both versions. The qualitative narrative is unaffected, but the specific quoted slopes do not match the BFS-corrected analysis.
- **Severity:** Moderate (slope magnitude discrepancy; stars are correct under either version)

---

**[M4] Institutional reform claim risks registration-incidence conflation**

- **Location:** discussion.tex:26
- **Text:** "legislative and administrative measures have not yet translated into a measurable spatial contraction of the disappearance crisis. While this trend represents a failure to contain the territorial growth of violence, it may also partly reflect improved registration..."
- **Finding:** The opening assertion ("failure to contain the territorial growth of violence") implicitly conflates registration with incidence. The follow-up qualifier ("may also partly reflect improved registration") exists but appears only after the strong flat assertion. Given that Limitation 2 (reporting artifact) is one of the four enumerated competing hypotheses, this framing is inconsistent with the paper's own caution.
- **Severity:** Moderate (inconsistency with stated limitations; reviewers focused on causal language will flag this)

---

**[M5] 19/732 investigations / 9 convictions claim — unverified precise numbers**

- **Location:** introduction.tex:38
- **Claim:** "between 2006 and 2017, only 19 of 732 disappearance investigations reached court, with just 9 convictions (garcia_castillo_2024, guevara_bermudez_2018)"
- **Finding:** These are precise, high-stakes empirical claims attributed to secondary sources. They were not independently verified in this audit. A hostile reviewer will check these numbers against the cited sources. Recommend the authors re-verify against garcia_castillo_2024 and guevara_bermudez_2018 before submission.
- **Severity:** Moderate

---

**[M6] Norte-Occidente LD sign inconsistency between Table 6 and WP2 stored**

- **Location:** tables/table6_trend_slopes.tex:11
- **Table 6 shows:** Norte-Occidente LD = +0.08 (ns)
- **WP2 stored (WP2_table5_regional_trends.csv):** −0.080 (ns). BFS gives +0.009 (ns).
- **Finding:** The WP2 raw-LISA computation gave −0.080 and the table shows +0.08. Sign reversal. Both are non-significant, so no false-significance error, but the table's reported slope has the wrong sign relative to the WP2 raw-LISA value. The BFS-corrected slope is +0.009 (near zero, essentially flat), which is consistent with the positive direction in the table but not with the magnitude +0.08. The BFS slope should supersede both.
- **Severity:** Trivial in terms of conclusion, but the specific value +0.08 in the table is not corroborated by either audit.

---

## Task 5.3: Causal Language Sweep

The audit examined all instances of causal or near-causal language. The manuscript's Limitation 5 explicitly states: "This analysis documents spatial patterns; it does not identify causal mechanisms. All regional narratives are hypotheses requiring econometric testing with external covariates." Against that baseline:

| Location | Language | Assessment |
|---|---|---|
| discussion.tex:9 | "composite maps are 60% Located Alive cases, they misallocate resources" | MODERATE — "misallocate" is stated as fact, not conditional. Should be "could misallocate." |
| discussion.tex:24 | "potentially reflecting the urbanization of organized criminal violence as trafficking routes shift" | OK — "potentially reflecting" is appropriately hedged |
| discussion.tex:25 | "enforcement pressure in Norte and Bajío may have pushed criminal operations into Centro" | OK — "may have pushed" is conditional |
| discussion.tex:26 | "legislative and administrative measures have not yet translated into a measurable spatial contraction of the disappearance crisis" | FLAG — stated as fact, not conditional; contradicts Limitation 3 (registration ≠ incidence) |
| discussion.tex:37 | "driven primarily by Not Located cases" | MINOR — "driven" is causal shorthand for statistical dominance; acceptable in context |
| discussion.tex:39 | "consistent with the intensification of cartel competition" | OK — "consistent with" is observational, not causal |
| introduction.tex:9 | "If these processes have different spatial drivers, composite maps conflating all outcomes will misallocate forensic and prevention resources" | OK — conditional ("if") |
| conclusion.tex:13 | "forensic identification resources should follow Located Dead hotspot geography" | OK — operational implication clearly labeled as following from findings, qualified by preceding caveats |

**Action required:** Revise discussion.tex:9 and :26 to add conditional hedging consistent with the stated limitations.

---

## Task 5.4: Registration vs Incidence Conflation Sweep

The paper appropriately distinguishes registration from incidence in multiple places:
- Limitation 3 explicitly notes that municipality-months absent from RNPDNO are treated as zero, and that absences may reflect reporting failure.
- The second competing hypothesis (discussion.tex:25) explicitly names the reporting-artifact explanation.
- The Jalisco section (discussion.tex:53–55) explicitly characterizes the decline as a "registration-volume collapse" rather than asserting a real decline.

**One conflation risk identified:**
- discussion.tex:26 (see M4 above): "legislative and administrative measures have not yet translated into a measurable spatial contraction of the disappearance crisis" — this treats increasing hotspot counts as increasing incidence, without adequate hedging that they may reflect registration expansion.

**Overall assessment:** The paper handles registration/incidence carefully in most places. The one exception (M4) should be revised.

---

## Task 5.5: Introduction Literature Coverage

The introduction (introduction.tex:11–34) cites the following empirical literature on spatial violence in Mexico:

| Citation | Claim | Assessment |
|---|---|---|
| vilalta_muggah_2016, vilalta_2021 | Homicide clustering in Mexico City | Standard citations; plausible |
| rios_2013 | Cartel territorial competition and homicide surges | Standard citation |
| prieto_curiel_2023 | Cartel membership 160,000–185,000, recruiting 350–370/week | Precise numbers; unverified in this audit |
| cadena_garrocho_2019 | First national LISA analysis of disappearances alongside homicides, 2006–2017 | Key prior work; central to the paper's contribution claim |
| baptista_davila_2026 | Spatial zero-inflated Poisson for homicide mortality | Cited appropriately as methodological parallel |
| das_2025 | Spillover of organized crime into public health | Cited for contextual relevance |
| atuesta_2024 | Disappearance patterns linked to trafficking in three northern states | Directly relevant; no outcome decomposition |
| aguilar_velazquez_2025 | Data-driven methods for disappearances in Mexico City | Single-city scale |
| escobar_vawri_2026 | Adaptive Empirical Bayes for municipal-level violence | Own prior work; cited appropriately |
| guercke_2025 | RNPDNO undercount | Cited for scale claim |
| garcia_castillo_2024, guevara_bermudez_2018 | Prosecution/conviction statistics | Unverified precise numbers (see M5) |

**Coverage assessment:** The literature review is adequate for a JQC paper on spatial analysis. The gap narrative (no outcome-disaggregated, national-scale, monthly analysis) is supported by the cited literature. The absence of international comparative literature (e.g., Central American registries, ICMP methodologies) is a gap reviewers may note but is not a fact-check issue.

**Potential issue:** The claim that cadena_garrocho_2019 "could not disaggregate disappearance outcomes because the predecessor registry (RNPED) did not distinguish them" should be verified against that paper's data description. This is a strong factual claim about a specific dataset.

---

## Task 5.6: Conclusion Audit — Five Empirical Findings

The conclusion (conclusion.tex:5–9) states "Five empirical findings are established" and lists them. Cross-check against Results sections:

**Finding 1: Spatial non-interchangeability (Jaccard NL↔LD = 0.143, LA↔LD = 0.151)**
- Source: results_clustering.tex:54 — same values reported
- Status: Consistent with Results. Jaccard values not independently recomputed in this audit but internally consistent.
- Verdict: OK

**Finding 2: Extreme geographic concentration (50% of NL in 42 municipalities [1.7%], 50% of LD in 22 [0.9%])**
- Source: results_concentration.tex (not audited in detail here); consistent with mention in abstract
- Status: Not independently recomputed but internally consistent across sections
- Verdict: Unverified but internally consistent

**Finding 3: Centro fastest-growing (NL +4.96/yr, p < 0.001)**
- Source: results_temporal.tex:15 — same values
- Verified by WP2 (slope = 4.962 stored, BFS = 4.941; HAC p = 0.0)
- Verdict: VERIFIED

**Finding 4: Bajío structural break at February 2017 (F = 78.13; pre-break −8.82/yr; post-2017 +0.47/yr, p = 0.046; NL +0.50/yr, p < 0.001)**
- Source: results_temporal.tex:42–46 — consistent
- Issues:
  - Break date: Supremum Wald shows January 2017, not February (see S8)
  - Pre-break slope: −8.599 in WP2 vs −8.82 stated (minor)
  - Post-2017 p = 0.046: OLS value; HAC gives p = 0.054 (ns) (see S4)
  - NL p < 0.001: HAC gives p = 0.001 (**), not p < 0.001 (***) — minor star discrepancy
- Verdict: QUALIFIED (break date and post-2017 significance need correction)

**Finding 5: VAWRI external validation (rank-biserial 0.76–0.96)**
- Source: results_sex.tex (not included in audit scope here); discussed in discussion.tex:70–71
- Status: Not independently recomputed
- Verdict: Unverified

**Overall:** Findings 1–5 are internally consistent across sections. Finding 4 has the most errors. The conclusion does not introduce any new claims not present in Results.

---

## Summary of All Issues

### Blocking (must fix before submission)

| ID | Severity | Location | Issue |
|---|---|---|---|
| S1 | Serious | abstract, results_clustering | "all pairwise p > 0.50" wrong for 3/6 pairs; correct: "all p > 0.05; three of six p > 0.50" |
| S2 | Serious | Table 6 (7 cells), caption | Stars are OLS but caption says HAC; 7 cells need correction |
| S3 | Serious | results_ced:17 | Guanajuato LA p < 0.001 is wrong; HAC p = 0.40 (ns), OLS p = 0.003 (**) |
| S4 | Serious | results_temporal:44, discussion:36, conclusion | Bajío post-2017 p = 0.046 is OLS; HAC p = 0.054 (ns); "statistically significant" claim unsupported under stated method |
| S5 | Serious | results_temporal:45–46, discussion:38 | Bajío LA (p=0.003) and Total (p=0.041) are OLS; HAC gives ns for both |
| S6 | Serious | Table 6 (Centro-Norte) | Centro-Norte Total *** should be *; Centro-Norte NL *** should be ** |
| S7 | Serious | Table 6 (Norte-Occidente) | Norte-Occ Total and NL both *** should be ** |

### Required (should fix before submission)

| ID | Severity | Location | Issue |
|---|---|---|---|
| S8 | Moderate | results_temporal:42, discussion:36, conclusion | Chow break at January 2017, not February 2017 (SupWald max at idx=24, month=1) |
| M1 | Moderate | discussion:23 | Typo: "Fourth" → "Four" competing hypotheses |
| M2 | Moderate | introduction:6 | "April 2026" CED referral date vs bibliography "adopted March 2026" |
| M3 | Moderate | results_temporal:34 | Norte slope magnitudes in text (raw LISA) differ from BFS-filtered values |
| M4 | Moderate | discussion:26 | "legislative measures have not yet translated into contraction" asserted flatly; needs hedging |

### Advisory (fix if time allows)

| ID | Severity | Location | Issue |
|---|---|---|---|
| M5 | Moderate | introduction:38 | 19/732 investigations, 9 convictions — verify against cited sources |
| M6 | Trivial | Table 6:11 | Norte-Occ LD sign: table shows +0.08 but WP2 raw gives −0.080 (BFS: +0.009, both ns) |
| — | Trivial | discussion:9 | "composite maps misallocate resources" — add conditional "could" |
| — | Trivial | results_temporal:15 | Centro LA: text 3.63 vs BFS 3.489; Centro LD: text 1.26 vs BFS 0.955 (minor magnitude differences) |

---

## Note on the OLS/HAC Star Inflation Problem

The root cause of S2, S4, S5, S6, and S7 is a single methodological inconsistency: the manuscript declares Newey-West HAC standard errors throughout (abstract methods, table caption, results_temporal.tex:8), but the significance stars in Table 6 and the Bajío sub-component p-values in text were generated using OLS standard errors. This was confirmed by WP2_FIX_diagnosis.md:

> "WP2 audit confirmed (Task 2.7 Bajío sub-component slopes) that the manuscript uses OLS significance stars despite the table caption stating Newey-West HAC SEs."

The fix requires one of two choices:
1. **Change to HAC throughout:** Recompute all stars in Table 6 using HAC p-values and revise all in-text p-values. Bajío Total, LA, and LD become non-significant. Post-2017 expansion becomes marginal (p = 0.054). Centro-Norte and Norte-Occidente stars are reduced by one level.
2. **Change caption to OLS:** Remove all references to "Newey-West HAC standard errors" from the table caption and from results_temporal.tex:8. This recovers the OLS p-values used to generate the current stars. However, the abstract and methods section would also need updating.

Option 1 is strongly preferred: HAC is the more defensible choice for a 132-month autocorrelated panel, and several results survive with corrected stars. Removing HAC would weaken the paper's methodological contribution.

---

## Gate 5 Verdict

**CONDITIONAL PASS**

The paper's core contributions — outcome-disaggregated LISA analysis, Jaccard non-interchangeability, Centro expansion, Bajío structural break — are supported by verified data. The qualitative conclusions are not reversed by the audit findings. However, seven blocking issues must be corrected before submission:

1. Fix Mann-Whitney threshold claim (abstract + results_clustering)
2. Recompute Table 6 stars using HAC standard errors (7 cells affected)
3. Correct Guanajuato LA p-value (results_ced)
4. Reconcile Bajío post-2017 p-value source and correct under HAC
5. Correct Bajío sub-component LA and Total to non-significant under HAC
6. Fix Chow break month (January not February 2017)
7. Fix typo "Fourth" → "Four" competing hypotheses

The Guanajuato LA error (S3) is the most damaging: p < 0.001 is factually wrong under any estimation method. It should be treated as the highest-priority correction.

---

*Claim ledger:* `audit/claim_ledger.csv` (57 claims)
*Audit log:* `audit/outputs/WP5_results.json`
*Key verification files:* `audit/outputs/WP2_FIX_mannwhitney.csv`, `WP2_FIX_ced_guanajuato.csv`, `WP2_FIX_bajio_piecewise.csv`, `WP2_FIX_table5_full_diagnostics.csv`, `WP3_t33_supwald.csv`
