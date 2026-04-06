# 00 — Schemas

## bajio_cvegeo_list_v2.csv

**Rows:** 200 | **Columns:** 3

| Column | Dtype | Nulls | Unique | Sample values |
|--------|-------|-------|--------|---------------|
| cvegeo | Int64 | 0 | 200 | 200 unique |
| nom_mun | String | 0 | 198 | 198 unique |
| cve_estado | Int64 | 0 | 7 | 1, 11, 14, 16, 22, 24, 32 |

## ced_state_hh_timeseries.csv

**Rows:** 2,267 | **Columns:** 6

| Column | Dtype | Nulls | Unique | Sample values |
|--------|-------|-------|--------|---------------|
| cve_estado | Int64 | 0 | 8 | 11, 14, 15, 18, 19, 27, 30, 5 |
| status_id | Int64 | 0 | 4 | 0, 2, 3, 7 |
| year | Int64 | 0 | 11 | 2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025 |
| month | Int64 | 0 | 12 | 1, 10, 11, 12, 2, 3, 4, 5, 6, 7, 8, 9 |
| n_hh_munis | Int64 | 0 | 46 | 46 unique |
| state | String | 0 | 8 | Coahuila, Estado de Mexico, Guanajuato, Jalisco, Nayarit, Nuevo Leon, Tabasco, Veracruz |

**Date range:** 2015-01 to 2025-12

## ced_temporal_alignment.csv

**Rows:** 32 | **Columns:** 12

| Column | Dtype | Nulls | Unique | Sample values |
|--------|-------|-------|--------|---------------|
| cve_estado | Int64 | 0 | 8 | 11, 14, 15, 18, 19, 27, 30, 5 |
| state | String | 0 | 8 | Coahuila, Estado de Mexico, Guanajuato, Jalisco, Nayarit, Nuevo Leon, Tabasco, Veracruz |
| region | String | 0 | 5 | Centro, Centro-Norte, Norte, Norte-Occidente, Sur |
| status | String | 0 | 4 | Located Alive, Located Dead, Not Located, Total |
| hh_jun2015 | Int64 | 0 | 8 | 0, 1, 20, 23, 25, 4, 6, 8 |
| hh_jun2025 | Int64 | 0 | 14 | 14 unique |
| peak_month | String | 0 | 24 | 24 unique |
| peak_count | Int64 | 0 | 19 | 19 unique |
| slope_yr | Float64 | 0 | 32 | 32 unique |
| p_value | Float64 | 0 | 19 | 19 unique |
| ced_window | String | 0 | 5 | 2015-2016, 2015-2017, 2015-2025, 2017-2025, 2024-2025 |
| peak_in_window | Boolean | 0 | 2 | False, True |

## cluster_comparison_rates_vs_cases.csv

**Rows:** 40 | **Columns:** 9

| Column | Dtype | Nulls | Unique | Sample values |
|--------|-------|-------|--------|---------------|
| year | Int64 | 0 | 10 | 2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024 |
| status | String | 0 | 4 | disappeared, located_alive, located_dead, total |
| n_hh_rates | Int64 | 0 | 37 | 37 unique |
| n_hh_cases | Int64 | 0 | 31 | 31 unique |
| n_clusters_rates | Int64 | 0 | 12 | 10, 11, 12, 13, 16, 3, 4, 5, 6, 7, 8, 9 |
| n_clusters_cases | Int64 | 0 | 10 | 10, 11, 13, 14, 4, 5, 6, 7, 8, 9 |
| jaccard_hh | Float64 | 0 | 39 | 39 unique |
| hh_intersection | Int64 | 0 | 26 | 26 unique |
| hh_union | Int64 | 0 | 37 | 37 unique |

## concentration_monthly.csv

**Rows:** 528 | **Columns:** 8

