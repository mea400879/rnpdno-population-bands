# CLAUDE CODE TASK — Full Pipeline Rerun (Updated 2026-04-06)

**Project root:** `/home/marco/workspace/work/rnpdno-population-bands/`
**Environment:** `conda activate rnpdno_eda` (Python 3.10)
**Status:** Pipeline completed successfully on 2026-04-06. Verification phases 00–09 regenerated. This file is the canonical reference for re-running if needed.

---

## LOCKED DECISIONS

- **Temporal window:** Jan 2015 – Dec 2025 (132 months)
- **Cross-section reference month:** JUNE (year=2025, month=6)
- **Bookend comparison:** Jun 2015 vs Jun 2025
- **Municipalities:** 2,478 (from `municipios_2024.geoparquet`)
- **Islands:** 0 (fuzzy_contiguity with 50m buffer)
- **Spatial weights:** Queen contiguity via `fuzzy_contiguity(buffer=50)`, row-standardized
- **LISA:** 999 permutations, α=0.05, 1,584 runs (4 statuses × 3 sexes × 132 months)
- **Min cluster size:** 3 municipalities (BFS connected components)
- **Polars mandatory** for data wrangling. Pandas only for GIS/PySAL.
- **EPSG:6372** for all spatial operations.
- **No sentinel cvegeo** (99998, XX998, XX999) in any output.
- **300 DPI**, PDF + PNG. Max 10 MB per figure. Simplify geometry (tolerance=500) and rasterize if needed.
- **Newey-West HAC** (bandwidth=12) for OLS trends on monthly data.

---

## FIGURE INVENTORY (9 figures, renumbered)

Old fig2 (plain Gini) merged into fig2 (annotated Gini). Old fig3 (Lorenz) replaced with Gini. All downstream renumbered. Old fig10 became fig9.

