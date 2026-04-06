# Claude Code Task: Pipeline Verification & Data Summaries for JQC Paper

**Context:** Marco is preparing a JQC manuscript on outcome-disaggregated spatial dynamics of disappearances in Mexico (2015–2025). A hostile peer review of the current draft and blueprint has identified specific data gaps that must be resolved before the paper can be structured. This task generates all required summaries from existing pipeline outputs.

**Environment:** `/home/marco/workspace/work/rnpdno-populations-bands/`
**Stack:** Polars (mandatory), Python 3.10, PySAL, Geopandas
**Output:** All summaries written to `reports/paper1_verification/` as markdown + CSV.

---

## PHASE 0 — Inventory Existing Pipeline Outputs

Before computing anything, catalog what already exists.

```
Task 0.1: List all files in data/processed/, data/interim/, and reports/
          with file sizes and modification dates.
          Write inventory to reports/paper1_verification/00_inventory.md
```

```
Task 0.2: For each parquet/CSV file found, print:
          - Column names and dtypes
          - Row count
          - Date range (if year/month columns exist)
          - Unique values for categorical columns (status_id, region, sex, etc.)
          Write schema summary to reports/paper1_verification/00_schemas.md
```

**Do not proceed past Phase 0 without showing Marco the inventory. Ask for approval.**

---

## PHASE 1 — Municipality Count Reconciliation

The tex file uses n=2,478. The blueprint says 2,475. The pipeline prompt says ~2,422. These must be reconciled.

```
Task 1.1: From the spatial weights file (spatial_weights_queen.gal or .pkl),
          report:
          - Total number of municipalities in the weights matrix
          - Number of island municipalities (zero neighbors)
          - List the island municipality cvegeo codes

Task 1.2: From panel_monthly_counts.parquet (or equivalent panel file),
          report:
          - Number of unique cvegeo values
          - Number of cvegeo values with ALL-ZERO counts across all 132 months
            (for each status_id separately)
          - Number of cvegeo values that appear in the panel but NOT in the
            spatial weights matrix (and vice versa)

Task 1.3: From the INEGI shapefile, report:
          - Total polygon count
          - CRS/projection (must be EPSG:6372)
          - Number of polygons that match panel cvegeo codes

Task 1.4: Write reconciliation summary:
          "The spatial weights matrix covers N municipalities.
           The panel contains M unique municipalities.
           The shapefile has P polygons.
           After excluding Q sentinel geocodes, the analytical sample is R.
           S island municipalities have zero Queen neighbors."
          → reports/paper1_verification/01_municipality_reconciliation.md
```

---

## PHASE 2 — Annual vs. Monthly Pipeline Comparison

The annual pipeline (scripts 07–09) and monthly pipeline produced different regional narratives. The Centro expansion finding appears in monthly but not annual results. This must be understood.

```
Task 2.1: From the MONTHLY pipeline outputs, extract for each
          (region, status_id) combination:
          - OLS slope of HH municipality count over time
            (convert to municipalities/year: slope × 12)
          - Standard error (use Newey-West HAC with bandwidth=12 if possible,
            otherwise HC3)
          - p-value
          - t-statistic
          Include ALL 5 regions × 4 statuses = 20 combinations.
          Also include Bajío sub-flag separately (5 sub-regions × 4 statuses
          if Bajío is flagged in the panel).

Task 2.2: From the ANNUAL pipeline outputs (if they exist as separate files),
          extract the same metrics. If annual outputs don't exist as files,
          aggregate monthly HH counts to annual (sum or mean — document which)
          and recompute OLS slopes.

Task 2.3: Create comparison table:
          | Region | Status | Monthly slope | Monthly p | Annual slope | Annual p | Discrepancy? |
          Flag any row where the sign differs or one is significant and the
          other is not.

Task 2.4: Specifically for CENTRO region:
          - Report the monthly HH count time series (132 values) for each status
          - Plot or describe: is the Centro expansion driven by a few months or
            is it a sustained trend?
          - Report the annual HH count time series (11 values) for each status
          - Is Centro significant at annual resolution? If not, why?
            (likely answer: annual aggregation masks within-year variation,
            or the trend is too recent to show in 11 data points)

          → reports/paper1_verification/02_annual_vs_monthly.md
          → reports/paper1_verification/02_annual_vs_monthly.csv (the full table)
```

