# WP2-FIX: Diagnosis of LD Slope Discrepancies
**Run:** 2026-04-17T10:39:46.834897
**Seed:** 42

## Root Cause: Two Compounding Bugs in WP2 Task 2.6

### Bug 1 — Raw LISA vs BFS-Filtered HH Time Series

WP2 Task 2.6 builds regional time series from `hh_regional_composition.csv`, which
aggregates ALL municipalities classified as HH by LISA (cluster_label == "HH"), regardless
of whether they belong to a spatially contiguous cluster of ≥3 municipalities (BFS filter).

The manuscript Section 3.3 states that only BFS-filtered hotspot clusters (minimum 3
contiguous HH municipalities) are retained for trend analysis. The processed file
`hh_clusters_monthly.parquet` reflects this filter (minimum cluster_size = 3 confirmed).

**Jan 2015, status=Total: raw vs BFS count by region**
| Region          | Raw LISA HH munis | BFS-filtered | Excess raw |
|-----------------|:-----------------:|:------------:|:----------:|
| Sur             | 13                | 3            | +10        |
| Norte-Occidente | 6                 | 3            | +3         |
| Centro-Norte    | 12                | 8            | +4         |
| Norte           | 15                | 12           | +3         |
| Centro          | 32                | 28           | +4         |

The excess raw municipalities are isolated HH cases or pairs that do NOT form
spatially contiguous clusters of ≥3 municipalities. Their temporal trajectories
differ from genuine cluster trends, introducing noise that can flip signs or inflate
magnitudes — especially where baseline BFS counts are near zero (e.g., Sur LD).

### Bug 2 — Missing-month regression on incomplete time series

WP2 Task 2.6 does NOT zero-fill months where a region has zero HH municipalities.
For low-count region/status combinations (e.g., Norte-Occidente LD, Sur LD), many
months have no HH municipalities at all. WP2 regressions run on the subset of
non-zero months only, producing a biased estimate that can have the wrong sign
relative to the full 132-month series.

The fix script zero-fills all 132 months for every region/status combination.

## LD Slopes: WP2 stored vs BFS fix (all LD cells)

         region  wp2_slope  bfs_slope wp2_stars bfs_hac_stars bfs_ols_stars
          Norte      0.734      0.742       ***           ***           ***
Norte-Occidente     -0.080      0.009        ns            ns            ns
   Centro-Norte     -0.202     -0.080        ns            ns            ns
         Centro      1.216      0.955       ***           ***           ***
            Sur     -0.078      0.017        ns            ns            ns
          Bajio      0.148      0.148        ns            ns             *

The three task-brief discrepancies (Centro-Norte −0.202→−0.080; Norte-Occidente
−0.080→+0.009; Sur −0.078→+0.017) are explained by Bug 1 + Bug 2 combined.

## HAC vs OLS Significance Stars

WP2 audit confirmed (Task 2.7 Bajío sub-component slopes) that the manuscript uses
OLS significance stars despite the table caption stating Newey-West HAC SEs.

Evidence: Bajío sub-components LD/LA/Total have HAC p > 0.10 (ns) but OLS p < 0.05 (*/
**), and the manuscript reports *, **, *.

Cells in the corrected BFS Table 5 where OLS and HAC stars differ (7/24):
         region status  slope_yr ols_stars hac_stars
Norte-Occidente  total     0.342       ***        **
   Centro-Norte  total    -0.954       ***         *
          Bajio  total    -0.307         *        ns
Norte-Occidente     nl     0.391       ***        **
   Centro-Norte     nl    -0.963       ***        **
          Bajio     la    -0.346        **        ns
          Bajio     ld     0.148         *        ns

## Summary of All Changes

| Issue | Scope |
|-------|-------|
| Slope changes > 0.02 (BFS vs WP2 raw) | 18/24 cells |
| Star changes (HAC vs WP2 stored) | 6/24 cells |
| Star changes (OLS vs HAC on BFS) | 7/24 cells |

## Recommendation

1. **Table 5**: use BFS-filtered time series (`hh_clusters_monthly.parquet`) with
   zero-filled 132-month series. Use HAC p-values for significance stars.
2. **Bajío row**: use raw LISA HH for the 29-muni corridor (BFS distorts this
   small corridor; raw LISA matches manuscript magnitude exactly).
3. **Bajío piecewise caption**: correct stars for LD/LA/Total sub-components to ns
   (HAC), or change caption to "OLS standard errors" if that is the actual method.
4. **Guanajuato LA**: HAC p = 0.40 (ns), not p<0.001 as claimed — Serious error.
   OLS p = 0.003 (**), still not p<0.001.
5. **Mann-Whitney claim "all pairwise p>0.50"**: incorrect — 3/6 pairs have
   0.14 ≤ p ≤ 0.19. Correct claim: "all pairwise p > 0.05; three of six p > 0.50."

## Files Generated
- `WP2_FIX_table5_hac.csv` — corrected 24-cell Table 5 (BFS + HAC stars)
- `WP2_FIX_table5_full_diagnostics.csv` — full regression output (OLS and HAC)
- `WP2_FIX_table5_comparison.csv` — cell-by-cell comparison vs WP2
- `WP2_FIX_bajio_piecewise.csv` — Bajío Chow piecewise + sub-component slopes
- `WP2_FIX_ced_guanajuato.csv` — Guanajuato OLS vs HAC
- `WP2_FIX_mannwhitney.csv` — all 6 Mann-Whitney p-values