| Column | Dtype | Nulls | Unique | Sample values |
|--------|-------|-------|--------|---------------|
| status_id | Int64 | 0 | 4 | 0, 2, 3, 7 |
| status_name | String | 0 | 4 | located_alive, located_dead, not_located, total |
| year | Int64 | 0 | 11 | 2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025 |
| month | Int64 | 0 | 12 | 1, 10, 11, 12, 2, 3, 4, 5, 6, 7, 8, 9 |
| gini | Float64 | 0 | 528 | 528 unique |
| hhi | Float64 | 0 | 528 | 528 unique |
| n_munis | Int64 | 0 | 1 | 2478 |
| total_cases | Int64 | 0 | 448 | 448 unique |

**Date range:** 2015-01 to 2025-12

## hh_clusters_cases_disappeared.csv

**Rows:** 91 | **Columns:** 12

| Column | Dtype | Nulls | Unique | Sample values |
|--------|-------|-------|--------|---------------|
| year | Int64 | 0 | 10 | 2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024 |
| status | String | 0 | 1 | disappeared |
| metric | String | 0 | 1 | cases |
| cluster_id | String | 0 | 91 | 91 unique |
| n_munis | Int64 | 0 | 17 | 17 unique |
| region | String | 0 | 5 | Centro, Centro-Norte, Norte, Norte-Occidente, Sur |
| pct_bajio | Float64 | 0 | 14 | 14 unique |
| is_bajio_cluster | Boolean | 0 | 2 | False, True |
| dominant_band | Int64 | 0 | 4 | 1, 2, 3, 4 |
| band_label | String | 0 | 4 | Band 1: Rural, Band 2: Small Town, Band 3: Mid-Size, Band 4: Metropolitan |
| centroid_x | Float64 | 0 | 75 | 75 unique |
| centroid_y | Float64 | 0 | 75 | 75 unique |

## hh_clusters_cases_located_alive.csv

**Rows:** 67 | **Columns:** 12

| Column | Dtype | Nulls | Unique | Sample values |
|--------|-------|-------|--------|---------------|
| year | Int64 | 0 | 10 | 2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024 |
| status | String | 0 | 1 | located_alive |
| metric | String | 0 | 1 | cases |
| cluster_id | String | 0 | 67 | 67 unique |
| n_munis | Int64 | 0 | 21 | 21 unique |
| region | String | 0 | 5 | Centro, Centro-Norte, Norte, Norte-Occidente, Sur |
| pct_bajio | Float64 | 0 | 6 | 0.0, 0.5, 0.6667, 0.8571, 0.9091, 1.0 |
| is_bajio_cluster | Boolean | 0 | 2 | False, True |
| dominant_band | Int64 | 0 | 4 | 1, 2, 3, 4 |
| band_label | String | 0 | 4 | Band 1: Rural, Band 2: Small Town, Band 3: Mid-Size, Band 4: Metropolitan |
| centroid_x | Float64 | 0 | 55 | 55 unique |
| centroid_y | Float64 | 0 | 55 | 55 unique |

## hh_clusters_cases_located_dead.csv

**Rows:** 69 | **Columns:** 12

| Column | Dtype | Nulls | Unique | Sample values |
|--------|-------|-------|--------|---------------|
| year | Int64 | 0 | 10 | 2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024 |
| status | String | 0 | 1 | located_dead |
| metric | String | 0 | 1 | cases |
| cluster_id | String | 0 | 69 | 69 unique |
| n_munis | Int64 | 0 | 22 | 22 unique |
| region | String | 0 | 5 | Centro, Centro-Norte, Norte, Norte-Occidente, Sur |
| pct_bajio | Float64 | 0 | 11 | 0.0, 0.4167, 0.5, 0.5882, 0.6667, 0.7143, 0.7692, 0.7857, 0.8182, 0.8333, 1.0 |
| is_bajio_cluster | Boolean | 0 | 2 | False, True |
| dominant_band | Int64 | 0 | 4 | 1, 2, 3, 4 |
| band_label | String | 0 | 4 | Band 1: Rural, Band 2: Small Town, Band 3: Mid-Size, Band 4: Metropolitan |
| centroid_x | Float64 | 0 | 67 | 67 unique |
| centroid_y | Float64 | 0 | 67 | 67 unique |

