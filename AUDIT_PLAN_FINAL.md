# RNPDNO Manuscript Pre-Submission Audit Plan

**Target:** Journal of Quantitative Criminology (JQC)
**Status:** Pre-submission, full audit
**Execution:** Local machine, Claude Code
**Principal:** Marco A. Escobar
**Audit design:** M-RESEARCH mode (hostile peer reviewer protocol)

---

## Governing Principles

1. Every numeric claim in the manuscript must be traceable to a script output with a timestamp and git commit hash.
2. Every citation must be verified against the actual source, not against memory or secondary quotation.
3. Every methodological choice must survive a hostile reviewer challenge or be defended in limitations.
4. No rewriting of the manuscript occurs before auditing. Identify problems first, fix second.
5. Each work package ends with a **Review Gate**: Claude Code produces a report; Marco and the M-RESEARCH assistant sync before next WP begins.

---

## Repository Structure (actual)

**Root:** `/home/marco/workspace/work/rnpdno-population-bands/`
(NOTE: directory is `rnpdno-population-bands`, not `rnpdno-populations-bands`)

```
rnpdno-population-bands/
├── data/
│   ├── raw/                          # symlinks to pCloudDrive originals (READ-ONLY)
│   │   ├── rnpdno_total.csv
│   │   ├── rnpdno_disappeared_not_located.csv
│   │   ├── rnpdno_located_alive.csv
│   │   └── rnpdno_located_dead.csv
│   ├── external/
│   │   ├── municipios_2024.geoparquet  # symlink, EPSG:6372
│   │   ├── bajio_corridor_municipalities.csv
│   │   ├── conapo_poblacion_1990_2070.parquet  # symlink, for rate normalization
│   │   └── ageeml_catalog.csv          # symlink, INEGI geographic catalog
│   ├── interim/
│   ├── processed/                     # derived analytical outputs
│   │   ├── panel_monthly_counts.parquet
│   │   ├── lisa_monthly_results.parquet
│   │   ├── hh_clusters_monthly.parquet
│   │   ├── morans_i_monthly.csv
│   │   ├── concentration_monthly.csv
│   │   ├── spatial_weights_queen.gal
│   │   ├── municipality_classification_v2.csv
│   │   ├── hh_clusters_{cases|rates}_{status}.csv  # 8 files
│   │   ├── bajio_corridor_hh_timeseries.csv
│   │   ├── ced_state_hh_timeseries.csv
│   │   ├── ced_temporal_alignment.csv
│   │   ├── cluster_comparison_rates_vs_cases.csv
│   │   ├── hh_cross_tabulation_latest.csv
│   │   ├── hh_regional_composition.csv
│   │   └── island_municipalities.csv
│   └── manual/
├── scripts/                          # numbered pipeline scripts
│   ├── 01_build_master_panel.py       # → panel_monthly_counts.parquet
│   ├── 10_build_monthly_panel.py      # → panel rebuild
│   ├── 11_build_spatial_weights.py    # → spatial_weights_queen.gal
│   ├── 12_compute_lisa_monthly.py     # → lisa_monthly_results.parquet
│   ├── 13_compute_concentration.py    # → concentration_monthly.csv
│   ├── 14_generate_figures.py         # → manuscript/figures/
│   ├── 15_generate_tables.py          # → manuscript/tables/
│   └── run_pipeline.py                # orchestrator
├── manuscript/
│   ├── main.tex
│   ├── references.bib
│   ├── sections/                      # modular .tex files
│   │   ├── introduction.tex
│   │   ├── data.tex
│   │   ├── methods.tex
│   │   ├── results_descriptive.tex
│   │   ├── results_concentration.tex
│   │   ├── results_clustering.tex
│   │   ├── results_temporal.tex
│   │   ├── results_sex.tex
│   │   ├── results_ced.tex
│   │   ├── discussion.tex
│   │   ├── conclusion.tex
│   │   └── appendix.tex
│   ├── figures/                       # PDF + PNG, 9 figures + VAWRI scatter
│   └── tables/                        # 6 .tex table files
├── reports/
│   └── paper1_verification/           # PRIOR verification (13 reports, 00-13)
│       ├── 08_executive_summary_v2.md
│       └── ...
├── rnpdno_eda/                        # source modules
│   └── models/spatial.py              # core spatial routines
├── audit/                             # WP reports go here
│   ├── WP1_data_integrity.md
│   ├── WP2_numeric_audit.md
│   ├── WP3_methodological_audit.md
│   ├── WP4_reference_audit.md
│   ├── WP5_discussion_factcheck.md
│   └── revision_memo.md
├── notebooks/
│   └── audit/                         # WP notebooks (to be created)
├── logs/
├── archive/
└── main.py
```

## Key Path References for Claude Code

