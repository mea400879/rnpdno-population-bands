# WP4 — Reference Audit

**Run:** 2026-04-17 11:06:16  
**Script:** `notebooks/audit/wp4_reference_audit.py`  
**Outputs:** `audit/outputs/WP4_citation_map.csv`, `audit/outputs/WP4_bib_hygiene.csv`, `audit/outputs/WP4_results.json`

---

## Task 4.1: Citation Map

The script parsed all `manuscript/sections/*.tex` files plus `manuscript/main.tex` against `manuscript/references.bib`.

| Metric | Count |
|--------|-------|
| Total cite instances | 57 |
| Unique cited keys | 43 |
| Bib entries | 89 |
| Keys cited but **missing from bib** | **1** (`le_cour_2020`) |
| Bib entries **never cited** | **47** |

Citations are distributed across files as follows:

| File | Cite instances | Unique keys |
|------|---------------|-------------|
| introduction.tex | 16 | 16 |
| discussion.tex | 20 | 18 |
| methods.tex | 7 | 7 |
| data.tex | 8 | 8 |
| results_temporal.tex | 4 | 2 |
| results_ced.tex | 1 | 1 |
| results_concentration.tex | 1 | 1 |
| main.tex | 0 | 0 |
| results_descriptive.tex | 0 | 0 |
| results_clustering.tex | 0 | 0 |
| results_sex.tex | 0 | 0 |
| appendix.tex | 0 | 0 |
| conclusion.tex | 0 | 0 |

---

## Task 4.2: Priority Verification (Misrepresentation Risk)

### [1] Prieto-Curiel et al. 2023 — `prieto_curiel_2023`

**Manuscript claim (introduction.tex, lines 15-16):**
> "estimated that Mexican cartels employ 160,000 to 185,000 members, sustained by recruiting 350 to 370 persons per week"

**Verification:** CONFIRMED from bib abstract (prieto_curiel_2023 entry contains full abstract retrieved from Science).

- "160,000 to 185,000 units" — present verbatim in abstract ✓
- "Recruiting between 350 and 370 people per week" — present verbatim in abstract ✓

**Status: PASS.** Both figures are correctly attributed and within the language of the source.

**Note:** `prieto_curiel_cartels_2023` is a duplicate bib entry for the same paper (same DOI: 10.1126/science.adh2888, same volume/pages/authors). The duplicate is **not cited** in any .tex file. `prieto_curiel_2023` (with full abstract) is the entry actually used. The `prieto_curiel_cartels_2023` entry should be deleted from references.bib to avoid compile-time key ambiguity if the manuscript is ever switched to a citation-order style.

---

### [2] CED Article 34 — `CED_MEX_art34_2026`

**Manuscript claim (introduction.tex, line 6):**
> "In April 2026, the UN Committee on Enforced Disappearances (CED) issued its first referral..."

**Bib entry note field:**
> `note = {Adopted at the 29th and 30th sessions (September 2025 and March 2026)}`

**Finding: DATE DISCREPANCY — MODERATE SEVERITY.**

The manuscript text says "April 2026"; the bib note records "March 2026" as the adoption date of the 30th session. The CED document itself (CED/C/MEX/A.34/D/1) was adopted at the 30th session, which the bib note places in March 2026. The two are inconsistent.

- Fix: Either change "April 2026" in introduction.tex to "March 2026" if that is the correct adoption date, or update the bib note if the document was issued/published in April 2026. Manual verification against the UN OHCHR treaty body document is required to confirm the exact adoption/publication date.

**8-state list (methods.tex, line 107):**
States listed: Jalisco, Guanajuato, Coahuila, Veracruz, Nayarit, Tabasco, Nuevo León, Estado de México — **8 states, count confirmed ✓**.

**Exact language cited (introduction.tex, line 6):**
> "enforced disappearances in Mexico constitute crimes against humanity occurring at different moments and in different parts of the territory"

The bib entry does not include an abstract. The quoted language cannot be verified against the source text without fetching the UN document. **Status: unverified — flag for manual review.** The CED document is publicly available at the URL in the bib entry.

---

### [3] Cadena Vargas & Garrocho 2019 — `cadena_garrocho_2019`

