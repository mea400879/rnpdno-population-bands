# 01 — Municipality Reconciliation

## Counts

- Panel unique cvegeo: **2,478**
- Spatial weights (GAL): **2,478**
- Shapefile (geoparquet): **2,478**

## Agreement

- Panel == Weights: **True**
- Panel == Shapefile: **True**
- All three agree at N=2,478: **True**

## Islands

- Island municipalities (zero neighbors): **0**
- Method: fuzzy_contiguity(buffer=50m) on EPSG:6372

## Sentinels

- Sentinel rows in panel: **0**
- Sentinels excluded: **YES**

## Panel-only municipalities (not in shapefile)

- None

## Shapefile-only municipalities (not in panel)

- None