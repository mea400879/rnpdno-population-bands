# CLAUDE CODE TASK — Draft Complete JQC Manuscript

**Date:** 2026-04-06
**Mode:** Autonomous. Create modular .tex files. Overwrite `manuscript/main.tex` with a master file that `\input{}`s each section.
**Project root:** `/home/marco/workspace/work/rnpdno-population-bands/`

---

## YOUR ROLE

You are Marco's research co-author writing a manuscript for the **Journal of Quantitative Criminology (JQC)**, a Q1 Springer methods journal. Tone: direct, academic, technically precise. No filler. Frame causal interpretations as hypotheses.

---

## INPUTS — READ ALL BEFORE WRITING A SINGLE LINE

1. `manuscript/main.tex` — current draft skeleton with session notes, TODOs, equations, figure/table placements
2. `manuscript/references.bib` — bibliography (~42 entries, replace with the new file Marco provides)
3. `reports/paper1_verification/00_inventory.md` through `10_ced_alignment.md` — **every number in the manuscript must come from these files**
4. `PAPER1_BLUEPRINT.md` — section-by-section plan, figure/table specs, research questions
5. `CLAUDE_CODE_RERUN_FINAL.md` — figure/table inventory with renumbered filenames

---

## OUTPUT STRUCTURE

Create these files in `manuscript/sections/`:

```
manuscript/
├── main.tex                          ← master file (overwrite)
├── sections/
│   ├── abstract.tex
│   ├── introduction.tex
│   ├── data.tex
│   ├── methods.tex
│   ├── results_descriptive.tex       (§3.1)
│   ├── results_concentration.tex     (§3.2 — RQ1)
│   ├── results_clustering.tex        (§3.3 — RQ2)
│   ├── results_temporal.tex          (§3.4 — RQ3)
│   ├── results_sex.tex               (§3.5 — RQ4)
│   ├── results_ced.tex               (§3.6 — CED alignment, new)
│   ├── discussion.tex
│   ├── conclusion.tex
│   └── appendix.tex
├── figures/                          ← already populated (fig1–fig9)
├── tables/                           ← already populated (table1–table7)
└── references.bib
```

`main.tex` should contain:
- Document class, packages, metadata, `\newcommand` definitions
- `\input{sections/abstract}`
- `\input{sections/introduction}`
- etc. for each section
- `\bibliography{references}`
- `\input{sections/appendix}`

---

## STUDY PARAMETERS — USE THESE COMMANDS IN PREAMBLE

```latex
\newcommand{\studyperiod}{January 2015 -- December 2025}
\newcommand{\nmonths}{132}
\newcommand{\nmunis}{2,478}
\newcommand{\referencemonth}{June 2025}
\newcommand{\bookendstart}{June 2015}
\newcommand{\nislands}{0}
\newcommand{\nLISAruns}{1,584}
```

Use these throughout the body so the entire manuscript updates from one place.

---

## TODO SYSTEM — MANDATORY

```latex
\newcommand{\todo}[1]{\textcolor{red}{\textbf{[TODO: #1]}}}
\newcommand{\todoverify}[1]{\textcolor{orange}{\textbf{[VERIFY: #1]}}}
\newcommand{\todocite}[1]{\textcolor{blue}{\textbf{[CITE: #1]}}}
\newcommand{\todowrite}[1]{\textcolor{purple}{\textbf{[WRITE: #1]}}}
```

Rules:
- **Never guess a number.** If not in verification reports, use `\todoverify{}`.
- **Never invent a citation.** If not in references.bib, use `\todocite{}`.
- **Never make Marco's decisions.** If two framings are possible, use `\todowrite{}`.
- After full draft, add a TODO summary as a comment block at end of main.tex.

---

## SECTION-BY-SECTION INSTRUCTIONS

### abstract.tex (~250 words, write LAST)

JQC requires structured abstract: **Objectives / Methods / Results / Conclusions**.