| Resource | Path |
|----------|------|
| Raw CSVs | `data/raw/rnpdno_*.csv` (symlinks) |
| Geoparquet | `data/external/municipios_2024.geoparquet` |
| Population data | `data/external/conapo_poblacion_1990_2070.parquet` |
| Bajío corridor list | `data/external/bajio_corridor_municipalities.csv` |
| Regional classification | `data/processed/municipality_classification_v2.csv` |
| Constructed panel | `data/processed/panel_monthly_counts.parquet` |
| LISA results | `data/processed/lisa_monthly_results.parquet` |
| HH clusters | `data/processed/hh_clusters_monthly.parquet` |
| Spatial weights | `data/processed/spatial_weights_queen.gal` |
| Moran's I series | `data/processed/morans_i_monthly.csv` |
| Concentration series | `data/processed/concentration_monthly.csv` |
| Manuscript LaTeX | `manuscript/main.tex` + `manuscript/sections/*.tex` |
| Manuscript figures | `manuscript/figures/` |
| Manuscript tables | `manuscript/tables/` |
| Bibliography | `manuscript/references.bib` |
| Prior verification | `reports/paper1_verification/` |
| Pipeline scripts | `scripts/01-15_*.py` |
| Core spatial module | `rnpdno_eda/models/spatial.py` |
| CED decision doc | (available in project knowledge, not in repo) |
| VAWRI data | (location TBD — Marco confirms available) |
| Audit reports | `audit/WP*.md` |
| Audit notebooks | `notebooks/audit/` |

---

## Global Execution Protocol

Every audit notebook begins with this preamble to guarantee reproducibility:

```python
import polars as pl
import numpy as np
import hashlib
import json
from datetime import datetime
from pathlib import Path

AUDIT_SEED = 42
RUN_TIMESTAMP = datetime.now().isoformat()
AUDIT_LOG = {"seed": AUDIT_SEED, "timestamp": RUN_TIMESTAMP, "hashes": {}}

PROJECT_ROOT = Path("/home/marco/workspace/work/rnpdno-population-bands")
DATA_RAW = PROJECT_ROOT / "data" / "raw"
DATA_PROCESSED = PROJECT_ROOT / "data" / "processed"
DATA_EXTERNAL = PROJECT_ROOT / "data" / "external"
AUDIT_DIR = PROJECT_ROOT / "audit"
NOTEBOOKS_AUDIT = PROJECT_ROOT / "notebooks" / "audit"
MANUSCRIPT_DIR = PROJECT_ROOT / "manuscript"

for f in ["rnpdno_total.csv", "rnpdno_disappeared_not_located.csv",
          "rnpdno_located_alive.csv", "rnpdno_located_dead.csv"]:
    with open(DATA_RAW / f, "rb") as fh:
        h = hashlib.sha256(fh.read()).hexdigest()
    AUDIT_LOG["hashes"][f] = h

print(json.dumps(AUDIT_LOG, indent=2))
```

Every result table is written to disk as `audit/outputs/WP{N}_{table_name}.csv` with a companion `.json` metadata file containing seed, timestamp, and input hashes.

## Prior Verification Reports

The `reports/paper1_verification/` directory contains 13 prior verification reports (00 through 13, including `08_executive_summary_v2.md`). These were produced during an earlier verification pass. **They are NOT assumed trustworthy for this audit.** Marco's pivot-table finding suggests at least one number does not hold. The audit begins from raw CSVs and re-derives everything independently. Prior reports may be consulted for comparison but do not substitute for re-computation.

---

# WP1 — Data Integrity and Panel Reconstruction

**Goal:** verify the analytical dataset exactly reproduces the manuscript's descriptive statistics before any methodological audit begins. **Marco has identified a discrepancy via pivot table — WP1 must locate and characterize this discrepancy.**

**Dependencies:** none
**Blocks:** WP2, WP3

## Pre-Task: Source Integrity

Before any computation, verify data provenance:
- Verify symlinks resolve: `ls -la data/raw/` to confirm targets exist.
- Hash all four raw CSVs (SHA-256) and record in audit log.
- Check whether `data/processed/panel_monthly_counts.parquet` was built from the current raw CSVs or from an older version.

## Tasks

| ID | Task | JQC expected | EDA expected |
|----|------|--------------|--------------|
| 1.1 | Load four CSVs from `data/raw/`, verify schemas and row counts | Total 57,373; NL 34,617; LA 37,379; LD 9,936 | Same (row counts should be identical across papers) |
| 1.2 | Verify person-registrations (sum of `total` column per CSV, ALL rows including sentinels) | 263,402 + 6,105 = 269,507 | 269,507 |
| 1.2b | Verify person-registrations AFTER sentinel exclusion (cvegeo ending 998/999 or == 99998) | Total 263,402; NL 89,631; LA 157,990; LD 15,438 | N/A (EDA does not exclude from national totals) |
| 1.3 | Verify excluded counts — TWO definitions to check | JQC: sentinel geocodes → 6,105 / 2,855 / 2,911 / 339 persons | EDA: "4,141 rows, 3.0%" — verify denominator and meaning of "rows" vs "persons" |
| 1.4 | Verify non-zero cell counts (rows where total > 0, after JQC exclusion) | 55,568 / 33,359 / 36,541 / 9,696 | Not reported in EDA |
| 1.5 | Reconstruct balanced panel: verify unique municipality count | JQC: 2,478 (INEGI frame, zero-infilled) | EDA: 2,025 unique identifiers in data (no infill) |
| 1.6 | Cross-status consistency: sum NL + LA + LD per (cvegeo, year, month) and compare to Total CSV | Document residual; if non-zero, characterize | Same check |
| 1.7 | Verify June 2025 zero-inflation rates | JQC: 77.0% / 85.7% / 84.2% / 96.3% (of 2,478) | EDA: "573 municipalities recorded ≥1 total" → 76.9% zero (of 2,478), consistent |
| 1.8 | Verify female LD mean and zero rate per municipality-month | JQC: 0.0065 per muni-month, 99.4% zero | Not reported in EDA |
| 1.9 | Verify end-of-period reporting lag: Dec 2025 / Jul 2025 ratio per status | JQC: 0.46-0.72 | EDA: 0.45-0.72 (slight difference in lower bound) |
| 1.10 | Temporal coverage: no silent gaps, no duplicate (cvegeo, year, month) rows per CSV | Zero duplicates, 132 unique (year, month) combos | Same |
| 1.11 | Compare panel built from raw CSVs against existing `data/processed/panel_monthly_counts.parquet` | Document any differences | — |
| 1.12 | Cross-reference with existing `reports/paper1_verification/` | Document discrepancies | — |