---

## PHASE 3 — Core Paper Metrics (RQ1: Concentration)

```
Task 3.1: From concentration_monthly.csv (or compute from panel),
          report for each status_id:
          - Gini coefficient: min, max, mean, std across 132 months
          - HHI: min, max, mean, std across 132 months
          - Is there a significant trend in Gini over time? (OLS slope + p-value)

Task 3.2: For three reference periods (Jan 2015, Jan 2020, Dec 2024),
          report for each status_id:
          - What percentage of municipalities account for 50% of cases?
          - What percentage of municipalities have zero cases?
          - Gini and HHI values

Task 3.3: How does concentration compare to Weisburd's "law of crime
          concentration" benchmarks?
          Weisburd (2015): ~50% of crime in 4-6% of places.
          Report: for each status, what % of municipalities contain 50% of cases
          in Dec 2024?

          → reports/paper1_verification/03_concentration.md
          → reports/paper1_verification/03_concentration.csv
```

---

## PHASE 4 — Core Paper Metrics (RQ2: Clustering & Non-Interchangeability)

This is the paper's headline result.

```
Task 4.1: From morans_i_monthly.csv, report for each status_id:
          - Number of months where Moran's I is significant at p < 0.05
            (out of 132)
          - Range of Moran's I values
          - Is there a trend in Moran's I over time? (OLS slope + p)

Task 4.2: From lisa_monthly_results.parquet (or equivalent), for Dec 2024
          (year=2024, month=12), report LISA classification counts for each
          status_id (total sex):
          | Status | HH | LL | HL | LH | NS |

Task 4.3: CRITICAL — Cross-tabulation and Jaccard.
          For Dec 2024, using total sex:
          - For each pair of statuses (6 pairs from 4 statuses), compute:
            * Number of municipalities that are HH in BOTH statuses
            * Jaccard index: |A ∩ B| / |A ∪ B|
          - Present as matrix:
            |           | Total HH | Not Located HH | Located Alive HH | Located Dead HH |
            |-----------|----------|-----------------|------------------|-----------------|
            | Total     | [n]      | [overlap/Jaccard] | ...            | ...             |
            | Not Loc   |          | [n]             | ...              | ...             |
            | Loc Alive |          |                 | [n]              | ...             |
            | Loc Dead  |          |                 |                  | [n]             |

          THE JACCARD VALUES ARE THE SINGLE MOST IMPORTANT NUMBERS IN THE PAPER.
          If all Jaccard > 0.6, the non-interchangeability argument is weak.
          If Jaccard < 0.3 for most pairs, the argument is strong.

Task 4.4: Repeat Task 4.3 for Jan 2015 and Jan 2020 to show the
          non-interchangeability is not a single-period artifact.

Task 4.5: From hh_clusters_monthly.parquet (connected components, min size=3),
          report for Dec 2024:
          - Number of HH clusters per status
          - Size distribution (min, max, mean municipalities per cluster)
          - Geographic location of largest cluster per status (list municipality names)

          → reports/paper1_verification/04_clustering.md
          → reports/paper1_verification/04_jaccard_matrix.csv
```

---

## PHASE 5 — Core Paper Metrics (RQ3: Temporal Dynamics)

```
Task 5.1: From hh_regional_composition.csv, report for each status_id,
          for Dec 2015 vs Dec 2024:
          - Number of HH municipalities in each of the 5 regions
          - Percentage share by region
          - χ² test: is the regional distribution significantly different
            between 2015 and 2024?

Task 5.2: The three key narratives — provide specific numbers:

          NORTE CONSOLIDATION:
          - HH municipalities in Norte, Dec 2015 vs Dec 2024, for each status
          - Slope (municipalities/year) with p-value

          BAJÍO TRAJECTORY:
          - HH municipalities in Bajío, Dec 2015 vs Dec 2024, for each status
          - Slope with p-value
          - Is the "rising Bajío" hypothesis supported or rejected?

          CENTRO EXPANSION:
          - HH municipalities in Centro, Dec 2015 vs Dec 2024, for each status
          - Slope with p-value
          - When did the Centro expansion begin? (visual inspection of time series)

          → reports/paper1_verification/05_temporal_dynamics.md
          → reports/paper1_verification/05_trend_slopes.csv
```

