# Script Summary — RNPDNO Population Bands

## Scripts 01–09: Legacy Annual Pipeline (`.venv`, Python 3.13)

These scripts are **no longer part of the active pipeline**. Scripts 10–15 supersede them with monthly granularity, multi-status support, and sex disaggregation. The only output still consumed by the active pipeline is `municipality_classification_v2.csv` (from script 08).

| # | File | Purpose | Inputs | Outputs | Methods | Runtime |
|---|------|---------|--------|---------|---------|---------|
| 01 | `01_build_master_panel.py` | Merge RNPDNO counts with CONAPO population; assign population bands; compute rates | `rnpdno_total.csv`, `conapo_poblacion_1990_2070.parquet` | `master_panel.parquet` | Linear interpolation, 5-tier band assignment | seconds |
| 02 | `02_analyze_divergence.py` | Compare top-100 burden vs top-100 risk municipalities | `master_panel.parquet` | Console only | Jaccard similarity | seconds |
| 03 | `03_annual_rates.py` | Aggregate monthly panel to annual rates per municipality | `master_panel.parquet` | `annual_rates.parquet` | Annual groupby, rate per 100k | seconds |
| 04 | `04_annual_lisa.py` | LISA for each year 2015–2024 (10 runs) | `annual_rates.parquet`, municipios geometry | `lisa_annual_summary.csv`, `lisa_annual_clusters.parquet` | LISA (999 perms, alpha=0.05), Queen contiguity | seconds |
| 05 | `05_centroid_trajectory.py` | Track geographic centroid of HH clusters over time | `lisa_annual_clusters.parquet`, municipios geometry | `hotspot_centroids.csv` | Unary union, centroid, displacement | seconds |
| 06 | `06_test_shift_significance.py` | Test significance of centroid drift | `hotspot_centroids.csv` | `shift_significance.csv` | Linear regression, Mann-Kendall | seconds |
| 07 | `07_bajio_regional_clusters.py` | Classify municipalities by region/Bajio; extract HH connected components | AGEEML catalog, LISA clusters, municipios geometry | `bajio_cvegeo_list.csv`, `municipality_classification.csv`, `hh_clusters_by_year.csv`, `cluster_region_trend.csv` | BFS connected components, fuzzy name matching, chi-square | minutes |
| 08 | `08_full_analysis.py` | Multi-status LISA (4 statuses x rates/cases x 10 yrs = 80 runs); Jaccard comparison; classification v2 | 4 RNPDNO CSVs, AGEEML, CONAPO, municipios | `municipality_classification_v2.csv`, `hh_clusters_{rates,cases}_*.csv` (8), `cluster_comparison_rates_vs_cases.csv` | LISA, BFS, Jaccard, band/region classification | minutes |
| 09 | `09_publication_figures.py` | Generate 3 figures, 2 tables, and findings narrative from script 08 | Script 08 outputs, municipios geometry | `fig1-3.{pdf,png}`, `table1-2.tex`, `findings_summary.md` | Choropleth maps, chi-square, OLS slopes | minutes |

---

## Scripts 10–15: Active Monthly Pipeline (`rnpdno_eda`, Python 3.10)

Run sequentially: `10 -> 11 -> 12 -> 13 -> 14, 15`

| # | File | Purpose | Inputs | Outputs | Methods | Runtime |
|---|------|---------|--------|---------|---------|---------|
| 10 | `10_build_monthly_panel.py` | Load 4 status CSVs; remove sentinels; build canonical grid (2,478 x 132 x 4); zero-fill; join names + region | 4 `rnpdno_*.csv`, `municipios_2024.geoparquet`, `municipality_classification_v2.csv` | `panel_monthly_counts.parquet` (1,308,384 rows) | Polars cross-join, sentinel mask, zero-fill, name dedup | seconds |
| 11 | `11_build_spatial_weights.py` | Build Queen contiguity weights with fuzzy tolerance (50m buffer) | `panel_monthly_counts.parquet`, `municipios_2024.geoparquet` | `spatial_weights_queen.gal`, `island_municipalities.csv` | `fuzzy_contiguity(buffer=50)`, row-standardized | seconds |
| 12 | `12_compute_lisa_monthly.py` | Run LISA 1,584 times (4 statuses x 3 sexes x 132 months); global Moran's I; extract HH clusters | `panel_monthly_counts.parquet`, `spatial_weights_queen.gal` | `lisa_monthly_results.parquet` (3,925,152 rows), `morans_i_monthly.csv` (528), `hh_clusters_monthly.parquet` | Moran_Local (999 perms, alpha=0.05), BFS clusters (min 3) | ~3 min |
| 13 | `13_compute_concentration.py` | Compute Gini + HHI monthly per status; HH regional composition; cross-tabulation | `panel_monthly_counts.parquet`, `lisa_monthly_results.parquet`, `hh_clusters_monthly.parquet` | `concentration_monthly.csv` (528), `hh_regional_composition.csv`, `hh_cross_tabulation_latest.csv` | Gini, HHI, Polars group_by | seconds |
| 14 | `14_generate_figures.py` | Generate 8 publication figures (F1–F8) | Panel, concentration, Moran's I, LISA results, municipios geometry | 8 `fig*.{pdf,png}` in `manuscript/figures/` | matplotlib, geopandas choropleth, OLS slopes, imshow heatmap, chi-square | minutes |
| 15 | `15_generate_tables.py` | Generate 7 LaTeX tables (T1–T7) | 4 raw CSVs, panel, concentration, LISA | 7 `table*.tex` in `manuscript/tables/` | Polars, OLS slopes, set operations, LaTeX formatting | seconds |