## Cross-Paper Consistency Check (NEW — critical)

After completing Tasks 1.1–1.12, explicitly reconcile the two papers:

| Check | Expected relationship |
|-------|----------------------|
| EDA total = JQC total + JQC excluded | 269,507 = 263,402 + 6,105 ✓ on paper; verify from data |
| EDA "4,141 rows excluded" vs JQC "6,105 persons excluded" | Different metrics? Rows vs persons? Or different exclusion criteria? MUST resolve |
| EDA 2,025 municipalities vs JQC 2,478 | 2,025 = municipalities with ≥1 registration across all CSVs; 2,478 = INEGI frame. Verify 2,025 from data |
| EDA June 2025 counts (Total 3,098; NL 1,173; LA 1,788; LD 144) vs JQC June 2025 | JQC does not report June 2025 national totals directly, but these should be derivable. Verify match |
| EDA sex composition (Table 1) vs JQC Section 4.1 | JQC: NL 77.9% male, LD 85.9%, LA 49.4%/50.5%. EDA: NL 77.8%, LD 85.8%, LA 49.4%/50.5%. Minor rounding differences — verify from data |
| EDA zero-inflation: 82.5% / 89.4% / 88.6% / 97.0% (full study period) vs JQC June 2025: 77.0% / 85.7% / 84.2% / 96.3% | Different metrics: EDA is full-period average, JQC is June 2025 snapshot. Both valid, verify both |
| EDA reporting lag lower bound 0.45 vs JQC 0.46 | Rounding or data difference? Verify from data |

**If the raw CSVs do not reproduce EITHER paper's numbers, the data has changed since both papers were written and ALL analyses in BOTH papers must be re-run from the current raw CSVs.**

## Pivot-Table Discrepancy and Two-Paper Divergence

Marco identified a discrepancy via manual pivot table. Additionally, the submitted EDA paper and the pre-submission JQC paper report different numbers. The differences in total persons (269,507 vs 263,402) are explained by sentinel-geocode exclusion, but the exclusion counts themselves differ between papers (EDA: "4,141 rows, 3.0%" vs JQC: "6,105 persons, 2.3%"). WP1 must:

1. Establish ground truth from the current raw CSVs — what do they actually contain right now?
2. Determine which paper (if either) matches the current data
3. If neither matches, the data has been updated since both papers were written
4. Characterize the blast radius: which downstream results in each paper are affected?

**Critical path:** if the raw CSVs have changed since the JQC analyses were run, ALL processed outputs in `data/processed/` are stale and the entire pipeline must be re-run before WP2 can proceed. WP2 becomes a verification of the re-run, not a verification of the existing outputs.

**Halt conditions:**
- If the raw CSVs do not match EITHER paper → halt, re-scrape or identify correct data version
- If the raw CSVs match the EDA but not the JQC → the JQC was built on old data; re-run JQC pipeline
- If the raw CSVs match the JQC but not the EDA → the EDA was built on old data; flag for erratum
- If the raw CSVs match both (after accounting for exclusion differences) → proceed normally

## Deliverable
`audit/WP1_data_integrity.md` with a pass/fail table and narrative of any discrepancies.

## Review Gate 1
Marco reviews. Resolve all discrepancies before WP2 begins.

---

# WP2 — Numeric Audit of Reported Results

**Goal:** every number in the manuscript must be traceable to a script output. If WP1 determines the raw data has changed, WP2 verifies the RE-RUN outputs, not the stale processed files.

**Dependencies:** WP1 passed
**Blocks:** WP3

**NOTE:** The EDA paper (submitted) reports slightly different numbers than the JQC paper in several places (sex composition percentages, reporting-lag ratios, zero-inflation rates). Where both papers make a claim about the same metric, WP2 verifies BOTH and documents which is correct. The EDA paper's key numbers for cross-reference:
- Total registrations (incl. sentinels): 269,507
- NL 92,486; LA 160,901; LD 15,777
- June 2025: Total 3,098; NL 1,173; LA 1,788; LD 144
- Sex: NL 77.8% male (cumul), LD 85.8%, LA 49.4%M/50.5%F
- Zero-inflation (full period): 82.5% / 89.4% / 88.6% / 97.0%
- Active municipalities June 2025: Total 573, NL 357, LA 391, LD 91
- Chi-squared sex composition: χ²(2, N=3,105) = 166.30, p < .001, V = 0.23

## Tasks

### 2.1 Concentration (Section 4.2, Table 2)

- Recompute Gini monthly for all 132 months × 4 statuses
- Verify mean/min/max/trend for each status
  - Total: 0.935 / 0.915 / 0.958 / −0.004
  - NL:    0.946 / 0.926 / 0.966 / −0.003
  - LA:    0.955 / 0.935 / 0.978 / −0.004
  - LD:    0.979 / 0.963 / 0.993 / −0.002