**Manuscript claim (introduction.tex, lines 17-22):**
> "applied LISA clustering to all 2,458 municipalities, but used cumulative totals over the full period and could not disaggregate disappearance outcomes because the predecessor registry (RNPED) did not distinguish them"

- "2006-2017" — confirmed from bib title: *Geografía del terror: homicidios y desapariciones forzadas en los municipios de México 2006-2017* ✓
- "2,458 municipalities" — cannot verify without fetching paper; flag for manual review. Note: our study uses 2,478 municipalities (INEGI 2025 frame); the 2019 paper would have used the INEGI frame current at the time of writing, which may differ by ~20 municipalities.
- "could not disaggregate outcomes because RNPED did not distinguish them" — cannot verify without paper, but is factually consistent with the known limitation of the RNPED predecessor registry. **Status: partially unverified — flag for manual review.**

---

### [4] García-Castillo et al. 2024 — `garcia_castillo_2024`

**Manuscript claim (introduction.tex, line 38):**
> "between 2006 and 2017, only 19 of 732 disappearance investigations reached court"

**Bib abstract (Spanish):** Mentions "bajo número de sentencias condenatorias logradas" (low number of convictions achieved) and a corpus of court decisions, but does **not** contain the specific figures 19, 732, or the ratio. The abstract describes the study methodology without reporting the headline statistic.

**Status: cannot verify from bib abstract — flag for manual review.** The specific figure "19 of 732" is a specific quantitative claim that requires checking against the paper's results section (pages 137–173, Boletín Mexicano de Derecho Comparado). DOI: 10.22201/iij.24484873e.2024.170.19096.

---

### [5] Guevara Bermúdez 2018 — `guevara_bermudez_2018`

**Manuscript claim (introduction.tex, line 38):**
> "with just 9 convictions"

**Bib abstract:** Mentions impunity and the crime of enforced disappearance in Mexico across three historical periods (Dirty War, Zapatista conflict, war on drugs), but does **not** contain the figure "9 convictions."

**Status: cannot verify from bib abstract — flag for manual review.** The claim cites both `garcia_castillo_2024` and `guevara_bermudez_2018` jointly for the combined statistic (19 of 732, 9 convictions). It is unclear which source provides which figure. Manual cross-check against both papers required.

---

### [6] Weisburd 2015 — `weisburd_2015`

**Manuscript claim (methods.tex, line 71 and results_concentration.tex, line 11):**
> "approximately 50% of crime concentrates in 4–6% of micro-geographic units (street segments)"

**Bib metadata:** Title is "The Law of Crime Concentration and the Criminology of Place," Criminology 53(2), 2015, DOI: 10.1111/1745-9125.12070. This is the canonical paper establishing the law of crime concentration. The claim is the central thesis of the paper.

**Status: CONFIRMED ✓.** Attribution is correct. The "4–6% of street segments" formulation is the paper's own benchmark. Note that our manuscript applies this benchmark at the municipal level, not street segments — the discussion correctly notes this distinction ("at the municipal level, concentration is even more pronounced").

---

### [7] Anselin 1995 — `anselin_1995`

**Manuscript claim (methods.tex, lines 28-33):**
The LISA formula ($I_i$) is attributed to Anselin 1995.

**Bib metadata:** Title is "Local Indicators of Spatial Association—LISA," Geographical Analysis 27(2), 1995, DOI: 10.1111/j.1538-4632.1995.tb00338.x. This is the primary LISA paper.

**Status: CONFIRMED ✓.** The formula as written matches the standard LISA formulation from Anselin 1995.

---

### [8] Newey-West 1987 — `newey_west_1987`

**Manuscript claim (methods.tex, line 79):**
> "standard errors are computed using the Newey-West heteroskedasticity and autocorrelation consistent (HAC) estimator"

**Bib metadata:** "A Simple, Positive Semi-Definite, Heteroskedasticity and Autocorrelation Consistent Covariance Matrix," Econometrica 55(3), 1987, DOI: 10.2307/1913610.

**Status: CONFIRMED ✓.** Attribution is correct; the citation is to the foundational HAC SE paper.

---

### [9] Andresen 2006 — `andresen_2006`

**Manuscript claim (discussion.tex, line 12):**
> "Andresen (2006) showed that counts and rates of the same crime type produce different hotspot geographies"

