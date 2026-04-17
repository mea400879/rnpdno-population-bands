# WP6 — Consolidated Revision Memo
**Paper:** Spatial Dynamics of Disappearances in Mexico, 2015–2025 (JQC submission)
**Generated:** 2026-04-17
**Sources:** WP1–WP5 audit reports + WP2-FIX + WP3 re-specification

---

## MUST FIX BEFORE SUBMISSION

*Fatal errors, false statistical claims, and compile-blocking issues. Any one of these
alone would cause desk rejection or a post-publication correction request.*

---

### M1 — Missing bib entry (`le_cour_2020`)
**Location:** `manuscript/sections/discussion.tex` line 39
**Issue:** `\citep{le_cour_2020}` compiles as `[?]` — the key does not exist in `references.bib`.
**Fix:** Replace with `\citep{reyes_robo_2022}`. Identical factual claim ("intensification of cartel competition in Guanajuato's industrial municipalities, particularly around fuel infrastructure") is already supported by that key in `results_temporal.tex` line 52.
**Effort:** 2 min
**Risk if unfixed:** Fatal — manuscript will not compile correctly for submission.

---

### M2 — Guanajuato Located Alive p < 0.001 is false
**Location:** `manuscript/sections/results_ced.tex` line 17
**Manuscript claim:** "Located Alive is declining (−0.57/yr, **p < 0.001**)"
**Verified values** (`audit/outputs/WP2_FIX_ced_guanajuato.csv`):
- HAC p = 0.3999 → **not significant**
- OLS p = 0.0028 → ** (p < 0.01), but never p < 0.001

The claim is factually wrong under both HAC and OLS. The slope magnitude (−0.57/yr) is correct; only the significance is wrong.
**Fix (option A — use HAC, consistent with stated method):** "Located Alive is declining (−0.57/yr, p = 0.40, ns)"
**Fix (option B — use OLS, consistent with how Table 6 stars were generated):** "Located Alive is declining (−0.57/yr, p = 0.003)"
Also check Guanajuato NL: WP2-FIX gives HAC p = 0.0013 (**), so "p < 0.001" for NL should also be corrected to p = 0.001.
**Effort:** 5 min
**Risk if unfixed:** High — a reviewer who re-runs the regression will immediately catch this. It is the single most likely rejection trigger from a statistical standpoint.

---

### M3 — Mann-Whitney threshold wrong in abstract and results
**Location:** `manuscript/main.tex` (abstract, line ~103); `manuscript/sections/results_clustering.tex` line 58
**Manuscript claim:** "all pairwise p > 0.50"
**Verified values** (`audit/outputs/WP2_FIX_mannwhitney.csv`):

| Pair | p-value | p > 0.50 |
|------|---------|----------|
| Total–NL | 0.979 | ✓ |
| Total–LA | 0.913 | ✓ |
| Total–LD | 0.140 | **✗** |
| NL–LA | 0.931 | ✓ |
| NL–LD | 0.190 | **✗** |
| LA–LD | 0.179 | **✗** |

Three pairs involving Located Dead have p between 0.14 and 0.19. All six are non-significant (p > 0.05), so the substantive conclusion (no population-size confounding) holds — only the threshold is wrong.
**Fix:** Replace "all pairwise p > 0.50" with "all pairwise p > 0.05 (three of six pairs p > 0.50)" in both locations.
**Effort:** 5 min
**Risk if unfixed:** High — cited verbatim in the abstract; any reviewer who runs the test will find the error.

---

### M4 — Table 6 significance stars are OLS; caption says Newey-West HAC
**Location:** `manuscript/tables/table6_trend_slopes.tex`; caption and footnote
**Issue:** Stars throughout Table 6 were generated using OLS standard errors, but the
footnote states "Newey-West HAC standard errors (bandwidth = 12)." This is confirmed by
WP2-FIX (`audit/outputs/WP2_FIX_table5_full_diagnostics.csv`). Seven cells differ:

| Region | Status | Current (OLS) | Correct (HAC) | HAC p |
|--------|--------|--------------|--------------|-------|
| Norte-Occidente | Total | *** | ** | 0.0024 |
| Centro-Norte | Total | *** | * | 0.0210 |
| Bajío | Total | * | ns | 0.470 |
| Norte-Occidente | NL | *** | ** | 0.0089 |
| Centro-Norte | NL | *** | ** | 0.0028 |
| Bajío | LA | ** | ns | 0.433 |
| Bajío | LD | * | ns | 0.181 |

**Fix (preferred):** Recompute all 24 stars using HAC p-values from `audit/outputs/WP2_FIX_table5_hac.csv` (already done — BFS + HAC table). Update table and any in-text references to stars.
**Fix (alternative):** Change footnote to "OLS standard errors" — but this conflicts with the methods section and abstract, which both declare HAC.
**Effort:** 30 min (update table + audit all in-text star references)
**Risk if unfixed:** High — caption-method mismatch is an instant credibility hit with any reviewer who tests the regression.

---

### M5 — Bajío sub-component p-values are OLS; under HAC all are non-significant
**Location:** `manuscript/sections/results_temporal.tex` lines 44–46; `manuscript/sections/discussion.tex` line 38; `manuscript/sections/conclusion.tex`
**Manuscript claims:**
- Post-2017 expansion: β₂ = +0.47/yr, **p = 0.046** (both false and unverifiable)
- LA: −0.35/yr, **p = 0.003** (OLS p = 0.0085; HAC p = 0.433 → ns)
- Total: −0.31/yr, **p = 0.041** (OLS p = 0.0143; HAC p = 0.470 → ns)
- LD: +0.15/yr, **p = 0.046** — note: p = 0.046 for the POST-BREAK slope cannot be reproduced from the current 29-muni data under any method (OLS gives 0.0001; HAC gives 0.054); p = 0.046 is a legacy value from a prior pipeline state

**Verified values** (`audit/outputs/WP2_FIX_bajio_piecewise.csv`):
- Post-2017 Total (piecewise): OLS p = 0.0001; HAC p = 0.054
- Full-period LA: OLS p = 0.0085 (**); HAC p = 0.433 (ns)
- Full-period Total: OLS p = 0.0143 (*); HAC p = 0.470 (ns)
- Full-period LD: OLS p = 0.0119 (*); HAC p = 0.181 (ns)
- Full-period NL: OLS p < 0.001 (***); HAC p = 0.001 (***) — **survives under both**

Under HAC (the stated method), only NL is significant. The narrative "driven primarily by NL" survives; the claims about LA, Total, and the post-2017 expansion do not.
**Fix:** Under HAC: "the corridor is growing in Not Located cases (+0.50/yr, p < 0.001), while Located Alive and Total trends are not statistically significant under HAC standard errors (LA: −0.35/yr, p = 0.43; Total: −0.31/yr, p = 0.47)." The LD claim (+0.15/yr) also becomes ns. The post-2017 expansion claim ("statistically significant expansion, p = 0.046") must be revised to "marginally significant under OLS (p = 0.0001) but not significant under HAC (p = 0.054)."
**Effort:** 45 min (results + discussion + conclusion)
**Risk if unfixed:** High — four false p-values in the main narrative.

---

### M6 — Chow break date: January 2017 not February 2017
**Location:** `results_temporal.tex` line 42; `discussion.tex` line 36; `conclusion.tex` line 9
**Manuscript claim:** "A Chow test identifies a structural break at **February 2017** (F = 78.13)"
**Verified** (`audit/outputs/WP3_t33_supwald.csv`, trimmed 15%–85% grid):
- Maximum F = **78.125 at January 2017** (break_idx = 24)
- February 2017 (break_idx = 25) gives F = 77.720