- Verify June 2025 concentration counts: 50% of NL in 42 muni (1.7%); 50% of LD in 22 (0.9%); 50% of Total in 48 (1.9%)
- Verify "88.8% zero → 77.0% zero" deconcentration claim

### 2.2 Global Moran's I (Section 4.3.1, Figure 3)

- Recompute for 132 months × 4 statuses, Queen contiguity (fuzzy, 50m buffer), 999 permutations
- Verify significance counts: 132/132, 132/132, 127/132, 122/132
- Verify I means and ranges: Total (0.199, 0.038-0.374); LA (0.187, 0.011-0.401); NL (0.163, 0.043-0.280); LD (0.101, −0.006-0.298)
- Verify trend slopes: +0.019, +0.007, +0.020, +0.005 per year
- Verify LD trend non-significance (p = 0.224)

### 2.3 LISA classification (Table 3, June 2025 total sex)

- Queen contiguity, 999 permutations, α = 0.05, BFS filter (min 3 contiguous HH)
- Verify:
  - Total: HH 106, LL 50, HL 1, LH 62, NS 2259
  - NL: HH 93, LL 2, HL 2, LH 52, NS 2329
  - LA: HH 110, LL 5, HL 35, LH 69, NS 2259
  - LD: HH 35, LL 7, HL 38, LH 105, NS 2293
- Record PySAL random seed; if not reproducible, document drift tolerance (±2 municipalities acceptable per status)

### 2.4 Jaccard pairwise (Table 4)

- Recompute 4×4 HH intersection matrix for June 2025
- Diagonals: 106, 93, 110, 35
- Off-diagonals (intersection counts): Total-NL 71, Total-LA 87, Total-LD 24, NL-LA 56, NL-LD 16, LA-LD 19
- Derive Jaccard coefficients and verify the load-bearing numbers: NL↔LD = 0.143, LA↔LD = 0.151, Total↔LA = 0.674, NL↔LA = 0.381
- Verify Jaccard at June 2015 and June 2020 per Section 4.3.3
  - June 2015: NL↔LD 0.103, LA↔LD 0.000
  - June 2020: NL↔LD 0.164, LA↔LD 0.198

### 2.5 Mann-Whitney U on HH populations (Section 4.3.3, Abstract)

- For June 2025, for each pair of HH sets, test whether municipal populations differ
- Verify claim: "all pairwise p > 0.50"
- Also run Kolmogorov-Smirnov per manuscript

### 2.6 Regional trends (Table 5) — PRIORITY

- Recompute 24 slope estimates (6 regions × 4 statuses) with Newey-West HAC (bw = 12)
- Verify every cell in Table 5 against point estimate and significance star
- Load-bearing: Centro NL +4.96***; Baj´ıo NL +0.50***; Total row across regions
- Record full regression output (coefficient, SE, t, p, N, bandwidth)

### 2.7 Baj´ıo structural break (Section 4.4.3)

- Recompute Chow test at Feb 2017 with full regression diagnostics
- Verify F = 78.13, p < 0.001
- Verify piecewise slopes: β1 = −8.82/yr (pre), β2 = +0.47/yr (post, p = 0.046)
- Verify sub-components: post-break NL +0.50/yr (p < 0.001), LD +0.15/yr (p = 0.046), LA −0.35/yr (p = 0.003), Total −0.31/yr (p = 0.041)

### 2.8 Chi-square bookend tests (Figure 7)

- Recompute Pearson chi-square for June 2015 vs June 2025 regional distribution, per status
- Verify: Total χ² = 9.5, p = 0.050; NL χ² = 16.5, p = 0.002; LA χ² = 17.7, p = 0.001; LD χ² = 14.1, p = 0.007

### 2.9 Sex disaggregation (Table 6)

- Recompute male/female LISA for June 2025
- Verify HH counts: Total M 121 / F 99; NL M 85 / F 50; LA M 83 / F 90; LD M 27 / F 0
- Verify shared counts: 74, 28, 58, 0
- Verify Jaccard: 0.507, 0.262, 0.504, 0.000
- Verify "if female set matched male size, 28 shared = 33%" counterfactual

### 2.10 CED state trajectories (Section 4.6, Figure 9)

- Recompute monthly HH counts for 8 states: Jalisco, Guanajuato, Coahuila, Veracruz, Nayarit, Tabasco, Nuevo León, Estado de México
- Verify quoted slopes:
  - Edomex: NL +2.36/yr (p<0.001), LA +1.81/yr (p<0.001)
  - Nuevo León: LA +1.34/yr (p<0.001), LD +0.80/yr (p<0.001)
  - Guanajuato: NL +0.75/yr (p<0.001), LA −0.57/yr (p<0.001)
- Verify Jalisco registration collapse: 3,825 (2021) → 216 (2024), 103 → 41 municipalities
- Verify Tabasco claim: Female LA 31 muni-months across 6 muni (2023-2025); Male LA 6 muni-months across 4 muni; Male NL 39 vs Female NL 34 muni-months

### 2.11 Temporal stability (Appendix A.1)

- Recompute Spearman rank correlation of local I_i between June 2024 and June 2025 for 12 (status × sex) combinations
- Verify the 12 values in Table A1 (range 0.227 to 0.607)

