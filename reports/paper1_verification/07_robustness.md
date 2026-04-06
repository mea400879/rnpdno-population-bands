# 07 — Robustness Checks

## 1. Temporal Stability of Local Moran's I (Jun 2024 vs Jun 2025)

Spearman rank correlation of local_i values between consecutive June cross-sections.

| Status | Sex | Spearman ρ | p-value |
|--------|-----|-----------|---------|
| Total | total | 0.6070 | 0.0000* |
| Total | male | 0.5261 | 0.0000* |
| Total | female | 0.4850 | 0.0000* |
| Not Located | total | 0.3338 | 0.0000* |
| Not Located | male | 0.3050 | 0.0000* |
| Not Located | female | 0.3549 | 0.0000* |
| Located Alive | total | 0.5396 | 0.0000* |
| Located Alive | male | 0.4935 | 0.0000* |
| Located Alive | female | 0.4335 | 0.0000* |
| Located Dead | total | 0.2486 | 0.0000* |
| Located Dead | male | 0.2266 | 0.0000* |
| Located Dead | female | 0.3025 | 0.0000* |

## 2. Permutation Sensitivity (Jun 2025, sex=total)

HH municipality counts at different significance thresholds (all use 999 permutations).

| Status | α=0.05 HH | α=0.01 HH | α=0.001 HH | Retention 0.01/0.05 |
|--------|-----------|-----------|------------|---------------------|
| Total | 106 | 48 | 0 | 45% |
| Not Located | 93 | 46 | 0 | 49% |
| Located Alive | 110 | 36 | 0 | 33% |
| Located Dead | 35 | 12 | 0 | 34% |

## 3. Global Moran's I Significance Summary

Proportion of 132 months with significant (p<0.05) global Moran's I.

| Status | Significant | Total | % Significant |
|--------|-------------|-------|---------------|
| Total | 132 | 132 | 100.0% |
| Not Located | 132 | 132 | 100.0% |
| Located Alive | 127 | 132 | 96.2% |
| Located Dead | 122 | 132 | 92.4% |

## 4. Island Municipalities

Island municipalities (zero neighbors): **0**

No island municipalities — `fuzzy_contiguity(buffer=50m)` successfully closes all geometry gaps.

## 5. Spatial Weights Summary

- Method: `fuzzy_contiguity(buffering=True, buffer=50)`
- Transform: row-standardized
- CRS: EPSG:6372 (projected, metres)
- Buffer rationale: closes sub-metre geometry precision gaps in source geoparquet
- Prior method (Queen.from_dataframe) produced 52 false islands