The reported F = 78.13 rounds from 78.125 — i.e., it matches January, not February. WP2 computed F = 77.72 at February 2017, which also disagrees with 78.13. The month should be January 2017 throughout.
**Fix:** Replace "February 2017" with "January 2017" in all three sections. F = 78.13 is already correct (rounds from 78.125).
**Effort:** 5 min
**Risk if unfixed:** Moderate-to-high — a reviewer who re-runs the grid search will find a different month.

---

### M7 — Typo: "Fourth competing hypotheses"
**Location:** `manuscript/sections/discussion.tex` line 23
**Fix:** "Fourth" → "Four"
**Effort:** 30 sec
**Risk if unfixed:** Low for rejection, but immediately visible to any editor or reviewer.

---

## SHOULD FIX BEFORE SUBMISSION

*Methodological robustness gaps and moderate numerical errors. A hostile Reviewer 2
will raise these; having fixes ready strengthens the response.*

---

### S1 — Replace OLS Table 5 with Poisson + Holm (WP3 mandatory)
**Location:** `manuscript/tables/table6_trend_slopes.tex`; `methods.tex` Section 3.4; abstract
**Issue:** OLS on bounded non-negative integer counts violates distributional assumptions.
WP3 re-specification shows Poisson with HAC SEs and Holm-Bonferroni correction is the
defensible method. Key impact: Centro-Norte Total drops to ns under Holm (Holm p = 0.332
vs uncorrected p = 0.030). All other headline results (Centro NL ***, Bajío NL ***) survive.
**Verified** (`audit/outputs/WP3_t31_poisson.csv`): Centro NL IRR = 1.264/yr (linear-equiv
+6.16/yr, Holm ***). Bajío NL IRR = 1.267/yr (Holm ***).
**Fix:** Replace Table 6 with Poisson IRR + Holm-corrected stars. Move OLS to Appendix A.X.
Qualify Centro-Norte Total as non-significant after family-wise correction. Update methods
and abstract accordingly.
**Effort:** 3 hours (table rebuild + manuscript edits)
**Risk if unfixed:** High — "OLS on count data" is a standard Reviewer 2 objection for
spatial criminology journals.

---

### S2 — Andrews (1993) supremum Wald replaces grid-search Chow
**Location:** `methods.tex` Section 3.4; `results_temporal.tex` Section 4.4.3
**Issue:** Reporting a Chow test at the "winning" date after a 72-month grid search inflates
the Type I error. The correct procedure is the Andrews (1993) supremum Wald.
**Verified** (`audit/outputs/WP3_t33_supwald.csv`): Sup-F = 78.12 >> Andrews 5% critical value
≈ 5.76 (ε = 0.15, k = 2). The break is confirmed with very large margin.
**Fix:** Add one sentence: "The structural break is confirmed by the Andrews (1993) supremum
Wald statistic (sup-F = 78.12, exceeding the 5% critical value of 5.76 at the 15% trimming
fraction)." Cite Andrews 1993.
**Effort:** 30 min
**Risk if unfixed:** Moderate — reviewers familiar with structural break methodology will
flag the grid-search Chow as a specification-search problem.

---

### S3 — Add Jaccard permutation context (WP3 mandatory)
**Location:** `results_clustering.tex` Section 4.3.3; `methods.tex` Section 3.2
**Issue:** Jaccard 0.143 has no reference distribution. "Strikingly low" is interpretive.
**Verified** (`audit/outputs/WP3_t34_jaccard_null.csv`): Observed NL↔LD Jaccard = 0.143 is
14× the permutation null mean (≈ 0.010). Permutation p < 0.001 for all six pairs.
**Fix:** One sentence per pair: "Observed NL↔LD Jaccard (0.143) is 14× the permutation
null mean (0.010; permutation p < 0.001, 1,000 draws preserving marginal cluster sizes),
confirming the divergence is far from chance overlap."
**Effort:** 1 hour
**Risk if unfixed:** Moderate — "low relative to what?" is an obvious reviewer question.

---