### 2.12 Abstract and Section 1 counts

- Verify "1,584 LISA runs" (4 × 3 × 132)
- Verify "2,478 municipalities"
- Verify "132 months"
- Verify "263,402 person-registrations" total

### 2.13 VAWRI external validation (Section 3.7, Section 5.5)

- Recompute Mann-Whitney U tests comparing VAWRI in HH vs non-HH at June 2023 cross-section
- Verify rank-biserial effect sizes referenced in Conclusion: 0.76 to 0.96 range

## Deliverable
`audit/WP2_numeric_audit.md` — table with columns: Location | Claim | Manuscript value | Computed value | Status (✅/⚠️/❌) | Notes

Every discrepancy gets a severity: **Trivial** (rounding, third decimal), **Moderate** (first-second decimal, no narrative impact), **Serious** (changes sign or significance), **Fatal** (invalidates a headline claim).

## Review Gate 2
Marco + M-RESEARCH review every ⚠️ and ❌. Decide per item: fix manuscript / re-verify computation / document ambiguity.

---

# WP3 — Methodological Audit and Re-Specification

**Goal:** fix the methodological exposures that a hostile JQC Reviewer 2 will exploit.

**Dependencies:** WP2 passed
**Blocks:** WP6

## Tasks

### 3.1 HH-count trend re-specification (Tier 1 — FATAL if unaddressed)

**Problem:** OLS on bounded non-negative integer counts (HH municipalities per month) with values near zero in some regions violates OLS assumptions. Newey-West fixes autocorrelation but not distributional misspecification.

**Fix:** Re-estimate all 24 region-status trends as:
- (a) Poisson regression with HAC SEs (primary)
- (b) Negative binomial with HAC SEs (robustness, if overdispersion present)
- (c) OLS with Newey-West (retained for comparison)

**Apply Holm-Bonferroni family-wise correction** across the 24 tests. Report both corrected and uncorrected p-values.

**Deliverable:** revised Table 5 with IRR, linear-equivalent slope, uncorrected p, Holm-corrected p. OLS moved to Appendix A.X.

### 3.2 Threshold-sensitivity of HH trends

**Problem:** HH classification at α = 0.05 is noise-sensitive near threshold. Current Appendix A.2 shows June 2025 sensitivity only.

**Fix:** Extend to all 132 months for three regions (Centro, Baj´ıo, Norte) × 4 statuses at α ∈ {0.01, 0.05, 0.10}. Re-estimate trends.

**Load-bearing question:** does the Centro NL +4.96/yr headline survive at α = 0.01?

**Deliverable:** Appendix table with trend slopes at 3 alpha levels; note in Section 4.4.1 if headline qualifies.

### 3.3 Structural break re-specification

**Problem:** Chow test at a single "winning" date after searching a 72-month grid is a specification search. Correct approach: supremum Wald (Andrews 1993) with correct critical values.

**Fix:** Implement supremum Wald over the Jan 2016–Dec 2021 grid. Report sup-W statistic and Andrews 1993 critical values at the sample fraction used. Alternatively: Bai-Perron.

**Outcome path A:** break survives → retain narrative, replace reported statistic
**Outcome path B:** break does not survive → rewrite Baj´ıo section as gradual post-2017 expansion without a break claim

**Deliverable:** revised Section 4.4.3 with correct test.

### 3.4 Jaccard null distribution (Tier 2 — reviewer bait)

**Problem:** Jaccard 0.143 has no reference distribution. A reviewer will ask: "low relative to what?"

**Fix:** Construct a permutation null. For each of 1,000 draws, randomly assign HH status to |HH_A| and |HH_B| municipalities drawn from the 2,478 universe (preserving marginal cluster sizes). Compute Jaccard distribution.

**Deliverable:** observed Jaccard with permutation-based p-value for all 6 pairs. Expected finding: observed 0.143 sits far below the null mean, yielding p ≈ 0.001 — but "strikingly low" becomes a quantified claim.

### 3.5 Population-normalized robustness (Option 2, appendix only)

**Scope:** June 2025 cross-section only. Purpose: preempt reviewer objection.

**Steps:**
- Load CONAPO population from `data/external/conapo_poblacion_1990_2070.parquet` (symlink to pCloudDrive)
- Filter to 2025 projection (or 2020 Census if projections are unreliable at municipal level — verify with Marco)
- Merge with panel by cvegeo
- Compute rate per 100,000 for June 2025, 4 statuses × 3 sexes = 12 series
- Re-run LISA on rates using existing `data/processed/spatial_weights_queen.gal` (same Queen fuzzy contiguity, 999 permutations, α = 0.05, BFS filter)
- Recompute Jaccard matrix on rate-based HH sets
- Compare to count-based Jaccard from Table 4

**Deliverable:** Appendix A.5 with:
- Table: HH counts per status (counts vs rates)
- Table: Jaccard matrix (counts vs rates)
- 1-paragraph narrative: "the non-interchangeability finding is (not) robust to population normalization"

### 3.6 Spatial weights sensitivity

**Scope:** June 2025 only, 4 statuses.

**Steps:**
- Load geoparquet from `data/external/municipios_2024.geoparquet`
- Construct alternative weights: (a) k-nearest neighbors k=4, k=8; (b) distance-band weights at 50km, 100km
- Re-run LISA under each specification
- Compare HH classifications to Queen-based (from `data/processed/spatial_weights_queen.gal`) via Jaccard
- Tabulate in Appendix