## hh_clusters_cases_total.csv

**Rows:** 76 | **Columns:** 12

| Column | Dtype | Nulls | Unique | Sample values |
|--------|-------|-------|--------|---------------|
| year | Int64 | 0 | 10 | 2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024 |
| status | String | 0 | 1 | total |
| metric | String | 0 | 1 | cases |
| cluster_id | String | 0 | 76 | 76 unique |
| n_munis | Int64 | 0 | 21 | 21 unique |
| region | String | 0 | 5 | Centro, Centro-Norte, Norte, Norte-Occidente, Sur |
| pct_bajio | Float64 | 0 | 8 | 0.0, 0.4286, 0.6667, 0.8182, 0.8462, 0.9167, 0.9231, 1.0 |
| is_bajio_cluster | Boolean | 0 | 2 | False, True |
| dominant_band | Int64 | 0 | 4 | 1, 2, 3, 4 |
| band_label | String | 0 | 4 | Band 1: Rural, Band 2: Small Town, Band 3: Mid-Size, Band 4: Metropolitan |
| centroid_x | Float64 | 0 | 56 | 56 unique |
| centroid_y | Float64 | 0 | 56 | 56 unique |

## hh_clusters_monthly.parquet

**Rows:** 24,650 | **Columns:** 6

| Column | Dtype | Nulls | Unique | Sample values |
|--------|-------|-------|--------|---------------|
| status_id | Int64 | 0 | 4 | 0, 2, 3, 7 |
| year | Int64 | 0 | 11 | 2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025 |
| month | Int64 | 0 | 12 | 1, 10, 11, 12, 2, 3, 4, 5, 6, 7, 8, 9 |
| cluster_id | Int64 | 0 | 11 | 0, 1, 10, 2, 3, 4, 5, 6, 7, 8, 9 |
| cvegeo | String | 0 | 584 | 584 unique |
| cluster_size | Int64 | 0 | 62 | 62 unique |

**Date range:** 2015-01 to 2025-12

## hh_clusters_rates_disappeared.csv

**Rows:** 80 | **Columns:** 12

| Column | Dtype | Nulls | Unique | Sample values |
|--------|-------|-------|--------|---------------|
| year | Int64 | 0 | 10 | 2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024 |
| status | String | 0 | 1 | disappeared |
| metric | String | 0 | 1 | rates |
| cluster_id | String | 0 | 80 | 80 unique |
| n_munis | Int64 | 0 | 25 | 25 unique |
| region | String | 0 | 5 | Centro, Centro-Norte, Norte, Norte-Occidente, Sur |
| pct_bajio | Float64 | 0 | 20 | 20 unique |
| is_bajio_cluster | Boolean | 0 | 2 | False, True |
| dominant_band | Int64 | 0 | 4 | 1, 2, 3, 4 |
| band_label | String | 0 | 4 | Band 1: Rural, Band 2: Small Town, Band 3: Mid-Size, Band 4: Metropolitan |
| centroid_x | Float64 | 0 | 79 | 79 unique |
| centroid_y | Float64 | 0 | 79 | 79 unique |

## hh_clusters_rates_located_alive.csv

**Rows:** 108 | **Columns:** 12

| Column | Dtype | Nulls | Unique | Sample values |
|--------|-------|-------|--------|---------------|
| year | Int64 | 0 | 10 | 2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024 |
| status | String | 0 | 1 | located_alive |
| metric | String | 0 | 1 | rates |
| cluster_id | String | 0 | 108 | 108 unique |
| n_munis | Int64 | 0 | 31 | 31 unique |
| region | String | 0 | 5 | Centro, Centro-Norte, Norte, Norte-Occidente, Sur |
| pct_bajio | Float64 | 0 | 15 | 15 unique |
| is_bajio_cluster | Boolean | 0 | 2 | False, True |
| dominant_band | Int64 | 0 | 4 | 1, 2, 3, 4 |
| band_label | String | 0 | 4 | Band 1: Rural, Band 2: Small Town, Band 3: Mid-Size, Band 4: Metropolitan |
| centroid_x | Float64 | 0 | 107 | 107 unique |
| centroid_y | Float64 | 0 | 107 | 107 unique |