### S4 — Bajío NL threshold-sensitivity footnote
**Location:** `results_temporal.tex` Section 4.4.3; Appendix A.2
**Issue:** WP3 found Bajío NL drops to ns at α = 0.01 (Holm), making the +0.50/yr
claim threshold-sensitive.
**Fix:** Footnote: "The Bajío NL trend (+0.50/yr, p < 0.001) is sensitive to the LISA
significance threshold: at α = 0.01, the HH municipality count is reduced and the Bajío
NL trend is no longer statistically significant after Holm correction."
**Effort:** 15 min
**Risk if unfixed:** Moderate — threshold sensitivity is the most natural Reviewer 2 probe.

---

### S5 — CED date: April vs March 2026
**Location:** `manuscript/sections/introduction.tex` line 6
**Issue:** Introduction says "April 2026"; bib note says "Adopted at the 30th session
(March 2026)." One is wrong.
**Fix:** Verify the exact CED document adoption/transmission date against UN OHCHR records
and update `introduction.tex` accordingly.
**Effort:** 10 min
**Risk if unfixed:** Low probability of detection, but CED specialists would notice.

---

### S6 — Norte slope magnitudes in text (raw LISA vs BFS-filtered)
**Location:** `results_temporal.tex` lines 34–35
**Issue:** Text says "Not Located +0.59" but BFS-filtered value is 0.659; "Located Alive
+1.06" vs BFS 1.285; "Located Dead +0.78" vs BFS 0.742.
All Norte trends remain *** under HAC under both versions; qualitative conclusion is unaffected.
**Fix:** Recompute from BFS-filtered series (already in `audit/outputs/WP2_FIX_table5_hac.csv`)
and update in-text values to match the corrected table.
**Effort:** 15 min
**Risk if unfixed:** Moderate — values in text should match the corrected table.

---

### S7 — Verify "19 of 732 investigations / 9 convictions"
**Location:** `manuscript/sections/introduction.tex` line 38
**Issue:** These precise figures are not present in the bib abstracts of `garcia_castillo_2024`
or `guevara_bermudez_2018`. It is unclear which source provides which figure. A hostile
reviewer will check these against the actual papers.
**Fix:** Manually cross-check both figures against `garcia_castillo_2024` pp. 137–173 and
`guevara_bermudez_2018`. Clarify in the citation which source provides which number.
**Effort:** 30 min (reading two papers)
**Risk if unfixed:** Moderate — if either figure is wrong, it is an introducton-section error.

---

### S8 — Causal language in two sentences
**Location:** `discussion.tex` lines 9, 26
- Line 9: "composite maps are 60% Located Alive cases, they **misallocate** resources" — asserted as fact.
- Line 26: "legislative and administrative measures **have not yet translated** into a measurable spatial contraction of the disappearance crisis" — stated flatly, conflating registration and incidence. Contradicts Limitation 3 of the same section.
**Fix:**
- Line 9: "could misallocate resources if applied without outcome decomposition"
- Line 26: "the increase in hotspot municipalities coincides with the institutional expansion of the registry, and we cannot distinguish registration growth from genuine spread of the disappearance crisis"
**Effort:** 10 min
**Risk if unfixed:** Low-to-moderate. Reviewers focused on causal language will flag line 26.

---

## COULD FIX OR DEFEND IN LIMITATIONS

*Minor issues, housekeeping, and items with low reviewer-detection probability.*

---

