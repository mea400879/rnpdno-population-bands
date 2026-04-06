# PROMPT — Overhaul main.tex into Complete JQC Manuscript Draft

---

## YOUR ROLE

You are Marco's research co-author. Tone: laconic, academic, direct. No pleasantries. You are writing a manuscript for the **Journal of Quantitative Criminology (JQC)**, a Q1 Springer methods journal in criminology.

You will receive:
- `main.tex` — the current draft (skeleton with TODOs, session notes, some written prose in Methods and partial Results)
- `references.txt` — complete BibTeX database (~90 entries, natbib, author-year style)
- Verification reports (`01_municipality_reconciliation.md` through `08_executive_summary.md`) — pipeline output summaries with exact numbers
- `rnpdno_update.tex` — the companion Data in Brief paper (for cross-referencing dataset details)

Your job: **rewrite main.tex into a complete, submission-ready manuscript.** Replace all TODOs. Strip all session notes. Every number must come from the verification reports. Every citation must exist in references.txt.

---

## STUDY PERIOD

The pipeline covers January 2015 through December 2025 (132 months). However, the verification reports compute headline numbers through **December 2024 (120 months)**. A separate diagnostic (09_endpoint_diagnosis.md) will determine whether Nov–Dec 2025 data is reliable or shows administrative reporting lag.

**Rule:** Use the numbers as they appear in the verification reports (Dec 2024 endpoint). Where the text frames the study period, write it as a placeholder that Marco will finalize after the endpoint diagnostic:

```latex
\newcommand{\studyperiod}{January 2015 -- December 2024}  % UPDATE after endpoint diagnosis
\newcommand{\nmonths}{120}  % UPDATE after endpoint diagnosis
\newcommand{\referencemonth}{December 2024}  % UPDATE after endpoint diagnosis
```

Define these commands in the preamble. Use `\studyperiod`, `\nmonths`, and `\referencemonth` throughout the body so the entire manuscript updates from one place.

---

## CORE ARGUMENT

Prior spatial analysis of disappearances in Mexico treats them as a monolithic phenomenon. The RNPDNO distinguishes four outcome statuses: Total (0), Not Located (7), Located Alive (2), Located Dead (3). We demonstrate they are **spatially non-interchangeable**: different municipalities, different dynamics, different regional trajectories. Policy: forensic teams and prevention programs need different geographic targeting.

## RESEARCH QUESTIONS

- **RQ1 (Concentration):** How concentrated are disappearances, and does concentration differ by status?
- **RQ2 (Clustering):** Do the four statuses produce distinct spatial cluster geographies?
- **RQ3 (Temporal dynamics):** How has spatial distribution evolved? Do Norte, Centro, and Bajío diverge?
- **RQ4 (Sex disaggregation):** Do male and female disappearances show different spatial patterns?

---

## SECTION-BY-SECTION INSTRUCTIONS

### Abstract (~250 words)
Write LAST, after all sections are done. Structured: Objectives / Methods / Results / Conclusions. Key numbers to include:
- First outcome-disaggregated spatial analysis, N=2,478 municipalities, \nmonths{} months
- Jaccard LA↔LD = 0.071, NL↔LD = 0.091 (non-interchangeability headline)
- Centro fastest-growing region: NL +3.92 munis/yr
- Bajío "rising" hypothesis rejected: Total −1.33/yr
- Concentration 2–6× Weisburd benchmark
- Policy: forensic ≠ prevention geography

### Introduction (~3,500 words)

**Structure (6 paragraphs/blocks):**

1. **Scale and stakes** (~400w): Mexico's disappearance crisis. 250k+ cumulative RNPDNO. Humanitarian toll. International context (OHCHR, IACHR). Cite `\citep{mandolessi_introductiondisappearances_2022, solar_forced_2021, guercke_state_2021}`.

2. **Spatial criminology lineage** (~600w): Hot spots (Sherman 1989) → law of crime concentration (Weisburd 2015) → JQC special issues (Braga, Andresen & Lawton 2017; Andresen et al. 2021) → concentration measurement (Prieto Curiel et al. 2018; Schnell, Braga & Piza 2017) → crime at places stability (Weisburd et al. 2004; Curman et al. 2015; Steenbeek & Weisburd 2016). Routine activities as theoretical anchor (Cohen & Felson 1979). Establish that spatial concentration and LISA are standard JQC tools.

3. **Mexico-specific spatial work** (~500w): Osorio (2015) contagion of drug violence. Vilalta & Muggah (2016), Vilalta et al. (2021) Mexico City. Cadena & Garrocho (2019) — **primary positioning target**: homicides + disappearances at municipal level, but treated as monolithic. Atuesta & González (2024) organized crime disappearances in 3 states. Aguilar-Velázquez et al. (2025) Mexico City disappearances. Engage with each: what did they do, what did they miss.