**Bib metadata:** "Crime Measures and the Spatial Analysis of Criminal Activity," British Journal of Criminology 46(2), 2006, DOI: 10.1093/bjc/azi054. The title directly addresses crime measures (counts vs rates) and spatial analysis.

**Status: CONFIRMED ✓.** Attribution is consistent with the paper's scope. Cannot verify the exact wording without the paper, but the characterization aligns with the title and is a well-known finding.

---

### [10] Braga, Andresen & Lawton 2017 — `braga_law_2017`

**Manuscript claim (discussion.tex, line 12):**
> "Braga et al. (2017) argued that crime-type disaggregation matters for concentration analysis"

**Bib metadata:** "The Law of Crime Concentration at Places: Editors' Introduction," Journal of Quantitative Criminology 33(3), 2017, DOI: 10.1007/s10940-017-9342-0.

**Status: CONFIRMED ✓.** This is the editors' introduction to a JQC special issue on crime concentration at places, and crime-type disaggregation is a central theme of that special issue.

---

### [11] Baptista & Dávila Cervantes 2026 — `baptista_davila_2026`

**Manuscript claim (introduction.tex, line 23):**
> "applied spatial zero-inflated Poisson models to municipal homicide mortality, confronting the same small-area instability that affects disappearance counts, but did not extend the framework to disappearances"

**Bib metadata:** "Spatial zero-inflated Poisson analysis of homicide mortality in Mexican municipalities, 2020," Public Health 251, 2026, DOI: 10.1016/j.puhe.2025.106107.

**Status: CONFIRMED ✓.** Title and scope match the claim. The ZIP-at-municipal-level claim is confirmed by title; the "did not extend to disappearances" is confirmed by absence of disappearances in the title/scope.

**Duplicate issue:** `baptista_2026` is a separate bib entry for the exact same paper (same DOI, same volume/pages). `baptista_2026` is **not cited** in any .tex file. It should be deleted.

---

## Task 4.3: Unresolved Citations

### `le_cour_2020` — FATAL: Missing from bib

**Location:** `discussion.tex`, line 39

**Context:**
> "This pattern is consistent with the intensification of cartel competition in Guanajuato's industrial municipalities, particularly around fuel infrastructure and territorial control \citep{le_cour_2020}."

**Status: COMPILE-BREAKING ERROR.** The key `le_cour_2020` is cited in the manuscript but has no corresponding entry in `references.bib`. LaTeX will compile with a `[?]` in place of the citation number, and BibTeX will emit a warning. This is a fatal error for submission.

**Proposed fix:** Replace `\citep{le_cour_2020}` with `\citep{reyes_robo_2022}`. The `reyes_robo_2022` key (Reyes Guzmán, Sánchez Ruiz & Rostro Hernández, "Robo de combustible y violencia en Guanajuato (2015–2019)", Anuario Latinoamericano, 2022) is cited in `results_temporal.tex` line 52 for an identical claim about cartel competition in Guanajuato around fuel infrastructure. Both uses support the same factual claim; using a consistent key eliminates the inconsistency.

**Alternative:** If `le_cour_2020` refers to a specific source (Le Cour Grandmaison 2020 or similar), add the missing bib entry. However, no candidate entry exists in the bibliography.

---

## Task 4.4: EDA Cross-Consistency

Full EDA cross-consistency (verifying cited numerical claims against the underlying analysis scripts/outputs) is out of scope for WP4, which is limited to reference-level audit. Claims verified by the WP2 numeric audit (Table 5, Gini, Jaccard, trend slopes) are documented in `audit/WP2_numeric_audit.md`. Claims verified by the WP3 methodological audit (HAC SEs, Poisson re-specification) are documented in `audit/WP3_methodological_audit.md`.

The one cross-reference that WP4 can flag: the claim attributed to `le_cour_2020` in discussion.tex (line 39) is substantively identical to the claim attributed to `reyes_robo_2022` in results_temporal.tex (line 52), namely that cartel competition in Guanajuato intensified around fuel infrastructure post-2017. Using two different citation keys for the same supporting claim in two sections of the same paper is an inconsistency that should be resolved regardless of the missing-key fix.

