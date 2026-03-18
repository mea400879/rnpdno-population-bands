# Phase 1 — Municipality Reconciliation

## Study Period
**Jan 2015 – Dec 2025, 132 months**

## Spatial Coverage

| Source | N |
|--------|---|
| Spatial weights matrix (GAL) | 2478 |
| Panel (unique cvegeo) | 2478 |
| Municipality classification v2 | 2478 |
| Shapefile polygons (municipios_2024.geoparquet) | 2478 |
| Island municipalities (no queen neighbours) | 52 |

**Mismatches between panel and GAL:** 0 (verified)

## Island Municipalities (52)

Islands are municipalities with zero queen-contiguity neighbours and are excluded from LISA significance computation. Their cluster_label is always NS regardless of local I value.

Full list stored in: `data/processed/island_municipalities.csv`

## All-Zero Municipality Counts (full 132-month period)

A municipality is "all-zero" if its cumulative count equals zero across all 132 months.

| Status | Status Name | All-Zero Municipalities | % of 2478 |
|--------|-------------|------------------------|-----------|
| 0 | Total | 523 | 21.1% |
| 7 | Not Located | 766 | 30.9% |
| 2 | Located Alive | 712 | 28.7% |
| 3 | Located Dead | 1280 | 51.7% |

Note: Located Dead has the highest zero-inflation (~52% of municipalities never recorded a located dead person over the full study period).

## Panel Structure Verification

- **Total rows:** 1,308,384 (expected 2,478 x 4 statuses x 132 months = 1,308,384) PASS
- **Years:** 2015 - 2025
- **Months:** 1 - 12
- **Status IDs present:** [0, 2, 3, 7]
- **Regions:** Centro, Centro-Norte, Norte, Norte-Occidente, Sur
- **Panel vs GAL mismatches:** 0

## Data Integrity Summary

All checks pass. The analytical sample is exactly **N = 2,478 municipalities** observed over **132 months (Jan 2015 - Dec 2025)**, with spatial weights verified against the GAL file.