**Deliverable:** Appendix A.6 showing HH robustness across 5 weight specifications.

### 3.7 FDR audit

**Current state:** manuscript defends uncorrected α = 0.05 by noting the permutation floor problem. This is reasonable but incomplete.

**Fix:** Run BH-FDR with 9,999 permutations for June 2025 as a one-off demonstration. Report how many HH municipalities survive. If stable, strengthens the defense.

**Deliverable:** 1-paragraph addition to Section 3.3 or Appendix.

### 3.8 Reporting-lag truncation robustness

**Problem:** Trend estimates include partially reported 2025-07 through 2025-12 months.

**Fix:** Re-estimate all primary trends on the 2015-01 to 2025-06 window. Compare headline numbers:
- Centro NL trend (current: +4.96/yr)
- Baj´ıo post-2017 slope (current: +0.47/yr)
- All 24 Table 5 cells

**Deliverable:** Appendix comparison table; note in Section 5.7 which trends shift materially.

## Deliverable (WP3 aggregate)
`audit/WP3_methodological_audit.md` with:
- Summary of every re-specification
- Replacement tables for main text (Table 5 revised)
- New appendix tables (A.3 re-spec sensitivity, A.4 Jaccard null, A.5 rate-based, A.6 weights, A.7 lag truncation)
- Explicit note per task: whether the original finding survives, qualifies, or fails

## Review Gate 3
Marco + M-RESEARCH decide: main text vs appendix placement for each re-specification. I will argue for Poisson trends in main text.

---

# WP4 — Reference Audit

**Goal:** every citation verified against the actual source.

**Dependencies:** none (runs in parallel with WP3)
**Blocks:** WP6

## Tasks

### 4.1 Citation map
For each of the 42 references, list every sentence in the manuscript that invokes it. Build as `audit/citation_map.csv`.

### 4.2 Priority deep-verification (misrepresentation risk)

| Ref | Claim to verify | Method |
|-----|-----------------|--------|
| [2] CED Article 34 | "Eightfold increase since 2017" attribution to Guanajuato; 8-state list; April 2026 referral date; "crimes against humanity... different moments... different parts of the territory" | Read `CED_C_MEX_A-34_D_1_69218_S__2_.docx` (project knowledge) and `CED_C_MEX_VR.pdf` (project, for ref [39]) |
| [7] Prieto-Curiel et al. | 160,000-185,000 cartel members; 350-370/week recruitment | Fetch Science 2023 article |
| [8] Cadena Vargas & Garrocho | 2,458 municipalities; could not disaggregate outcomes (because RNPED did not distinguish); covered 2006-2017 | Fetch Papeles de Población 2019 |
| [10] Das et al. | Spatial spillover of organized crime violence into public health | PDF in project: `Das_et_al___2025__The_Mexican_drug_war_Homicides_and_deaths_of_despair_2000_2020.pdf` |
| [14] García-Castillo | 19 of 732 investigations reached court | Fetch |
| [15] Guevara Bermúdez | 9 convictions | Fetch |
| [26] Weisburd 2015 | 50% of crime in 4-6% of micro-geographic units (street segments) | Fetch Criminology 2015 |
| [30] Andresen 2006 | Counts vs rates produce different hotspot geographies | Fetch BJC 2006 |
| [31] Braga et al. 2017 | Crime-type disaggregation matters | Fetch JQC 2017 |
| [11] Atuesta & González | Disappearance patterns linked to trafficking routes; Durango/Tamaulipas/Coahuila | Fetch Trends in Organized Crime 2024 |
| [25] Anselin 1995 | Correct attribution of LISA formula | Verify formula matches |
| [27] Newey-West 1987 | Correct attribution | Verify |

### 4.3 Unresolved citations
- Section 5.2 contains `[? ]` after "fuel infrastructure and territorial control". Verify this resolves to [29] (Reyes Guzmán et al. 2022, already cited earlier in same section 4.4.3).
- Verify both "Authors (2026)" placeholders in Data/Code availability — ensure they correctly anonymize the data paper and code repo for double-blind review (if JQC uses double-blind).

### 4.4 EDA Paper Cross-Consistency (NEW)

The submitted EDA paper makes claims that must be consistent with the JQC paper since both use the same underlying dataset. Verify:
- CED "eightfold increase since 2017" — EDA Section 3.3 says Guanajuato June 2025 (157) is below June 2015 (181), "confines [CED finding] to a specific temporal window." JQC Section 5.3 makes the same claim. Verify both from data.
- 19/732 investigations, 9 convictions — cited in both papers. Verify against García-Castillo and Guevara Bermúdez.
- EDA cites Gobierno de México (2026) rejection — verify this source exists and is accurately characterized.
- EDA's Tabasco female-anomalous claim (70.6% female LA in 2015, 85.2% in 2018) — verify from data; check consistency with JQC Section 4.6 Tabasco discussion.
- EDA's Located Dead OLS post-2019: β = 0.11/month (SE = 0.13, p = .43), M = 145, SD = 21 — verify from data.
- EDA's chi-squared: χ²(2, N=3,105) = 166.30, p < .001, V = 0.23 — verify from data.

### 4.5 Self-citations (light touch per Marco's instruction)
- [13] Escobar et al. VAWRI — confirm title, journal, year match; confirm methodology referenced in Section 3.7 matches actual VAWRI construction
- [19] Data paper — confirm existence and OSF DOI

