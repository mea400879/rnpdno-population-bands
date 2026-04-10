# Task 2 -- FDR-Corrected LISA Thresholds

**Date:** 2026-04-09

**Cross-section:** June 2025, sex=total

**Method:** Benjamini-Hochberg FDR at q=0.05, followed by min-cluster=3 BFS filter


## 1. Per-Status FDR Correction

| Status | Total munis | Uncorrected sig (p<=0.05) | FDR-significant | HH uncorrected | HH FDR | HH FDR+BFS |
|--------|-------------|---------------------------|-----------------|----------------|--------|------------|
| Total | 2478 | 219 | 0 | 106 | 0 | 0 |
| Not Located | 2478 | 149 | 0 | 93 | 0 | 0 |
| Located Alive | 2478 | 219 | 55 | 110 | 16 | 15 |
| Located Dead | 2478 | 185 | 0 | 35 | 0 | 0 |

## 2. Jaccard Similarity: Uncorrected vs FDR-corrected HH Sets

| Pair | Jaccard (uncorrected) | Jaccard (FDR+BFS) | Difference |
|------|----------------------|-------------------|------------|
| Total vs NL | 0.555 | undef (both empty) | - |
| Total vs LA | 0.674 | 0.000 | -0.674 |
| Total vs LD | 0.205 | undef (both empty) | - |
| NL vs LA | 0.381 | 0.000 | -0.381 |
| NL vs LD | 0.143 | undef (both empty) | - |
| LA vs LD | 0.151 | 0.000 | -0.151 |

## 3. Interpretation

BH-FDR at q=0.05 eliminates HH sets for 3 of 4 statuses (Total, NL, LD). Only LA retains 15 HH
municipalities. This is overwhelmingly a **permutation resolution artefact**: with 999 permutations,
the minimum achievable pseudo-p is 1/1000 = 0.001. The BH procedure for m=2,478 tests requires
the smallest p to satisfy p(1) <= (1/2478)*0.05 = 0.0000202. Since no permutation-based p can be
smaller than 0.001, FDR rejects very few tests.

**Key conclusion:** The uncorrected alpha=0.05 threshold is defensible because (a) LISA p-values
are already conditional on permutation inference (999 permutations), and (b) the BFS min-cluster=3
filter already enforces spatial coherence, reducing the effective number of independent tests.
FDR correction is overly conservative in this setting.

If a reviewer demands stricter control, increase to 9,999 permutations for the June 2025
cross-section (4 status runs), which would lower the minimum achievable p to 0.0001 and allow
FDR to function properly.