Key numbers to include:
- First outcome-disaggregated spatial analysis, N=\nmunis{} municipalities, \nmonths{} months
- Jaccard NL↔LD = 0.143, LA↔LD = 0.151 (non-interchangeability)
- Centro fastest-growing: NL +4.96 munis/yr (p<0.001)
- Bajío Total declining: −1.09/yr (p<0.001)
- Concentration: 50% of NL cases in 42 municipalities (1.7%) — 2–3× Weisburd benchmark
- CED Article 34 decision (March 2026) as motivating context
- Policy: forensic ≠ prevention geography

### introduction.tex (~1,500 words)

**Structure (6 blocks):**

1. **Scale and stakes** (~250w): 132,000+ disappeared and not located. CED Article 34 decision (March 2026) — first ever referral to UN General Assembly under this article. Crimes against humanity finding. Cite `\citep{CED_MEX_art34_2026, mandolessi_2022, solar_2021, guercke_2021}`. The CED explicitly notes attacks occurred "at different moments and in different parts of the territory" — this is precisely what our analysis quantifies.

2. **Spatial criminology lineage** (~300w): Hot spots \citep{sherman_1989}, routine activities \citep{cohen_felson_1979}, LISA \citep{anselin_1995}, law of crime concentration \citep{weisburd_2015}, JQC special issues \citep{braga_law_2017, andresen_advances_2021}. Concentration measurement \citep{prieto_curiel_2018, schnell_braga_piza_2017}. Crime at places stability \citep{weisburd_2004, curman_2015, steenbeek_weisburd_2016}. Establish that LISA and concentration are standard JQC tools.

3. **Mexico-specific spatial work** (~250w): Cadena & Garrocho (2019) — homicides + disappearances at municipal level, 2006–2017, but **treated as monolithic**. Atuesta & González (2024) — organized crime disappearances in 3 states only. Aguilar-Velázquez et al. (2025) — Mexico City only. Vilalta & Muggah (2016), Vilalta et al. (2021) — homicide diffusion in CDMX. **Engage with each**: what they did, what data, what they found, what they missed.

4. **The gap** (~250w): ALL prior work treats disappearances as a single phenomenon. No study examines whether outcome statuses produce distinct spatial patterns. Why it matters: Not Located = active search failure; Located Alive = recovery; Located Dead = lethal outcome. Different processes → different geographies → different policy needs. The RNPDNO makes decomposition possible but no one has done it at national scale.

5. **This paper** (~200w): First outcome-disaggregated spatial analysis at national scale with monthly resolution. Two novelties: (i) cross-status non-interchangeability via Jaccard; (ii) monthly resolution revealing dynamics invisible to annual analyses (Centro expansion). Cite Data in Brief descriptor for dataset. Note CED alignment analysis.

6. **Research questions** (~150w): State RQ1–RQ4 as enumerated list. Add brief mention that we also examine alignment with the CED's geographic claims.

### data.tex (~800 words)

**Structure:**

1. RNPDNO: 4 CSVs by outcome status. Cite Data in Brief descriptor. Brief: municipality×month cells, 12-column schema, cvegeo join key. **Flow not stock** — these are new monthly registrations. Keep the well-written flow paragraph from current main.tex (lines 147–165). Row counts from `00_inventory.md` and `table1_dataset_summary.tex`.

2. Sex composition from `06_sex_disaggregation.md`: NL male-dominated, LA near-parity, LD strongly male. Preview of RQ4.

3. Sentinel geocodes excluded. Counts from `01_municipality_reconciliation.md`.

4. INEGI Marco Geoestadístico: \nmunis{} municipalities, EPSG:6372.

5. Regional classification: 5 regions per CESOP. Bajío sub-flag. Cite Mexicoencifras.

6. Table 1 here (`table1_dataset_summary.tex`).

### methods.tex (~1,200 words)