## hh_clusters_rates_located_dead.csv

**Rows:** 51 | **Columns:** 12

| Column | Dtype | Nulls | Unique | Sample values |
|--------|-------|-------|--------|---------------|
| year | Int64 | 0 | 10 | 2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024 |
| status | String | 0 | 1 | located_dead |
| metric | String | 0 | 1 | rates |
| cluster_id | String | 0 | 51 | 51 unique |
| n_munis | Int64 | 0 | 14 | 14 unique |
| region | String | 0 | 5 | Centro, Centro-Norte, Norte, Norte-Occidente, Sur |
| pct_bajio | Float64 | 0 | 14 | 14 unique |
| is_bajio_cluster | Boolean | 0 | 2 | False, True |
| dominant_band | Int64 | 0 | 4 | 1, 2, 3, 4 |
| band_label | String | 0 | 4 | Band 1: Rural, Band 2: Small Town, Band 3: Mid-Size, Band 4: Metropolitan |
| centroid_x | Float64 | 0 | 51 | 51 unique |
| centroid_y | Float64 | 0 | 51 | 51 unique |

## hh_clusters_rates_total.csv

**Rows:** 110 | **Columns:** 12

| Column | Dtype | Nulls | Unique | Sample values |
|--------|-------|-------|--------|---------------|
| year | Int64 | 0 | 10 | 2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024 |
| status | String | 0 | 1 | total |
| metric | String | 0 | 1 | rates |
| cluster_id | String | 0 | 110 | 110 unique |
| n_munis | Int64 | 0 | 31 | 31 unique |
| region | String | 0 | 5 | Centro, Centro-Norte, Norte, Norte-Occidente, Sur |
| pct_bajio | Float64 | 0 | 19 | 19 unique |
| is_bajio_cluster | Boolean | 0 | 2 | False, True |
| dominant_band | Int64 | 0 | 4 | 1, 2, 3, 4 |
| band_label | String | 0 | 4 | Band 1: Rural, Band 2: Small Town, Band 3: Mid-Size, Band 4: Metropolitan |
| centroid_x | Float64 | 0 | 110 | 110 unique |
| centroid_y | Float64 | 0 | 110 | 110 unique |

## hh_cross_tabulation_latest.csv

**Rows:** 20 | **Columns:** 7

| Column | Dtype | Nulls | Unique | Sample values |
|--------|-------|-------|--------|---------------|
| status_id | Int64 | 0 | 4 | 0, 2, 3, 7 |
| cluster_label | String | 0 | 5 | HH, HL, LH, LL, NS |
| n_munis | Int64 | 0 | 20 | 20 unique |
| status_name | String | 0 | 4 | located_alive, located_dead, not_located, total |
| period | String | 0 | 1 | 2025-12 |
| total_munis | Int64 | 0 | 1 | 2478 |
| pct | Float64 | 0 | 20 | 20 unique |

## hh_regional_composition.csv

**Rows:** 3,299 | **Columns:** 7

| Column | Dtype | Nulls | Unique | Sample values |
|--------|-------|-------|--------|---------------|
| status_id | Int64 | 0 | 4 | 0, 2, 3, 7 |
| year | Int64 | 0 | 11 | 2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025 |
| month | Int64 | 0 | 12 | 1, 10, 11, 12, 2, 3, 4, 5, 6, 7, 8, 9 |
| region | String | 0 | 5 | Centro, Centro-Norte, Norte, Norte-Occidente, Sur |
| is_bajio | Boolean | 0 | 2 | False, True |
| n_hh_munis | Int64 | 0 | 71 | 71 unique |
| grouping_type | String | 0 | 1 | region |