### 4.5 Missing citation scan
Methodological claims that currently lack citation support:
- "Newey-West HAC bandwidth = 12 corresponding to one year of seasonal periodicity" — cite Andrews 1991 for bandwidth selection, or document as ad-hoc choice
- Supremum Wald test (if adopted in WP3.3) — cite Andrews 1993
- Holm-Bonferroni (if adopted) — cite Holm 1979
- Mann-Whitney rank-biserial effect size (Section 3.7) — Kerby 2014 is cited, verify correctness
- Jaccard permutation null (if adopted in WP3.4) — no standard citation needed but document procedure

### 4.6 Bibtex hygiene
- Check `manuscript/references.bib` for consistency with in-text citations across `manuscript/sections/*.tex`
- Flag any references in .bib not cited in manuscript, or cited in manuscript but missing from .bib
- Cross-reference with project-level `references.bib` (root) if it exists and differs

## Deliverable
`audit/WP4_reference_audit.md` with per-citation status: verified / misrepresented / ambiguous / unresolved / missing.

## Review Gate 4
Marco reviews flags. Any misrepresentation fixed before submission.

---

# WP5 — Discussion and Introduction Fact-Check

**Goal:** locate interpretive overreach and misrepresentation.

**Dependencies:** none (runs in parallel with WP3)
**Blocks:** WP6

## Tasks

### 5.1 Claim classification
For each sentence in `manuscript/sections/introduction.tex`, `discussion.tex`, and `conclusion.tex`, classify as:
- **(a) Direct empirical finding from our data** → must match Results section exactly
- **(b) Restatement of cited literature** → must match source per WP4
- **(c) Interpretive hypothesis** → must be explicitly labeled as hypothesis

Build as `audit/claim_ledger.csv`.

### 5.2 Priority claims for scrutiny

| Section | Claim | Audit question |
|---------|-------|-----------------|
| Abstract, Intro | "First outcome-disaggregated spatial analysis" | Literature search confirms no prior work disaggregates NL/LA/LD |
| Section 5.2 | "Centro expansion went undetected in annual analyses" | Does Cadena Vargas & Garrocho 2019 cover Centro? If yes, reword |
| Section 5.2 | Three competing hypotheses for Centro | All three are properly hedged as hypotheses? |
| Section 5.2 | "Intensification of cartel competition in Guanajuato's industrial municipalities, particularly around fuel infrastructure" | Supported by cited source [29]? |
| Section 5.2 | "Institutional anticipation effects and state-level pilot programs cannot be ruled out" for Feb 2017 break | This is speculation — verify it is framed as such |
| Section 5.3 | "First national-scale quantitative evidence bearing on CED's characterization" | Any prior quantitative work on the CED findings? |
| Section 5.4 | Two mechanisms proposed for Located Alive near-parity | Hedged as hypotheses? |
| Section 5.5 | "VAWRI comparison confirms HH coincide with elevated violence" | Effect sizes and p-values in Section 4 / Appendix support this? |
| Section 5.6 | "Institutional reforms... coincide with the largest expansion" | Temporal alignment verified; causal language avoided? |
| Section 6 | "One operational implication follows: forensic resources should follow LD; search programs should follow NL" | Is this framed as an implication of the descriptive finding, not a causal claim? |

### 5.3 Causal-language sweep

Flag every instance in Sections 1, 5, 6 of: "drivers", "caused by", "because", "reflects", "due to", "results from", "explains". For each, decide: (a) acceptable descriptive use, (b) rewrite to hedge, (c) remove.

### 5.4 Registration-vs-incidence conflation sweep

The manuscript mostly handles this carefully but a line-by-line pass is needed. Any claim about "disappearances" that should be "registered disappearances" must be flagged.

### 5.5 Introduction literature-coverage check

- Baptista & Dávila Cervantes [9] is cited but the manuscript does not engage with their spatial zero-inflated Poisson methodology. Either engage (argue why LISA is appropriate instead) or cut the cite.
- No engagement with broader crime-concentration literature beyond Weisburd [26] and Braga et al. [31]. Verify whether additional engagement is needed for JQC's readership.

### 5.6 Conclusion audit

Section 6 lists "five empirical findings." Each must match the Results section exactly (same magnitudes, same p-values, same caveats). Recheck after WP2 completes.

## Deliverable
`audit/WP5_discussion_factcheck.md` with every flagged sentence, proposed revision, and rationale.

## Review Gate 5
Marco + M-RESEARCH walk through every flag.

---

# WP6 — Consolidation and Revision Memo

**Goal:** single prioritized action list.

**Dependencies:** WP1–WP5 complete

## Tasks

### 6.1 Merge outputs into `audit/revision_memo.md`

Three sections:
- **MUST FIX BEFORE SUBMISSION** — fatal flaws, misrepresentations, numerical errors with narrative impact
- **SHOULD FIX BEFORE SUBMISSION** — reviewer-bait, robustness gaps, unhedged claims
- **COULD FIX OR DEFEND IN LIMITATIONS** — minor issues, stylistic concerns

### 6.2 Per-item spec

Each item has: manuscript location | issue description | proposed fix | estimated effort (hours) | risk-to-Q1-acceptance if unfixed (low/medium/high).

### 6.3 Restructuring check

If re-specifications (WP3) force main-text changes beyond Table 5 replacement, propose revised manuscript outline.

