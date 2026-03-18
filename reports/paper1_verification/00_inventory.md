# Phase 0 Inventory — Pipeline Outputs
Generated: 2026-03-18

## data/processed/ (28 files)

| File | Size | Modified |
|------|------|----------|
| annual_rates.parquet | 255K | 2026-03-06 |
| bajio_cvegeo_list.csv | 4.4K | 2026-03-06 |
| bajio_cvegeo_list_v2.csv | 4.5K | 2026-03-06 |
| cluster_comparison_rates_vs_cases.csv | 1.8K | 2026-03-06 |
| cluster_region_trend.csv | 783 | 2026-03-06 |
| concentration_monthly.csv | 36K | 2026-03-16 |
| hh_clusters_by_year.csv | 5.8K | 2026-03-06 |
| hh_clusters_cases_disappeared.csv | 9.4K | 2026-03-06 |
| hh_clusters_cases_located_alive.csv | 8.8K | 2026-03-06 |
| hh_clusters_cases_located_dead.csv | 7.3K | 2026-03-06 |
| hh_clusters_cases_total.csv | 7.1K | 2026-03-06 |
| hh_clusters_monthly.parquet | 25K | 2026-03-16 |
| hh_clusters_rates_disappeared.csv | 9.3K | 2026-03-06 |
| hh_clusters_rates_located_alive.csv | 15K | 2026-03-06 |
| hh_clusters_rates_located_dead.csv | 6.2K | 2026-03-06 |
| hh_clusters_rates_total.csv | 11K | 2026-03-06 |
| hh_cross_tabulation_latest.csv | 1.1K | 2026-03-16 |
| hh_regional_composition.csv | 103K | 2026-03-16 |
| hotspot_centroids.csv | 501 | 2026-03-06 |
| island_municipalities.csv | 52 rows | 2026-03-11 |
| lisa_annual_clusters.parquet | 250K | 2026-03-06 |
| lisa_annual_summary.csv | 414 | 2026-03-06 |
| lisa_monthly_results.parquet | 19M | 2026-03-16 |
| master_panel.parquet | 1.4M | 2026-03-06 |
| morans_i_monthly.csv | 28K | 2026-03-16 |
| municipality_classification.csv | 46K | 2026-03-06 |
| municipality_classification_v2.csv | 51K | 2026-03-16 |
| panel_monthly_counts.parquet | 331K | 2026-03-11 |
| shift_significance.csv | 287 | 2026-03-06 |
| spatial_weights_queen.gal | 94K | 2026-03-11 |

## manuscript/figures/ (8 figures, all present)
fig1_time_series_by_status, fig2_gini_time_series, fig3_lorenz_curves,
fig4_morans_i_time_series, fig5_lisa_maps_latest, fig6_hh_trend_norte_bajio,
fig7_lisa_maps_2015_vs_2024, fig8_sex_disaggregation_maps
(Also legacy: fig1_hh_trend_by_status, fig2_cases_vs_rates_jaccard, fig3_hh_maps_2015_2024)

## manuscript/tables/ (8 tables, all present)
table1_dataset_summary, table2_summary_statistics, table3_concentration_metrics,
table4_lisa_classification, table5_hh_cross_tabulation, table6_regional_composition,
table7_trend_slopes, table8_sex_hh_counts
(Also legacy: table1_regional_shift, table2_trend_slopes)

## reports/
figures/: fig1–fig3 (from annual pipeline), fig_cluster_trend_by_region, fig_rates_vs_cases_hh
tables/: table1_regional_shift.tex, table2_trend_slopes.tex
findings_summary.md

## KEY FLAG — Study Period
Panel and LISA cover **Jan 2015 – Dec 2025** (132 months = 11 years × 12).
The tex file and blueprint refer to "2015–2024" (10 years, 120 months).
This discrepancy must be resolved before writing methods section.