4. **The gap** (~400w): ALL prior work treats disappearances as a single phenomenon. No study has examined whether outcome statuses produce distinct spatial patterns. Why this matters: Not Located = active search failure; Located Alive = recovery; Located Dead = lethal outcome. These reflect different processes, different actors, potentially different geographies. The RNPDNO registry makes decomposition possible but no one has done it.

5. **This paper's contribution** (~300w): First outcome-disaggregated spatial analysis at national scale with monthly resolution. Two axes of novelty: (i) cross-status non-interchangeability via Jaccard similarity; (ii) monthly temporal resolution revealing dynamics invisible to annual analyses (Centro expansion). Cite the DiB descriptor for the dataset. Frame as Paper 1 of a series (Paper 2: rates, Paper 3: econometrics).

6. **Research questions** (~200w): State RQ1–RQ4 as enumerated list. Brief roadmap of paper structure.

**Critical instruction:** Do NOT just cite papers — engage with them. State what each study did, what data they used, what they found, and what they missed. The Introduction is a scholarly argument, not a bibliography.

### Data and Methods (~2,000 words)

**§2.1 Data (~800w):**
- RNPDNO: 4 CSVs by outcome status. Cite DiB descriptor (`\citep{RNPDNO_DiB}`) for full pipeline details. Brief: municipality×month cells, 12-column schema, cvegeo join key.
- **Flow not stock**: These are new monthly registrations, not cumulative. The commonly cited 111k–115k is the historical stock. Explain clearly. (Use text from current main.tex lines 147–165, which is well-written.)
- Row counts from 01_municipality_reconciliation.md: panel = 2,478 × 4 × \nmonths{} = rows.
- Sex composition from 06_sex_disaggregation.md Task 6.1: NL 78.3% male, LA 48.8% male, LD 85.8% male. Flag this as a preview of RQ4.
- INEGI Marco Geoestadístico: 2,478 municipalities, EPSG:6372. Perfect match with panel (01_municipality_reconciliation.md).
- Regional classification: 5 regions per CESOP. Bajío sub-flag crosses Centro and Centro-Norte. Cite Mexicoencifras.
- Table 1 here (dataset summary by status).

**§2.2 Spatial Methods (~1,200w):**
- Spatial weights: Queen contiguity, row-standardized, 52 islands (2.1%). Cite `\citep{Rey2021}` for PySAL.
- Moran's I: equation (keep Eq. 1 from current draft). 999 permutations, α=0.05. Cite `\citep{Moran1950, Anselin1995}`.
- LISA: equation (keep Eq. 2). HH/LL/HL/LH/NS classification. Cite `\citep{Anselin1995}`.
- Connected-component HH clusters: min size 3, BFS on Queen graph.
- Gini coefficient: equation (keep Eq. 3). Cite Weisburd (2015) benchmark.
- HHI: equation (keep Eq. 4).
- Trend analysis: OLS on monthly HH counts by region×status. Newey-West HAC SE, bandwidth=12. Cite `\citep{noauthor_simple_nodate}` (Newey & West 1987 — NOTE: fix this bibkey). Slopes in municipalities/year.
- Sex disaggregation: repeat LISA for male and female counts separately. Flag female Located Dead power limitation upfront (0.0065 cases/muni/month).
- Tobler's First Law as one-sentence justification: `\citep{tobler_computer_1970}`.

### Results (~2,500 words)

**§3.1 Descriptive Overview (~400w):**
- Time series description. Not Located tripled from ~3,745/yr (2015) to ~12,888/yr (2024). Located Dead nearly quadrupled.
- Fig 1 reference (time series — already in current draft, adapt).
- Table 2: summary statistics.
- Source: current draft lines 297–315 have good prose. Expand with 2024 numbers.

**§3.2 Geographic Concentration — RQ1 (~500w):**
- Gini > 0.91 for all statuses across all months. Located Dead: 0.96–0.99.
- Weisburd benchmark: 50% of cases in 1.0–1.9% of municipalities vs. 4–6% benchmark. Disappearances 2–6× more concentrated. (03_concentration.md Task 3.3)
- Gini DECLINING over time (all statuses, p<0.001) but remains extreme. Cases slowly dispersing to more municipalities. (03_concentration.md Task 3.1)
- Zero municipalities: 78.6% (Total) to 96.1% (Located Dead) in Dec 2024. (03_concentration.md Task 3.2)
- Reference Gini/Lorenz figure and concentration table → move to SI. Cite numbers in text.