### 6.4 Reviewer-proofing paragraph

Draft a defense anticipating the three most likely Reviewer 2 objections:
- "Why not population-normalized rates?" → defense + Appendix A.5 pointer
- "Why OLS on counts?" → defense via Poisson robustness in Appendix
- "Why no FDR correction?" → defense via permutation floor + BFS filter + Appendix BH demonstration

### 6.5 Cross-check revised numbers against manuscript

Every number changed by the audit must be updated consistently across:
- Abstract
- Results sections
- Discussion
- Conclusion
- Appendix
- Figure captions
- Table notes

Build `audit/number_update_tracker.csv` listing every manuscript number with old value, new value, and all locations where it appears.

## Deliverable
`audit/revision_memo.md` — final action document.

## Review Gate 6
Final sync before revision writing begins.

---

# Execution Order and Sequencing

```
WP1 ──▶ GATE 1 ──▶ WP2 ──▶ GATE 2 ──┬──▶ WP3 ──▶ GATE 3 ──┐
                                    │                      │
                                    ├──▶ WP4 ──▶ GATE 4 ──┤
                                    │                      │
                                    └──▶ WP5 ──▶ GATE 5 ──┴──▶ WP6 ──▶ GATE 6
```

WP3, WP4, WP5 run in parallel after Gate 2.

---

# Session Cadence

Each Claude Code session:
1. Run one WP (or one task within a large WP)
2. Produce its markdown report
3. Commit: `git commit -m "audit(WP{N}.{task}): {description}"`
4. Marco pastes the report into the M-RESEARCH chat for review

I will return per-task verdicts in this format:

```
Task X.Y
Verdict: ✅ Pass / ⚠️ Qualify / ❌ Fail
Action: [specific instruction]
```

---

# Stop Conditions

Halt the audit and consult M-RESEARCH if:
- Any WP1 numeric check fails by more than 2% (panel integrity issue)
- Any WP2 load-bearing number (Jaccard 0.143, Centro +4.96, Gini means) diverges by more than rounding
- Any WP3 re-specification flips a significance sign
- Any WP4 citation check reveals misrepresentation
- Any WP5 claim is unsupported by data

---

# Environment and Tooling

- **Root:** `/home/marco/workspace/work/rnpdno-population-bands/`
- Python 3.10, Anaconda env `rnpdno_eda`
- Polars (data), Pandas (GIS only), GeoPandas, PySAL/esda, libpysal
- Statistical: statsmodels (HAC SE, Poisson), scipy.stats
- Reproducibility: fixed seeds, git commit hashes in every report
- Code style: follow project conventions
- **No code changes to existing analysis modules without Marco's explicit approval (per Global Code Change Consent Policy in userPreferences §3).** Audit notebooks are NEW files in `notebooks/audit/`; existing scripts in `scripts/` are READ-ONLY until gate approval.

## Existing Pipeline Scripts (READ-ONLY, audit reference)

| Script | Purpose | Key output |
|--------|---------|------------|
| `scripts/01_build_master_panel.py` | Initial panel construction | (superseded by 10?) |
| `scripts/10_build_monthly_panel.py` | Monthly panel rebuild | `data/processed/panel_monthly_counts.parquet` |
| `scripts/11_build_spatial_weights.py` | Queen contiguity weights | `data/processed/spatial_weights_queen.gal` |
| `scripts/12_compute_lisa_monthly.py` | 1,584 LISA runs | `data/processed/lisa_monthly_results.parquet` |
| `scripts/13_compute_concentration.py` | Gini/HHI monthly | `data/processed/concentration_monthly.csv` |
| `scripts/14_generate_figures.py` | Manuscript figures | `manuscript/figures/` |
| `scripts/15_generate_tables.py` | Manuscript tables | `manuscript/tables/` |
| `scripts/run_pipeline.py` | Orchestrator | runs all above |
| `rnpdno_eda/models/spatial.py` | Core spatial routines | imported by scripts |

The audit notebooks must NOT import from or modify these scripts. They re-derive from raw data independently.

## Existing Processed Outputs (audit will compare against these)

| File | Contents |
|------|----------|
| `data/processed/panel_monthly_counts.parquet` | Balanced panel used in all analyses |
| `data/processed/lisa_monthly_results.parquet` | All LISA classifications (1,584 runs) |
| `data/processed/hh_clusters_monthly.parquet` | HH cluster counts by region/month |
| `data/processed/morans_i_monthly.csv` | Global Moran's I series |
| `data/processed/concentration_monthly.csv` | Gini/HHI series |
| `data/processed/municipality_classification_v2.csv` | Regional assignments |
| `data/processed/bajio_corridor_hh_timeseries.csv` | Bajío-specific HH series |
| `data/processed/ced_state_hh_timeseries.csv` | CED state HH series |

WP2 will compare fresh computations against these files. Any divergence triggers investigation.

## CED Decision Document

The CED Article 34 decision [reference 2] is available as:
- Project knowledge file: `CED_C_MEX_A-34_D_1_69218_S__2_.docx`
- Also in project: `CED_C_MEX_VR.pdf` (the Article 33 visit report, reference [39])

WP4 uses these for citation verification.

## VAWRI Data

Marco confirms available. Location to be specified at WP2 execution (likely in pCloudDrive or a separate project). Ask Marco for exact path before running Task 2.13.

---

**END OF PLAN**