**Date range:** 2015-01 to 2025-12

## island_municipalities.csv

**Rows:** 0 | **Columns:** 1

| Column | Dtype | Nulls | Unique | Sample values |
|--------|-------|-------|--------|---------------|
| cvegeo | String | 0 | 0 |  |

## lisa_monthly_results.parquet

**Rows:** 3,925,152 | **Columns:** 9

| Column | Dtype | Nulls | Unique | Sample values |
|--------|-------|-------|--------|---------------|
| cvegeo | String | 0 | 2478 | 2478 unique |
| year | Int16 | 0 | 11 | 2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025 |
| month | Int8 | 0 | 12 | 1, 10, 11, 12, 2, 3, 4, 5, 6, 7, 8, 9 |
| status_id | Int32 | 0 | 4 | 0, 2, 3, 7 |
| sex | String | 0 | 3 | female, male, total |
| local_i | Float32 | 0 | 357625 | 357625 unique |
| p_value | Float32 | 0 | 500 | 500 unique |
| cluster_label | String | 0 | 5 | HH, HL, LH, LL, NS |
| z_score | Float32 | 0 | 1629566 | 1629566 unique |

**Date range:** 2015-01 to 2025-12

## morans_i_monthly.csv

**Rows:** 528 | **Columns:** 6

| Column | Dtype | Nulls | Unique | Sample values |
|--------|-------|-------|--------|---------------|
| status_id | Int64 | 0 | 4 | 0, 2, 3, 7 |
| year | Int64 | 0 | 11 | 2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025 |
| month | Int64 | 0 | 12 | 1, 10, 11, 12, 2, 3, 4, 5, 6, 7, 8, 9 |
| morans_i | Float64 | 0 | 528 | 528 unique |
| p_value | Float64 | 0 | 42 | 42 unique |
| z_score | Float64 | 0 | 528 | 528 unique |

**Date range:** 2015-01 to 2025-12

## municipality_classification_v2.csv

**Rows:** 2,478 | **Columns:** 4

| Column | Dtype | Nulls | Unique | Sample values |
|--------|-------|-------|--------|---------------|
| cvegeo | Int64 | 0 | 2478 | 2478 unique |
| region | String | 0 | 5 | Centro, Centro-Norte, Norte, Norte-Occidente, Sur |
| is_bajio | Boolean | 0 | 2 | False, True |
| pop_band | Int64 | 0 | 6 | 0, 1, 2, 3, 4, 5 |

## panel_monthly_counts.parquet

**Rows:** 1,308,384 | **Columns:** 14

| Column | Dtype | Nulls | Unique | Sample values |
|--------|-------|-------|--------|---------------|
| cvegeo | String | 0 | 2478 | 2478 unique |
| cve_estado | String | 0 | 32 | 32 unique |
| cve_mun | String | 0 | 570 | 570 unique |
| state | String | 0 | 32 | 32 unique |
| municipality | String | 0 | 2346 | 2346 unique |
| year | Int32 | 0 | 11 | 2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025 |
| month | Int32 | 0 | 12 | 1, 10, 11, 12, 2, 3, 4, 5, 6, 7, 8, 9 |
| status_id | Int32 | 0 | 4 | 0, 2, 3, 7 |
| male | Int32 | 0 | 82 | 82 unique |
| female | Int32 | 0 | 58 | 58 unique |
| undefined | Int32 | 0 | 9 | 0, 1, 2, 3, 4, 5, 6, 7, 8 |
| total | Int32 | 0 | 115 | 115 unique |
| region | String | 0 | 5 | Centro, Centro-Norte, Norte, Norte-Occidente, Sur |
| is_bajio | Boolean | 0 | 2 | False, True |

**Date range:** 2015-01 to 2025-12

## spatial_weights_queen.gal

Binary file (.gal), 104.8 KB