**§3.3 Spatial Clustering — RQ2 (~700w): THE CORE SECTION**
- Moran's I significant in 100% of months for Total/NL, 95% for LA, 87.5% for LD. Increasing over time. (04_clustering.md Task 4.1)
- LISA Dec 2024: Table 2 with HH/LL/HL/LH/NS counts. Located Dead asymmetry: 18 HH vs 118 LL (inverted pattern). (04_clustering.md Task 4.2)
- **Jaccard matrix — headline result.** LA↔LD = 0.071. NL↔LD = 0.091. NL↔LA = 0.387. Report for all 6 pairs. (04_clustering.md Task 4.3)
- Cluster geography: Total/NL/LA primary cluster = CDMX metro (29–32 munis). LD primary cluster = Guanajuato corridor (Celaya–Salamanca–Cortazar–Villagrán). LD has NO cluster in CDMX. (04_clustering.md Task 4.5)
- Jaccard stable across 3 reference periods (Dec 2023, Jun 2024, Dec 2024): LD pairs always < 0.22. (07_robustness.md Task 7.1)
- Fig 1 (LISA maps) and Table 2 (Jaccard matrix) are the paper's key display items.

**§3.4 Temporal Dynamics — RQ3 (~600w):**
- Three narratives, each with exact numbers from 05_temporal_dynamics.md:
  - **Centro expansion:** NL +3.92/yr*** (8→42 munis). Inflection 2019. Largest slopes for all 4 statuses.
  - **Norte consolidation:** All 4 statuses positive and significant. LA steepest (+1.12/yr***). LD emerged from 0 to 5.
  - **Bajío decline:** Total −1.33/yr** (12→8). No status shows positive trend. "Rising Bajío" rejected.
- Table 3 (trend slopes) and Fig 2 (time series) here.
- Fig 3 (LISA comparison 2015 vs 2024) here.

**§3.5 Sex Disaggregation — RQ4 (~300w):**
- NL male/female Jaccard = 0.317. Male 2.4× more HH munis (76 vs 32). (06_sex_disaggregation.md Task 6.3)
- LA male/female Jaccard = 0.562. Near-parity in counts → near-parity in geography. (06_sex_disaggregation.md Task 6.3)
- Female LD: 0 HH municipalities. Power failure — 0.0065 cases/muni/month, 78.3% all-zero. Report as limitation, not finding. (06_sex_disaggregation.md Task 6.5)
- LA female-only HH munis lean Norte (9/23) vs male-only lean Centro (9/16). (06_sex_disaggregation.md Task 6.4)
- Fig 4 (male vs female NL maps) here.

### Discussion (~1,500 words)

**§4.1 Non-Interchangeability (~500w):**
- Synthesize: Jaccard < 0.10 for LD pairs. CDMX vs Guanajuato corridor. Policy: forensic ≠ prevention geography.
- Connect to Andresen (2006): counts vs rates produce different hotspots. Our cross-status decomposition is an analogous divergence.
- Connect to Braga, Andresen & Lawton (2017): crime type disaggregation matters for concentration — our finding extends this to disappearance outcomes.

**§4.2 Regional Dynamics (~500w):**
- Centro: real expansion or reporting artifact? Present both hypotheses. Cite Rios (2013), Osorio (2015) for cartel mechanisms. Cannot distinguish with RNPDNO alone.
- Norte: multi-status consolidation suggests entrenched OC + some forensic capacity. Cite Atuesta & González (2024), Shirk & Wallman (2015).
- Bajío: rejected as rising hotspot. Transitional peak, not structural. Qualifies Cadena & Garrocho (2019).
- Frame ALL causal interpretations as hypotheses.

**§4.3 Sex Patterns (~200w):**
- LA near-parity puzzle: women 51% of LA but only 22% of NL. Different disappearance typologies? Registration differences? Hypothesis only.
- Female LD underpowered. Male LD interpretable.

**§4.4 Limitations (~300w):**
Enumerated, not bulleted. Six items:
1. Raw counts only — no population normalization (Paper 2 forthcoming). Cite Andresen (2006).
2. Ecological fallacy — municipal-level, no individual inference.
3. Zero-infilling: 83–97% zero cells (07_robustness.md Task 7.3). If absences = reporting failure, concentration underestimated.
4. Spatial weights: Queen contiguity may miss functional connectivity. Islands: 0 HH are islands (07_robustness.md Task 7.2).
5. Descriptive design — no causal claims.
6. Underreporting: RNPDNO relies on registry. Weak-state areas underreported, biasing hotspots toward high-capacity jurisdictions.
7. Female Located Dead power: 0.0065 cases/muni/month.
8. LL island artifact: 91–93% of NL/LA LL municipalities are islands (07_robustness.md Task 7.2).

### Conclusion (~500 words)