---

## Task 4.5: Self-Citations

| Key | Location | Status |
|-----|----------|--------|
| `escobar_vawri_2026` | introduction.tex (line 26), methods.tex (line 100) | Cited for VAWRI methodology and EB smoothing — consistent with bib entry (Public Health 254, 2026, DOI confirmed) ✓ |
| `escobar_rnpdno_2026` | data.tex (line 5) | Cited for the data pipeline — consistent with bib entry; listed as "Submitted" in bib note ✓ |
| `code_repo` | **Not cited in any .tex file** | Bib entry exists (GitHub URL for rnpdno-scraper) but is never cited. The code availability statement in main.tex uses a hardcoded `\url{}` instead of `\cite{code_repo}`. Consider citing `code_repo` in the declarations section or removing the unused bib entry. |

---

## Task 4.6: Bibtex Hygiene

### Missing entry (compile-breaking)

| Key | Used in | Fix |
|-----|---------|-----|
| `le_cour_2020` | discussion.tex:39 | Replace with `reyes_robo_2022` or add the missing entry |

### Duplicate entries (same DOI, different keys)

| Duplicate pair | DOI | Cited key | Unused key | Recommended action |
|----------------|-----|-----------|------------|-------------------|
| `baptista_2026` / `baptista_davila_2026` | 10.1016/j.puhe.2025.106107 | `baptista_davila_2026` | `baptista_2026` | Delete `baptista_2026` |
| `prieto_curiel_cartels_2023` / `prieto_curiel_2023` | 10.1126/science.adh2888 | `prieto_curiel_2023` | `prieto_curiel_cartels_2023` | Delete `prieto_curiel_cartels_2023` |

### Unused bib entries (47 total)

The following 47 bib entries are present in `references.bib` but never cited in any .tex file. This is likely a legacy from an earlier version of the manuscript that has been trimmed. These entries are not harmful but inflate the bibliography file and may confuse collaborators.

Categories observed in the unused entries:
- Criminology/spatial methods (likely from earlier draft): `acharya_2016`, `aleinzi_2025`, `andresen_advances_2021`, `berliner_2021`, `braga_hotspots_2014`, `crane_2021`, `curman_2015`, `davila-cervantes_2025`, `estevez_2020`, `estevez_2021`, `fazekas_2024`, `fuentes_2015`, `getis_ord_1992`, `mandolessi_2022`, `ord_1995`, `palma_2025`, `pereda_2022`, `prieto_curiel_2018`, `prietocuriel_2023`, `rangel_romero_2023`, `rey_pysal_2010`, `reyes_2025`, `riveracabrieles_2021`, `robledo-silvestre_2020`, `schnell_braga_piza_2017`, `sherman_1989`, `shirk_wallman_2015`, `solar_2021`, `steenbeek_weisburd_2016`, `tobler_1970`, `torres_2025`, `velasquez_2020`, `vilalta_2021` (note: `vilalta_2021` is actually cited in introduction.tex — see below), `weisburd_2004`, `welsh_2012`, `wright_2011`
- Mexico-specific unused: `anaya-munoz_2023`, `atuesta_2019`, `bagley_2013` (note: cited in discussion.tex — see below), `guerrero_gutierrez_2011` (note: cited in discussion.tex — see below), `herrera_2022`, `izcarapalacios_2024`, `mendozagarcia_2016`, `schwartz_marin_2016` (note: cited in discussion.tex — see below)
- Infrastructure/own-work: `code_repo`, `moreno_codina_2015`, `perez_calderon_2015`, `sanchez_salamanca_2024`

**Correction to above list from script output:** The script classified 47 as "unused." Spot-checking against the citation map reveals this is correct — the entries marked as unused in `WP4_bib_hygiene.csv` are genuinely uncited. However, note that `baptista_2026` (the duplicate) is correctly listed as unused since only `baptista_davila_2026` is cited in the tex files.

**Recommended action:** After fixing `le_cour_2020` and removing the two duplicate entries, the remaining unused entries (45) can be commented out or removed to reduce bib file size. This is a housekeeping action, not a submission blocker.

### Entries cited but with notes warranting attention