---

## PHASE 6 — Sex Disaggregation (RQ4)

```
Task 6.1: From the panel or LISA outputs, report aggregate sex composition
          for each status_id across the full study period:
          | Status | Male % | Female % | Undefined % | Total persons |

Task 6.2: For Dec 2024, run or extract LISA for male and female counts
          separately, for status_id = 7 (Not Located) and status_id = 3
          (Located Dead). Report:
          | Status | Sex    | HH count | LL count |
          |--------|--------|----------|----------|
          | 7      | Male   |          |          |
          | 7      | Female |          |          |
          | 3      | Male   |          |          |
          | 3      | Female |          |          |

Task 6.3: Compute overlap between male and female HH sets:
          For Not Located: how many municipalities are HH-male AND HH-female?
          Jaccard index for male vs female HH sets, per status.

Task 6.4: For Located Alive (status_id=2), the near-parity (49% male)
          is a key finding. Report:
          - Male vs female HH municipality counts
          - Are the HH municipalities the SAME for male and female,
            or do they diverge geographically?

Task 6.5: Flag statistical power concern:
          - For female Located Dead: how many total female persons across
            the full study period?
          - What is the mean monthly female Located Dead count per municipality?
          - If it's < 0.1/month in most municipalities, LISA has no power
            to detect clusters. Report this honestly.

          → reports/paper1_verification/06_sex_disaggregation.md
```

---

## PHASE 7 — Robustness Checks for Appendix

```
Task 7.1: REFERENCE PERIOD SENSITIVITY
          Repeat the Jaccard matrix (Phase 4, Task 4.3) for:
          - June 2024
          - December 2023
          Compute Spearman rank correlation of municipal LISA classifications
          between Dec 2024 and each alternative period.
          Are the HH sets stable across reference periods?

Task 7.2: ISLAND MUNICIPALITIES
          Re-run LISA for Dec 2024 (all 4 statuses, total sex) EXCLUDING
          the 52-53 island municipalities.
          Report: change in Moran's I and HH counts.
          Is any key finding sensitive to island inclusion?

Task 7.3: ZERO-INFLATION DIAGNOSTIC
          For each status_id, report:
          - Percentage of municipality-month cells that are zero
          - Percentage of municipalities that are ALL-ZERO across all 132 months
          - Does zero-inflation differ by region?

          → reports/paper1_verification/07_robustness.md
```

---

## PHASE 8 — Executive Summary for Paper Structuring

```
Task 8.1: Compile a single executive summary file that answers these
          questions in 1-2 sentences each, with exact numbers:

          1. How many municipalities in the analytical sample?
          2. What is the Jaccard index between Not Located and Located Dead
             HH sets in Dec 2024? (headline number)
          3. Which region has the largest positive HH trend slope for each status?
          4. Is the "rising Bajío" hypothesis supported? (yes/no + key number)
          5. Does Centro show significant HH expansion? At monthly resolution?
             At annual?
          6. What percentage of municipalities account for 50% of Not Located
             cases in Dec 2024?
          7. Are male and female HH sets geographically distinct for
             Not Located? (Jaccard value)
          8. Is there a statistical power problem for female Located Dead LISA?
          9. Are key findings robust to reference period (Dec 2024 vs June 2024)?
          10. How many LISA runs were performed in total?

          → reports/paper1_verification/08_executive_summary.md
```

---

## EXECUTION RULES

1. **Polars first.** No Pandas unless interfacing with Geopandas/PySAL.
2. **Do not modify any existing pipeline files.** Read-only access to data/ and existing outputs.
3. **All new outputs go to `reports/paper1_verification/`.** Create this directory.
4. **Show Phase 0 inventory to Marco before proceeding.** Wait for approval.
5. **If a required file does not exist**, report what's missing and what would need to be computed. Do not silently substitute or approximate.
6. **Report ALL results including non-significant ones.** No cherry-picking.
7. **Use EPSG:6372** for any spatial computation.
8. **Newey-West HAC standard errors** (bandwidth=12) for all OLS trend regressions on monthly data. If statsmodels is not available, use HC3 and flag.
9. **Git commit** the reports directory when each phase completes. Use descriptive commit messages.
10. **Total estimated effort:** 2–4 hours of computation + reporting.