Write this FIRST (working backwards). Four paragraphs:
1. Summary: first national-scale outcome-disaggregated monthly spatial analysis. N=2,478, \nmonths{} months, 4 statuses.
2. Empirical facts established: (i) non-interchangeability (Jaccard), (ii) Centro fastest-growing, (iii) Bajío rejected, (iv) concentration 2–6× Weisburd.
3. Policy: outcome-specific geographic targeting. Forensic → LD hotspots (Guanajuato, Norte). Prevention/search → NL hotspots (CDMX metro, expanding Centro).
4. Future work: Paper 2 (dual-metric: counts vs rates), Paper 3 (econometric panel with SESNSP + Banxico + mortality covariates).

---

## WHAT TO KEEP FROM CURRENT main.tex

- Equations 1–4 (Moran's I, LISA, Gini, HHI) — already well-formatted
- Flow-vs-stock paragraph (lines 147–165) — well-written, keep with minor edits
- Spatial weights paragraph (lines 200–206) — solid
- Time series prose (lines 297–306) — good, expand
- Located Dead HH/LL asymmetry observation (lines 401–408) — keep
- Limitations enumeration structure (lines 667–687) — expand

## WHAT TO STRIP

- All `\todo{}` macros — replace with written text
- All session notes in `%` comments (lines 67–86, 137–146, 484–514, 524–539, 578–593)
- The `\hl` and `\soul` packages (TODO highlighting)
- `\documentclass[12pt]{article}` — replace with JQC Springer template when ready (for now keep article class but note the change needed)

## WHAT TO ADD

- `\newcommand` definitions for study period, nmonths, reference month (see above)
- Data availability statement (JQC Type 2 policy): "Data and code are available at [OSF URL]."
- Declaration of generative AI use
- CRediT author statement

---

## CITATION RULES

- Only cite keys that exist in references.txt. Do not invent citations.
- Use `\citep{}` for parenthetical and `\citet{}` for textual.
- Aim for 50–60 unique citations. The Introduction should carry ~35 of these.
- Fix known broken bibkeys before citing:
  - `messner_spatial_nodate` → needs year=1999 added
  - `cohen_social_nodate` → needs year=1979 added
  - `noauthor_simple_nodate` → Newey & West 1987, needs author/year/journal added
  - `RNPDNO_DiB` → placeholder, cite as "Authors (forthcoming)" or replace with actual submission

---

## TODO SYSTEM — MANDATORY

The current main.tex defines `\todo{text}` (red bold). Keep this macro. When writing, you MUST use it instead of guessing. The following TODO categories are defined:

```latex
% In preamble — keep existing \todo, add typed variants:
\newcommand{\todo}[1]{\textcolor{red}{\textbf{[TODO: #1]}}}
\newcommand{\todoverify}[1]{\textcolor{orange}{\textbf{[VERIFY: #1]}}}
\newcommand{\todocite}[1]{\textcolor{blue}{\textbf{[CITE: #1]}}}
\newcommand{\todowrite}[1]{\textcolor{purple}{\textbf{[WRITE: #1]}}}
```

### When to use each:

- `\todoverify{...}` — A number that should come from the pipeline but you are not 100% certain it matches the verification reports. Example: `\todoverify{Confirm Dec 2025 HH count for Located Dead from updated 04\_clustering.md}`
- `\todocite{...}` — A claim that needs a citation you cannot find in references.txt. Example: `\todocite{Need reference for CJNG territorial expansion into Guanajuato post-2017}`
- `\todowrite{...}` — A passage that needs Marco's input (interpretation, framing decision, domain knowledge). Example: `\todowrite{Marco: choose between reporting-artifact vs real-increase framing for Centro}`
- `\todo{...}` — Generic catch-all for anything else.

### Rules:

1. **Never guess a number.** If it's not in the verification reports (01–08), use `\todoverify{}`.
2. **Never invent a citation.** If the claim needs a reference not in references.txt, use `\todocite{}`.
3. **Never make Marco's decisions.** If two framings are possible, write both and wrap in `\todowrite{}`.
4. **Fewer TODOs is better** — but a TODO is always preferable to a hallucinated number or fabricated citation.
5. After the full draft is complete, add a **TODO summary** as a LaTeX comment block at the end of the file listing all TODOs by type and count. Example:
```latex
% === TODO SUMMARY ===
% VERIFY: 3 items (numbers needing pipeline confirmation)
% CITE: 2 items (claims needing references)
% WRITE: 1 item (framing decisions for Marco)
% TOTAL: 6 open items
```

---

## CONSTRAINTS

1. Every number in the manuscript must trace to a specific verification report (01–08). If a number is not in the reports, use `\todoverify{}`.
2. Do not fabricate numbers. If you don't know a value, flag it.
3. Monthly resolution: 120 months (or \nmonths{} when updated). Not quarters, not years.
4. EPSG:6372 for all spatial work.
5. All regional narratives framed as hypotheses, not causal claims.
6. Report non-significant results (Bajío LD slope p=0.953). No p-hacking.
7. LaTeX must compile with natbib + apalike (current setup). Springer template swap happens later.