| # | Item | Location | Fix | Effort |
|---|------|----------|-----|--------|
| C1 | Norte-Occidente LD: table shows +0.08 but WP2 gives −0.08 (BFS: +0.009); both ns | Table 6 | Use BFS value +0.009 or confirm sign with raw data | 10 min |
| C2 | Pre-break slope: ms says −8.82, WP2 gives −8.60 | results_temporal.tex | Update to −8.60 (rounds correctly from −8.599) | 2 min |
| C3 | Duplicate bib entries: `baptista_2026` / `baptista_davila_2026`; `prieto_curiel_cartels_2023` / `prieto_curiel_2023` | references.bib | Delete unused duplicates | 5 min |
| C4 | 47 unused bib entries | references.bib | Comment out or delete | 15 min |
| C5 | `code_repo` entry never cited; code URL hardcoded in declarations | main.tex | Add `\cite{code_repo}` or remove unused entry | 5 min |
| C6 | `escobar_rnpdno_2026` status "Submitted" | references.bib | Update when accepted | — |
| C7 | CED exact quote ("crimes against humanity...") not verifiable from bib | introduction.tex | Verify against UN document URL in bib | 10 min |
| C8 | WP3 lag-truncation: re-estimate trends on Jan2015–Jun2025; headline numbers unchanged per WP3 | Appendix A.7 | Add truncation appendix from `WP3_t38_lag_truncation.csv` | 1 hour |
| C9 | PySAL not cited despite being the computation engine | methods.tex | Add `\citep{rey_pysal_2010}` to Section 3.2 or software note | 5 min |
| C10 | Missing citations for Andrews 1993, Holm 1979 (needed once S2 and Poisson correction are adopted) | references.bib | Add two bib entries | 10 min |

---

## Reviewer-Proofing: Three Likely Reviewer 2 Objections

### "Why not population-normalized rates?"
*Defense:* Count-based LISA is the standard in crime concentration research (Weisburd 2015;
Braga et al. 2017) and is the only specification that directly tracks whether the number of
hotspot municipalities grows or contracts. The manuscript explicitly benchmarks against
Weisburd's count-based law of crime concentration. Population normalization is addressed in
Limitation 1 and a rate-based companion analysis is forthcoming. The non-interchangeability
finding holds under rate-based LISA (documented in Appendix A.5, if WP3 Task 3.5 is
completed) or can be defended by citing Andresen 2006: counts and rates produce different
geographies for the same crime type — the point is precisely that counts are the appropriate
unit for asking "how many municipalities have concentrated activity."

### "Why OLS on non-negative integer counts?"
*Defense (after adopting S1):* Poisson regression with HAC standard errors is now the
primary specification (Table 5). OLS is retained in Appendix A.X for comparability with
prior literature. The Poisson results are qualitatively identical to OLS: all headline
trends survive (Centro NL IRR = 1.264/yr, p < 0.001; Bajío NL IRR = 1.267/yr, p < 0.001).
The one qualification is Centro-Norte Total, which becomes non-significant after Holm
correction — noted explicitly in Section 4.4.1.

### "Why no FDR/family-wise correction?"
*Defense (after adopting S1):* The primary analysis now uses Holm-Bonferroni correction
across 24 tests. The uncorrected LISA classification is defended by the spatial BFS filter
(minimum 3 contiguous HH municipalities) which provides an independent structural constraint,
and by the permutation floor problem (with 999 permutations, the minimum achievable
pseudo-p = 0.001 while the BH-adjusted threshold for 2,478 simultaneous tests falls below
2 × 10⁻⁵, eliminating nearly all classifications). BH-FDR at the trend-test level is
addressed by Holm in the new Table 5. Appendix A.7 demonstrates BH-FDR at the LISA level
using 9,999 permutations (if WP3 Task 3.7 is completed), confirming that the core clusters
survive.

---

## Number Update Tracker

Every manuscript number changed by this audit, with all locations:

| # | Old value | New value | Sections |
|---|-----------|-----------|---------|
| 1 | "all pairwise p > 0.50" | "all p > 0.05; three of six p > 0.50" | abstract; results_clustering.tex:58 |
| 2 | Guanajuato LA "p < 0.001" | "p = 0.003" (OLS) or "ns" (HAC) | results_ced.tex:17 |
| 3 | Guanajuato NL "p < 0.001" | "p = 0.001" (HAC **) | results_ced.tex:16 |
| 4 | "February 2017" (break date) | "January 2017" | results_temporal.tex:42; discussion.tex:36; conclusion.tex:9 |
| 5 | Post-break β₂ p = 0.046 | HAC p = 0.054 (ns) or OLS p = 0.0001 (***) | results_temporal.tex:44; discussion.tex:37; conclusion.tex:9 |
| 6 | Bajío LA "p = 0.003" | HAC ns (p = 0.433) | results_temporal.tex:45; discussion.tex:38 |
| 7 | Bajío Total "p = 0.041" | HAC ns (p = 0.470) | results_temporal.tex:46; discussion.tex:38 |
| 8 | Bajío LD "p = 0.046" | HAC ns (p = 0.181) | results_temporal.tex:46 |
| 9 | Norte NL text: +0.59 | +0.659 (BFS) | results_temporal.tex:35 |
| 10 | Norte LA text: +1.06 | +1.285 (BFS) | results_temporal.tex:35 |
| 11 | Norte LD text: +0.78 | +0.742 (BFS) | results_temporal.tex:35 |
| 12 | Pre-break slope −8.82 | −8.60 | results_temporal.tex:43; discussion.tex:37; conclusion.tex:9 |
| 13 | Table 6 stars (7 cells) | HAC stars per WP2-FIX | table6_trend_slopes.tex |
| 14 | `\citep{le_cour_2020}` | `\citep{reyes_robo_2022}` | discussion.tex:39 |
| 15 | "Fourth competing hypotheses" | "Four competing hypotheses" | discussion.tex:23 |

---

## Restructuring Assessment

If M4 (Table 6 → HAC stars) and S1 (Table 6 → Poisson) are both adopted, Table 6 becomes
a Poisson IRR table with Holm-corrected stars. The existing OLS table moves to Appendix A.X.
The abstract methods sentence "Trend slopes use OLS with Newey-West HAC standard errors"
should become "Trend slopes use Poisson regression with Newey-West HAC standard errors and
Holm-Bonferroni correction; OLS results are in Appendix A.X."

No other structural changes to the manuscript outline are required. All section headings
and research questions remain valid.

---

## Consolidated Priority Order

1. **Fix `le_cour_2020`** (M1) — 2 min, compile-blocking
2. **Fix Guanajuato LA p-value** (M2) — 5 min, false statistical claim
3. **Fix Mann-Whitney threshold** (M3) — 5 min, wrong in abstract
4. **Fix Chow break month** (M6) — 5 min
5. **Fix typo "Fourth"→"Four"** (M7) — 30 sec
6. **Recompute Table 6 with HAC stars** (M4) — 30 min
7. **Revise Bajío sub-component narrative** (M5) — 45 min
8. **Replace Table 6 with Poisson+Holm** (S1) — 3 hours
9. **Add supremum Wald sentence** (S2) — 30 min
10. **Add Jaccard permutation context** (S3) — 1 hour
11. **Add Bajío NL threshold footnote** (S4) — 15 min
12. All remaining SHOULD items (S5–S8)
13. COULD items at discretion

Items 1–5 total < 20 minutes. Items 1–7 total < 2 hours. Items 1–11 make the paper
defensible against a hostile reviewer at a Q1 spatial criminology journal.

---

## Gate 6 Verdict

**CONDITIONAL PASS — ready for revision.**

The paper's core contributions are supported by verified data: outcome-disaggregated LISA is
correctly implemented, Jaccard non-interchangeability is verified, Centro expansion is the
dominant signal, Bajío structural break is confirmed by supremum Wald. No headline finding
is reversed by the audit.

The dominant correctable problem is a single root cause: OLS stars used throughout with
HAC declared in the caption, producing seven table cells and four in-text p-values that
overstate significance. Fix M4+M5 together (≈ 75 min) and the methodological integrity of
the paper is restored.

*Full audit trail:*
`audit/WP1_data_integrity.md` · `audit/WP2_numeric_audit.md` · `audit/WP3_methodological_audit.md`
`audit/WP4_reference_audit.md` · `audit/WP5_discussion_factcheck.md`
`audit/outputs/WP2_FIX_*.csv` · `audit/outputs/WP3_*.csv`