---

## Pipeline Orchestrator

| File | Purpose |
|------|---------|
| `run_pipeline.py` | Sequential runner for scripts 10–15. Supports `--force`, `--from N`, `--only N`. |

---

## Shared Utility Module

| File | Functions |
|------|-----------|
| `rnpdno_eda/models/spatial.py` | `load_municipios()` — load geoparquet, set EPSG:6372, standardize cvegeo |
| | `build_queen_weights(gdf, buffer=50)` — fuzzy_contiguity with 50m buffer, row-standardized |
| | `run_lisa(values, w, perms=999, alpha=0.05)` — global + local Moran's I, cluster classification |

---

## Figure Inventory (Script 14 + CED post-processing)

| Fig | Name | Type | Content |
|-----|------|------|---------|
| 1 | `fig1_time_series_by_status` | Line | 4-panel monthly national counts, sex-disaggregated |
| 2 | `fig2_gini_time_series` | Line | Gini with OLS slope annotations + reference line at 0.90 |
| 3 | `fig3_morans_i_time_series` | Line | Global Moran's I, 4 statuses, non-sig marked |
| 4 | `fig4_lisa_maps_latest` | Map | LISA clusters Jun 2025, 2x2 by status (LL suppressed to grey) |
| 5 | `fig5_hh_trend_norte_bajio` | Line | HH municipalities: Norte vs Bajio vs Centro, 4-panel + OLS |
| 6 | `fig6_lisa_maps_2015_vs_2025` | Map | LISA bookend: Jun 2015 vs Jun 2025, Located Alive + Dead |
| 7 | `fig7_sex_disaggregation_maps` | Map | Male vs female LISA, Not Located + Located Dead, Jun 2025 |
| 8 | `fig8_regional_hh_heatmap` | Heatmap | 2x2 by status, y=6 regions, x=11 June snapshots |
| 9 | `fig9_ced_states` | Line | 2x4 CED-named states, 4 status lines, shaded temporal windows |

## Table Inventory (Script 15)

| Table | Name | Cross-section | Content |
|-------|------|---------------|---------|
| 1 | `table1_dataset_summary` | Full series | Rows, persons, sentinel counts by status |
| 2 | `table2_summary_statistics` | Full series | Mean, SD, median, P75, P95, max, skewness |
| 3 | `table3_concentration_metrics` | Full series | Gini + HHI ranges and OLS trend slopes |
| 4 | `table4_lisa_classification` | Jun 2025 | HH/LL/HL/LH/NS counts by status |
| 5 | `table5_hh_cross_tabulation` | Jun 2025 | Pairwise HH overlap matrix |
| 6 | `table6_trend_slopes` | Full series | OLS slopes (munis/yr) by region x status |
| 7 | `table7_sex_hh_counts` | Jun 2025 | HH by sex: total/male/female/overlap |

---

## Key Parameters

| Parameter | Value |
|-----------|-------|
| Municipalities | 2,478 (canonical from municipios_2024.geoparquet) |
| Temporal scope | Jan 2015 – Dec 2025 (132 months) |
| Status IDs | 0=Total, 7=Not Located, 2=Located Alive, 3=Located Dead |
| Cross-section reference | June (not December) |
| CRS | EPSG:6372 (projected, metres) |
| Spatial weights | Queen contiguity, fuzzy_contiguity(buffer=50m), row-standardized |
| LISA | 999 permutations, alpha=0.05 |
| Min cluster size | 3 municipalities (BFS connected components) |
| Regions | Norte, Norte-Occidente, Centro-Norte, Centro, Sur + Bajio (cross-cutting) |