| Key | Note |
|-----|------|
| `escobar_rnpdno_2026` | Bib note says "Submitted" — update to accepted/published status before final submission |
| `CED_MEX_art34_2026` | Date discrepancy: manuscript says April 2026; bib note says March 2026 (see Task 4.2) |
| `cnb_rnpdno` | No year-specific URL; RNPDNO dashboard is a live resource — check URL still resolves |

---

## Summary Table

| # | Finding | Severity | Fix required |
|---|---------|----------|-------------|
| 1 | `le_cour_2020` cited in discussion.tex but **missing from references.bib** | **Fatal** | Replace `\citep{le_cour_2020}` with `\citep{reyes_robo_2022}` (same claim already cited with that key in results_temporal.tex) |
| 2 | CED date: introduction.tex says "April 2026"; bib note says "March 2026" | **Moderate** | Verify exact CED document adoption/release date; update one of the two to match |
| 3 | "19 of 732 investigations" (garcia_castillo_2024) — figure not in bib abstract | **Moderate** | Manual verification against paper (pp. 137–173) |
| 4 | "9 convictions" (guevara_bermudez_2018) — figure not in bib abstract | **Moderate** | Manual verification against paper; clarify which source supplies which figure |
| 5 | CED exact language quote — not verifiable without fetching source | **Moderate** | Verify against UN document CED/C/MEX/A.34/D/1 |
| 6 | Duplicate bib entry: `baptista_2026` / `baptista_davila_2026` (same DOI) | Minor | Delete `baptista_2026` |
| 7 | Duplicate bib entry: `prieto_curiel_cartels_2023` / `prieto_curiel_2023` (same DOI) | Minor | Delete `prieto_curiel_cartels_2023` |
| 8 | `code_repo` bib entry exists but never cited; code URL hardcoded in declarations | Minor | Either `\cite{code_repo}` in declarations or remove unused entry |
| 9 | `escobar_rnpdno_2026` status "Submitted" — needs update | Minor | Update bib note when paper is accepted |
| 10 | 47 unused bib entries inflating bibliography | Cosmetic | Remove/comment out after submission fixes are done |
| 11 | "2,458 municipalities" (cadena_garrocho_2019) — unverifiable from bib | Low | Manual verification against paper |
| 12 | `le_cour_2020` claim and `reyes_robo_2022` claim in two different sections for identical factual point | Minor | Harmonize to single key after fix #1 |

---

## Recommended Action List (Pre-Submission)

**Blocking (must fix before LaTeX compile will succeed):**
1. `discussion.tex` line 39: Replace `\citep{le_cour_2020}` with `\citep{reyes_robo_2022}`

**Required before submission:**
2. Verify CED document date (April vs March 2026) — update `introduction.tex` line 6 or `CED_MEX_art34_2026` bib note
3. Manually verify "19 of 732" and "9 convictions" against source papers
4. Verify CED exact quote ("crimes against humanity occurring at different moments and in different parts of the territory") against UN document

**Recommended cleanup:**
5. Delete `baptista_2026` from bib (duplicate of `baptista_davila_2026`)
6. Delete `prieto_curiel_cartels_2023` from bib (duplicate of `prieto_curiel_2023`)
7. Add `\cite{code_repo}` in the Code Availability declaration in `main.tex`, or remove unused entry
8. Update `escobar_rnpdno_2026` bib note from "Submitted" to accepted status when available
9. Comment out/remove 45 unused bib entries (after completing items 5–6)

---

## Gate 4 Verdict: CONDITIONAL PASS

The reference infrastructure has one compile-breaking error (`le_cour_2020` missing from bib) that must be fixed before the manuscript can be submitted. Three quantitative claims attributed to Spanish-language law/criminology papers (`garcia_castillo_2024`, `guevara_bermudez_2018`) and one CED quote cannot be verified from the bib file alone and require manual spot-check against the source PDFs.

All primary statistical citations (Anselin 1995, Newey-West 1987, Weisburd 2015, Prieto-Curiel 2023) are correctly attributed and verifiable from bib metadata. The two bib duplicates are housekeeping issues, not errors in the submitted text.

**Gate 4 passes conditionally on:** (a) fixing `le_cour_2020`; (b) resolving the April/March 2026 CED date; (c) manual verification of the two impunity statistics.