| Fig | Filename | Content |
|-----|----------|---------|
| 1 | `fig1_time_series_by_status` | Monthly counts, sex-disaggregated, 4 panels |
| 2 | `fig2_gini_time_series` | Gini + OLS slopes + reference line at 0.90 |
| 3 | `fig3_morans_i_time_series` | Global Moran's I, 4 statuses, non-sig marked |
| 4 | `fig4_lisa_maps_latest` | LISA maps Jun 2025, 2×2 by status, LL = grey (#D9D9D9) |
| 5 | `fig5_hh_trend_norte_bajio` | HH municipalities: Norte vs Bajío vs Centro + OLS slopes |
| 6 | `fig6_lisa_maps_2015_vs_2025` | Bookend Jun 2015 vs Jun 2025, Located Alive + Dead |
| 7 | `fig7_sex_disaggregation_maps` | Male vs female LISA, Not Located + Located Dead, Jun 2025 |
| 8 | `fig8_regional_hh_heatmap` | 2×2 by status, y=6 regions, x=11 June snapshots |
| 9 | `fig9_ced_states` | 2×4 CED-named states, 4 status lines, shaded temporal windows |

## TABLE INVENTORY (7 tables)

| Table | Filename | Cross-section |
|-------|----------|---------------|
| 1 | `table1_dataset_summary` | Full series |
| 2 | `table2_summary_statistics` | Full series |
| 3 | `table3_concentration_metrics` | Full series |
| 4 | `table4_lisa_classification` | Jun 2025 |
| 5 | `table5_hh_cross_tabulation` | Jun 2025 |
| 6 | `table6_trend_slopes` | Full series |
| 7 | `table7_sex_hh_counts` | Jun 2025 |

---

## EXECUTION ORDER (for re-run)

```
0.  Verify data symlinks (data/raw/ → pCloud)
1.  Pre-flight check (log row counts + Jun/Nov/Dec 2025 totals)
2.  Script 10: python scripts/10_build_monthly_panel.py
3.  Script 11: python scripts/11_build_spatial_weights.py
4.  Script 12: python scripts/12_compute_lisa_monthly.py
5.  Script 13: python scripts/13_compute_concentration.py
6.  Script 14: python scripts/14_generate_figures.py
7.  Script 15: python scripts/15_generate_tables.py
8.  Post-run validation (row counts, headline numbers, file sizes)
9.  Regenerate verification reports (phases 00–09)
9.5 CED state-level HH analysis (post-processing on LISA output)
10. Git commit
```

### Step 0 — Verify Data Symlinks

```bash
cd ~/workspace/work/rnpdno-population-bands/
ls -la data/raw/rnpdno_*.csv
head -3 data/raw/rnpdno_total.csv
ls -la data/external/municipios_2024.geoparquet
```

All symlinks must point to `~/pCloudDrive/Datasets/crime/rnpdno/`. If broken, stop.

### Step 1 — Pre-Flight Check

```bash
python -c "
import polars as pl
files = {0: 'data/raw/rnpdno_total.csv', 7: 'data/raw/rnpdno_disappeared_not_located.csv',
         2: 'data/raw/rnpdno_located_alive.csv', 3: 'data/raw/rnpdno_located_dead.csv'}
for sid, path in files.items():
    df = pl.read_csv(path)
    print(f'status_id={sid} | rows={len(df)}')
    for yr, mo in [(2025,6),(2025,11),(2025,12)]:
        t = df.filter((pl.col('year')==yr)&(pl.col('month')==mo))['total'].sum()
        print(f'  {yr}-{mo:02d}: {t}')
"
```

Log output. Proceed regardless.

### Steps 2–5 — Core Pipeline

```bash
conda activate rnpdno_eda
python scripts/10_build_monthly_panel.py
python scripts/11_build_spatial_weights.py
python scripts/12_compute_lisa_monthly.py
python scripts/13_compute_concentration.py
```

**Validation checkpoints:**
- Panel: 1,308,384 rows (2,478 × 4 × 132)
- Weights: 2,478 obs, 0 islands
- LISA: 3,925,152 rows
- Concentration: 528 rows

### Step 6 — Script 14: Figures

Script 14 already contains all fixes from the April 6 run. Verify before running:

1. **Fig 2**: Gini time series WITH OLS slope annotations + 0.90 reference line (merged — no separate Lorenz figure exists)
2. **Fig 4**: LL color = `#D9D9D9` (grey), cross-section = Jun 2025
3. **Fig 5**: THREE lines: Norte + Bajío + Centro
4. **Fig 6**: Bookend = Jun 2015 vs Jun 2025
5. **Fig 7**: Cross-section = Jun 2025
6. **Fig 8**: Regional HH heatmap, 11 June snapshots, 2×2 by status
7. **Fig 9**: CED state-level small-multiples (8 panels, 4 status lines each)
8. **Figure numbering**: fig1 through fig9 sequentially, no gaps, no old fig3_lorenz or duplicate Gini

```bash
python scripts/14_generate_figures.py
```

Validate: 9 figures in `manuscript/figures/`, each PDF + PNG, non-zero, under 10 MB.

### Step 7 — Script 15: Tables

All cross-section tables use Jun 2025.

```bash
python scripts/15_generate_tables.py
```

Validate: 7 .tex files in `manuscript/tables/`.

### Step 8 — Post-Run Validation

Write to `logs/rerun_2026-04-06.md`:

1. Row counts match expected values
2. Headline numbers (Jun 2025):
   - Jaccard NL↔LD = 0.143, LA↔LD = 0.151, NL↔LA = 0.381
   - HH counts: Total=106, NL=93, LA=110, LD=35
   - Centro NL slope = +4.96/yr (p<0.001)
   - Bajío Total slope = −1.09/yr (p<0.001)
3. Figure inventory with file sizes
4. Table inventory

### Step 9 — Regenerate Verification Reports

Reports in `reports/paper1_verification/`. All cross-section analyses use June 2025.

| Phase | File | Content |
|-------|------|---------|
| 00 | `00_inventory.md`, `00_schemas.md` | File listing + column schemas |
| 01 | `01_municipality_reconciliation.md` | N=2,478, 0 islands, sentinel exclusion |
| 02 | `02_trend_slopes.md`, `.csv` | OLS slopes 20 region×status + 4 Bajío |
| 03 | `03_concentration.md`, `.csv` | Gini/HHI stats, Weisburd benchmark |
| 04 | `04_clustering.md`, `04_jaccard_matrix.csv` | LISA counts, Jaccard (Jun 2025/2020/2015) |
| 05 | `05_temporal_dynamics.md`, `.csv` | Centro/Norte/Bajío narratives |
| 06 | `06_sex_disaggregation.md` | Sex composition, M/F Jaccard, LD power warning |
| 07 | `07_robustness.md` | Reference period sensitivity, zero-inflation |
| 08 | `08_executive_summary_v2.md` | 10 headline numbers |
| 09 | `09_endpoint_diagnosis.md` | Nov–Dec 2025 reporting lag |

### Step 9.5 — CED State-Level HH Analysis

Post-processing on `lisa_monthly_results.parquet`. No new LISA.

**CED-named states:**

| State | cve_estado | CED claim |
|-------|-----------|-----------|
| Jalisco | 14 | Currently highest disappeared |
| Guanajuato | 11 | Eightfold increase since 2017 |
| Coahuila | 05 | Patterns 2009–2016 |
| Veracruz | 30 | Patterns 2010–2016 |
| Nayarit | 18 | Patterns 2011–2017 |
| Tabasco | 27 | Exponential increase 2024–2025, girls/women |
| Nuevo León | 19 | Civil society contributions |
| Estado de México | 15 | Civil society contributions |

**Outputs:**
- `data/processed/ced_state_hh_timeseries.csv`
- `data/processed/ced_temporal_alignment.csv`
- `reports/paper1_verification/10_ced_alignment.md`
- `manuscript/figures/fig9_ced_states.{pdf,png}`

**Tabasco sex check:** Female NL + LA HH counts for cve_estado=27, monthly 2023–2025 vs male. Append to `10_ced_alignment.md`.

### Step 10 — Git Commit

```bash
git add -A
git commit -m "rerun: full pipeline regeneration April 2026

- Fresh RNPDNO data, Jan 2015 – Dec 2025 (132 months)
- Cross-section: June 2025
- 0 islands (fuzzy_contiguity buffer=50m)
- 9 figures (renumbered: Lorenz dropped, Gini merged, downstream shifted)
- 7 tables (all Jun 2025 cross-sections)
- CED alignment: 8 states, temporal windows, Tabasco sex check
- Verification phases 00–09 regenerated"
```

---

## IF SOMETHING FAILS

1. **Symlink broken:** Stop. pCloud not mounted.
2. **Missing file in `data/processed/`:** Prior script failed. Fix that script first.
3. **Missing `municipality_classification_v2.csv`:** Re-run script 08 first.
4. **LISA >3 hours:** Check municipality count (must be 2,478).
5. **Figure >10 MB:** Simplify geometry (`tolerance=500`), rasterize.
6. **Any anomaly:** Log with "⚠️ ANOMALY" prefix.
