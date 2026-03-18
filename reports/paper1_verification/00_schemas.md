# Phase 0 Schemas — Key Pipeline Files
Generated: 2026-03-18

## panel_monthly_counts.parquet
- **Rows:** 1,308,384 = 2,478 munis × 4 statuses × 132 months
- **Columns:** cvegeo(Str), cve_estado(Str), cve_mun(Str), state(Str), municipality(Str), year(Int32), month(Int32), status_id(Int32), male(Int32), female(Int32), undefined(Int32), total(Int32), region(Str), is_bajio(Bool)
- **Years:** 2015–2025 | **Months:** 1–12
- **status_id:** [0, 2, 3, 7] = total, located_alive, located_dead, not_located
- **region:** Centro, Centro-Norte, Norte, Norte-Occidente, Sur

## lisa_monthly_results.parquet
- **Rows:** 3,925,152 = 2,478 munis × 4 statuses × 3 sexes × 132 months
- **Columns:** cvegeo(Str), year(Int16), month(Int8), status_id(Int32), sex(Str), local_i(Float32), p_value(Float32), cluster_label(Str), z_score(Float32)
- **sex:** female, male, total
- **cluster_label:** HH, LL, HL, LH, NS (not-significant)

## hh_clusters_monthly.parquet
- **Rows:** 18,006 (one row per municipality-member of an HH cluster, min cluster size=3)
- **Columns:** status_id(Int64), year(Int64), month(Int64), cluster_id(Int64), cvegeo(Str), cluster_size(Int64)
- NOTE: total sex only (no sex disaggregation in cluster file)

## morans_i_monthly.csv
- **Rows:** 528 = 4 statuses × 132 months
- **Columns:** status_id, year, month, morans_i, p_value, z_score
- NOTE: total sex only

## concentration_monthly.csv
- **Rows:** 528 = 4 statuses × 132 months
- **Columns:** status_id, status_name, year, month, gini, hhi, n_munis, total_cases

## hh_regional_composition.csv
- **Rows:** 3,086
- **Columns:** status_id, year, month, region, is_bajio, n_hh_munis, grouping_type
- grouping_type: likely 'region' and 'bajio' subsets

## hh_cross_tabulation_latest.csv
- **Rows:** 19 (LISA classifications × 4 statuses for latest period)
- **Columns:** status_id, cluster_label, n_munis, status_name, period, total_munis, pct

## municipality_classification_v2.csv
- **Rows:** 2,478
- **Columns:** cvegeo(Int64), region(Str), is_bajio(Bool), pop_band(Int64)

## island_municipalities.csv
- **Rows:** 52 (zero Queen neighbors)
- **Columns:** cvegeo

## spatial_weights_queen.gal
- **N obs:** 2,478 (confirmed from GAL header)

## lisa_annual_clusters.parquet
- **Rows:** 24,780 = 2,478 munis × 10 years (2015–2024)
- **Columns:** year, cvegeo, cluster(0–4), lisa_I, lisa_p
- cluster: 0=NS, 1=HH, 2=LL, 3=LH, 4=HL — total status only

## master_panel.parquet
- **Rows:** 57,370 (annual pipeline panel, status_id=0 only)
- **Columns:** cvegeo, cve_estado, state, cve_mun, municipality, male, female, undefined, total, year, month, status_id, date, pop_dynamic, pop_band, risk_rate

## cluster_comparison_rates_vs_cases.csv
- **Rows:** 40 = 4 statuses × 10 years
- **Columns:** year, status, n_hh_rates, n_hh_cases, n_clusters_rates, n_clusters_cases, jaccard_hh, hh_intersection, hh_union