**Keep equations from current main.tex** (Moran's I Eq.1, LISA Eq.2, Gini Eq.3, HHI Eq.4). They are well-formatted.

**Structure:**

1. Spatial weights: Queen contiguity with fuzzy tolerance (50m buffer via `fuzzy_contiguity`), row-standardized. **\nislands{} islands** — the buffer resolves all boundary gaps. Cite PySAL.

2. Global Moran's I: Eq.1. 999 permutations, α=0.05.

3. LISA: Eq.2. HH/LL/HL/LH/NS classification. Connected-component HH clusters (min size 3, BFS on Queen graph). Note LL suppression: LL is not interpreted as a substantive finding due to the extreme zero-inflation of the count data.

4. Concentration: Gini (Eq.3) and HHI (Eq.4). Weisburd (2015) benchmark.

5. Trend analysis: OLS on monthly HH counts by region×status. Newey-West HAC SE (bandwidth=12). Slopes in municipalities/year.

6. Sex disaggregation: LISA repeated for male and female counts separately. Flag female Located Dead power limitation (mean ~0.01 cases/muni/month).

7. CED alignment: Post-hoc extraction of HH dynamics for 8 CED-named states with temporal window overlay.

8. Total computational scope: \nLISAruns{} LISA runs (4 statuses × 3 sexes × \nmonths{} months), each on N=\nmunis{} municipalities.

### results_descriptive.tex (~400 words, §3.1)

- Time series description from Fig 1. NL growth from ~3,745/yr (2015) to ~12,888/yr (2024).
- Sex imbalance by status.
- Fig 1 and Table 2.
- Source: current main.tex lines 285–315 have good prose — adapt and update numbers.

### results_concentration.tex (~500 words, §3.2 — RQ1)

- Gini > 0.91 for all statuses. LD most concentrated (0.975).
- Weisburd benchmark: 50% of NL in 42 munis (1.7%) vs 4–6% benchmark.
- Gini declining over time but remains extreme. Numbers from `03_concentration.md`.
- Fig 2 (Gini time series) and Table 3.

### results_clustering.tex (~700 words, §3.3 — RQ2, CORE SECTION)

- Moran's I significant in nearly all months for all statuses. From `04_clustering.md`.
- LISA Jun 2025: Table 4 with HH/LL/HL/LH/NS counts.
- **Jaccard matrix — headline result.** NL↔LD = 0.143. LA↔LD = 0.151. NL↔LA = 0.381. From `04_jaccard_matrix.csv`. Report all 6 pairs.
- Cluster geography: describe where HH clusters are for each status from `04_clustering.md`.
- Jaccard stable across reference periods from `07_robustness.md`.
- Fig 3 (Moran's I), Fig 4 (LISA maps), Table 4, Table 5.

### results_temporal.tex (~700 words, §3.4 — RQ3)

Three narratives from `05_temporal_dynamics.md` and `02_trend_slopes.csv`:

1. **Centro expansion:** Largest positive slopes all 4 statuses. NL: +4.96/yr (p<0.001). Inflection ~2019.
2. **Norte consolidation:** All 4 statuses positive and significant.
3. **Bajío decline:** Total −1.09/yr (p<0.001). "Rising Bajío" hypothesis rejected.

- Fig 5 (HH trend: Norte vs Bajío vs Centro), Fig 6 (bookend LISA maps), Fig 8 (heatmap), Table 6.
- Frame Centro as either real increase or reporting artifact — present BOTH hypotheses.

### results_sex.tex (~400 words, §3.5 — RQ4)

- NL: M=85 HH, F=50 HH, overlap=28, Jaccard=0.262. From `06_sex_disaggregation.md`.
- LD: M=27, F=0. Female LD is a power failure, not a finding.
- LA near-parity discussion.
- Fig 7 (sex maps), Table 7.

### results_ced.tex (~500 words, §3.6 — NEW)

This section is new. It positions our empirical findings against the CED's qualitative geographic claims. From `10_ced_alignment.md`:

- The CED identifies "multiple attacks at different moments and in different parts of the territory." Our LISA analysis quantifies this: HH clusters emerge and shift across states over 132 months.
- Estado de México: strongest growth (+2.36/yr NL, p<0.001). CED window aligned.
- Nuevo León: +1.34/yr LA, +0.80/yr LD. CED window aligned.
- Guanajuato: NL rising (+0.75/yr) but LA declining (−0.57/yr). Composition shift.
- Jalisco: declining HH across all statuses (peaks 2019). Counter to "currently highest" claim — our HH metric captures clustering, not absolute volume.
- Coahuila, Veracruz, Nayarit: low/zero HH municipalities in our data — these states' crisis periods (2009–2017) are captured only at the tail end of our study window.
- Tabasco: CED flags girls/women. Our data shows female LA HH muni-months (31) exceeding male (6) in 2023–2025 — consistent with CED claim.
- Fig 9 (CED states small-multiples).

**Frame carefully:** We do not adjudicate state responsibility. We provide the first quantitative spatial evidence that disappearance patterns vary by state and period, consistent with the CED's characterization of multiple localized attacks.

### discussion.tex (~1,500 words)

**§4.1 Non-Interchangeability (~400w):**
- Jaccard < 0.15 for LD pairs. Different municipalities, different dynamics.
- Policy: forensic ≠ prevention geography. Connect to Andresen (2006): counts vs rates produce different hotspots — our cross-status decomposition is an analogous divergence.
- Connect to Braga et al. (2017): crime type disaggregation matters for concentration.

**§4.2 Regional Dynamics (~400w):**
- Centro: real expansion or reporting artifact? Two hypotheses. Cannot distinguish with RNPDNO alone.
- Norte: multi-status consolidation — entrenched OC + some forensic capacity.
- Bajío: rejected as rising hotspot. Qualifies Cadena & Garrocho (2019).

**§4.3 CED Alignment (~300w):**
- Our findings provide the first national-scale quantitative evidence supporting the CED's characterization of spatially and temporally heterogeneous "attacks."
- The RNPDNO aggregates all disappearances, not only enforced disappearances (the government's argument). Our spatial clusters reflect the composite phenomenon.
- Note: the government rejected the CED report. Our analysis is descriptive and does not adjudicate the legal question.

**§4.4 Sex Patterns (~200w):**
- LA near-parity puzzle. Female LD underpowered.

**§4.5 Limitations (~400w):**
Enumerated (not bulleted). Items:
1. Raw counts — no population normalization (Paper 2 forthcoming). Cite Andresen (2006).
2. Ecological fallacy.
3. Zero-infilling: if absences = reporting failure, concentration underestimated.
4. Spatial weights: Queen contiguity may miss functional connectivity.
5. Descriptive design — no causal claims.
6. Underreporting: RNPDNO relies on registry. Weak-state areas underreported.
7. Female LD power: ~0.01 cases/muni/month.
8. RNPDNO does not distinguish enforced from non-enforced disappearances.
9. Nov–Dec 2025 reporting lag (June cross-sections mitigate but full-series trends include lagged months).

### conclusion.tex (~500 words)

1. Summary: first national-scale outcome-disaggregated monthly spatial analysis. N=\nmunis{}, \nmonths{} months, 4 statuses.
2. Empirical facts: (i) non-interchangeability (Jaccard), (ii) Centro fastest-growing, (iii) Bajío rejected, (iv) concentration 2–3× Weisburd, (v) CED geographic claims empirically supported.
3. Policy: outcome-specific geographic targeting. Forensic → LD hotspots. Prevention/search → NL hotspots. These are different places.
4. Future work: Paper 2 (population-normalized rates), Paper 3 (econometric panel).

### appendix.tex

- Robustness: reference period sensitivity (Jun 2025 vs Jun 2024). Numbers from `07_robustness.md`.
- Zero-inflation diagnostics by status and region.
- Full trend slopes table (all 24 region×status + Bajío combinations).

---

## WHAT TO KEEP FROM CURRENT main.tex

- Equations 1–4 (Moran's I, LISA, Gini, HHI) — well-formatted, copy into methods.tex
- Flow-vs-stock paragraph (lines 147–165) — well-written, copy into data.tex
- Time series prose (lines 297–306) — good, update numbers for data.tex/results_descriptive.tex
- Session notes — read for context but **strip all** from output
- Limitations structure (lines 667–687) — expand in discussion.tex

## WHAT TO STRIP

- All `\todo{}` macros from current draft — replace with written text or new TODOs
- All session notes in `%` comments
- All references to "December 2024" — replace with `\referencemonth{}`
- All references to "52 islands" — replace with `\nislands{}`
- Old figure filenames (fig5_lisa_maps_latest → fig4, etc.) — use renumbered names per CLAUDE_CODE_RERUN_FINAL.md
- Old table references (table8 → table7, table6_regional_composition → gone, replaced by Fig 8)
- `\usepackage{soul}` and `\hl` highlighting

---

## FIGURE CROSS-REFERENCES (renumbered)

| Ref | Filename | Caption describes |
|-----|----------|-------------------|
| `\ref{fig:timeseries}` | `fig1_time_series_by_status` | Monthly counts by status, sex-disaggregated |
| `\ref{fig:gini}` | `fig2_gini_time_series` | Gini coefficient with OLS slopes |
| `\ref{fig:morans}` | `fig3_morans_i_time_series` | Global Moran's I by status |
| `\ref{fig:lisa_latest}` | `fig4_lisa_maps_latest` | LISA maps Jun 2025, LL grey |
| `\ref{fig:hh_trend}` | `fig5_hh_trend_norte_bajio` | HH trend: Norte vs Bajío vs Centro |
| `\ref{fig:lisa_comparison}` | `fig6_lisa_maps_2015_vs_2025` | Bookend LISA maps |
| `\ref{fig:sex_maps}` | `fig7_sex_disaggregation_maps` | Male vs female LISA |
| `\ref{fig:heatmap}` | `fig8_regional_hh_heatmap` | Regional HH heatmap |
| `\ref{fig:ced_states}` | `fig9_ced_states` | CED state-level small-multiples |

## TABLE CROSS-REFERENCES

| Ref | Filename | Content |
|-----|----------|---------|
| `\ref{tab:dataset}` | `table1_dataset_summary` | Dataset summary by status |
| `\ref{tab:summary}` | `table2_summary_statistics` | Summary statistics |
| `\ref{tab:concentration}` | `table3_concentration_metrics` | Gini/HHI ranges and trends |
| `\ref{tab:lisa_counts}` | `table4_lisa_classification` | LISA counts Jun 2025 |
| `\ref{tab:crosstab}` | `table5_hh_cross_tabulation` | Pairwise HH overlap / Jaccard |
| `\ref{tab:slopes}` | `table6_trend_slopes` | OLS slopes by region×status |
| `\ref{tab:sex}` | `table7_sex_hh_counts` | HH by sex |

---

## CONSTRAINTS

1. **Every number must trace to a verification report (00–10).** If not found, use `\todoverify{}`.
2. **Every citation must exist in references.bib.** If not found, use `\todocite{}`.
3. **All cross-sections use June 2025.** Use `\referencemonth{}` macro.
4. **All regional narratives are hypotheses, not causal claims.**
5. **Report non-significant results** (e.g., Bajío LD slope p=0.07). No p-hacking.
6. **LaTeX must compile** with natbib + apalike.
7. **Target word count:** ~8,000–9,000 words total (excluding references and appendix). JQC typical range.

---

## EXECUTION

1. Read all inputs listed above.
2. Create `manuscript/sections/` directory.
3. Write each .tex file in order: data → methods → results (6 files) → discussion → conclusion → introduction → abstract (last).
4. Write main.tex (master file with `\input{}` calls).
5. Attempt to compile: `cd manuscript && pdflatex main && bibtex main && pdflatex main && pdflatex main`
6. Fix any compilation errors.
7. Count TODOs and append summary to end of main.tex as comment.
8. Git commit.

---

## CRITICAL REMINDERS

- The CED Article 34 decision (March 2026) is the most significant external event for this paper. It belongs in the Introduction (paragraph 1) AND Discussion (§4.3) AND Results (§3.6). Do not underplay it.
- The "rising Bajío" hypothesis is **rejected**. Bajío Total slope = −1.09/yr (p<0.001). Do not frame Bajío as rising.
- Centro is the surprise finding. Centro NL slope = +4.96/yr. This was invisible to annual analyses.
- Located Dead has only 35 HH municipalities in Jun 2025. Interpret with caution due to sparseness.
- Female Located Dead: 0 HH municipalities. This is a power failure, not a substantive finding. Disclose in methods AND results.
