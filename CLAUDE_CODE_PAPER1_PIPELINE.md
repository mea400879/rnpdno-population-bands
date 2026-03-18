# PROMPT CONTRACT — Paper 1 Full Pipeline (Monthly LISA × 4 Outcome Statuses)

**Project:** `rnpdno-population-bands`
**Root:** `/home/marco/workspace/work/rnpdno-population-bands/`
**Agent:** Claude Code
**Principal:** Marco (M-RESEARCH mode)

---

## 1) GOAL

Build a **complete, reproducible pipeline** that:

1. **Loads** the 4 RNPDNO CSVs + INEGI municipal geometries + regional classification
2. **Builds** a monthly municipality-level panel for each outcome status (total, not located, located alive, located dead), with sex disaggregation (male, female, total)
3. **Computes** spatial statistics at monthly resolution (132 periods, Jan 2015 – Dec 2025) for each status:
   - Global Moran's I (Queen contiguity, 999 permutations)
   - Local Moran's I / LISA (Queen contiguity, 999 permutations, α = 0.05)
   - Gini coefficient and HHI (concentration metrics)
   - Connected-component HH clusters (minimum size = 3 municipalities)
4. **Generates** 8 publication-quality figures (300 DPI, PDF + PNG) and 8 LaTeX tables as specified in the Paper 1 blueprint
5. **Exports** all intermediate and final outputs to `data/processed/` and `manuscript/`

### Success Criteria (verifiable in < 2 minutes)

- [ ] `data/processed/panel_monthly_counts.parquet` exists with columns: `cvegeo`, `year`, `month`, `status_id`, `male`, `female`, `undefined`, `total`, and ≥ 100,000 rows
- [ ] `data/processed/lisa_monthly_results.parquet` exists with LISA classifications for 4 statuses × 132 months × ~2,422 municipalities (after sentinel exclusion)
- [ ] `data/processed/morans_i_monthly.csv` exists with 528 rows (4 statuses × 132 months), columns: `status_id`, `year`, `month`, `morans_i`, `p_value`, `z_score`
- [ ] `data/processed/concentration_monthly.csv` exists with Gini + HHI per status per month
- [ ] `manuscript/figures/` contains 8 figures as PDF (fig1–fig8)
- [ ] `manuscript/tables/` contains 8 tables as .tex files (table1–table8)
- [ ] All scripts run end-to-end via `make pipeline` (or equivalent single command)

---

## 2) CONSTRAINTS

### Environment

- **Python 3.10**, Anaconda environment `rnpdno_eda`
- Activate with: `conda activate rnpdno_eda`
- **Do NOT install new packages** without explicit approval. The environment already has: polars, geopandas, pysal (libpysal, esda, splot), shapely, folium, contextily, matplotlib, seaborn, numpy, scipy
- If a package is missing, **ask before installing**

### Data Engine

- **Polars is mandatory** for all data loading, transformation, aggregation, and panel construction
- **Pandas is allowed ONLY** for: (a) GIS operations via GeoPandas, (b) PySAL interfaces that require pandas input
- Convert Polars → Pandas at the last possible moment before spatial operations, and convert back immediately after
- **Never use Pandas for data wrangling** where Polars can do the job

### Spatial

- **Projection:** EPSG:6372 (Mexico ITRF2008 / LCC) for all distance calculations and mapping
- **Join key:** `cvegeo` (5-digit composite INEGI code = `cve_estado` + `cve_mun`)
- **Spatial weights:** Queen contiguity, row-standardized
- **Permutations:** 999 conditional permutations for all Moran's I and LISA
- **Significance:** α = 0.05
- **Island municipalities** (~53): retain in analysis; PySAL handles via conditional permutation

### External Data — Symlinks

Create these symlinks in `data/external/` pointing to the canonical pCloud location. **Do NOT copy files — symlink only.**

```
data/external/rnpdno_total.csv            → /home/marco/pCloudDrive/Datasets/crime/rnpdno/processed/rnpdno_total.csv
data/external/rnpdno_not_located.csv      → /home/marco/pCloudDrive/Datasets/crime/rnpdno/processed/rnpdno_disappeared_not_located.csv
data/external/rnpdno_located_alive.csv    → /home/marco/pCloudDrive/Datasets/crime/rnpdno/processed/rnpdno_located_alive.csv
data/external/rnpdno_located_dead.csv     → /home/marco/pCloudDrive/Datasets/crime/rnpdno/processed/rnpdno_located_dead.csv
data/external/municipios_2024.geoparquet  → /home/marco/pCloudDrive/Datasets/geographic/marco_geoestadistico/processed/municipios_2024.geoparquet
data/external/conapo_poblacion.parquet    → /home/marco/pCloudDrive/Datasets/socioeconomic/conapo_proyecciones/raw/poblacion_1990_2070_municipal.parquet
data/external/ageeml_catalog.csv          → /home/marco/pCloudDrive/Datasets/geographic/marco_geoestadistico/raw/AGEEML_202512121053644.csv
```

Note: some of these symlinks may already exist in `data/external/`. Check first; only create missing ones. Do NOT overwrite existing symlinks.

### Regional Classification

Use the 5-region scheme from Mexicoencifras (CESOP):

| Region | States |
|--------|--------|
| Sur | Guerrero, Oaxaca, Chiapas, Veracruz, Tabasco, Campeche, Yucatán, Quintana Roo |
| Centro | Guanajuato, Querétaro, Hidalgo, México, Ciudad de México, Morelos, Tlaxcala, Puebla |
| Centro-Norte | Jalisco, Aguascalientes, Colima, Michoacán, San Luis Potosí |
| Norte | Baja California, Sonora, Chihuahua, Coahuila, Nuevo León, Tamaulipas |
| Norte-Occidente | Baja California Sur, Sinaloa, Nayarit, Durango, Zacatecas |

**Bajío sub-flag:** Municipalities in the following states get `is_bajio = True`: Guanajuato, Querétaro, Aguascalientes, San Luis Potosí, plus Jalisco municipalities in the Altos de Jalisco / Lagos de Moreno corridor. Use the existing `bajio_cvegeo_list_v2.csv` in `data/processed/` if available; otherwise, construct from the state-level definition above.

### Code Architecture

- **Scripts in `scripts/`**: Numbered sequentially (10_xxx.py, 11_xxx.py, ...) to avoid collision with existing 01–09 scripts
- **Reusable modules in `rnpdno_eda/`**: spatial functions go in `rnpdno_eda/models/spatial.py` (already exists — extend, do not rewrite unless necessary)
- **Configuration:** All paths, parameters (α, permutations, min cluster size, regions) in a single `config.py` or at the top of each script as constants. No hardcoded paths buried in functions.
- **Logging:** Use Python `logging` module, not print statements. Log to `logs/pipeline.log`.

### Visualization

- **DPI:** 300 for all raster outputs
- **Formats:** Save both PDF (vector) and PNG (raster) for every figure
- **Style:** Academic palette. Use `matplotlib` with a clean style (e.g., `seaborn-v0_8-whitegrid` or similar). No default matplotlib blue.
- **Map projection:** EPSG:6372 for all choropleth/LISA maps
- **LaTeX labels:** Use LaTeX rendering for axis labels where appropriate (`plt.rc('text', usetex=False)` is fine — use mathtext `$...$` notation)
- **Figure size:** Minimum 8×6 inches for single panels, 12×10 for multi-panel figures
- **Font:** Serif family for axis labels (matches JQC/Springer style)

### Approval Gates

**Do not proceed between phases without approval.** The pipeline has 4 phases:

1. **Phase 1 — Data loading + panel construction** (scripts 10–11)
2. **Phase 2 — Spatial statistics computation** (scripts 12–13): LISA, Moran's I, Gini, HHI
3. **Phase 3 — Figure generation** (script 14)
4. **Phase 4 — Table generation** (script 15)

After completing each phase, **stop and present**:
- Row counts, column names, summary stats for key outputs
- Sample outputs (head of dataframes, thumbnail of figures)
- Any anomalies, warnings, or decisions made

**Wait for explicit "proceed" before starting the next phase.**

---

## 3) FORMAT

### File Paths — Scripts

```
scripts/
├── 10_build_monthly_panel.py       # Phase 1: Load 4 CSVs → unified panel
├── 11_build_spatial_weights.py     # Phase 1: Load geometries → Queen weights matrix
├── 12_compute_lisa_monthly.py      # Phase 2: LISA for 4 statuses × 132 months × {total, male, female}
├── 13_compute_concentration.py     # Phase 2: Gini, HHI, global Moran's I
├── 14_generate_figures.py          # Phase 3: All 8 publication figures
├── 15_generate_tables.py           # Phase 4: All 8 LaTeX tables
└── run_pipeline.py                 # Orchestrator (or use Makefile target)
```

### File Paths — Outputs

```
data/processed/
├── panel_monthly_counts.parquet          # Phase 1 output
├── spatial_weights_queen.gal             # Phase 1 output (PySAL weights file)
├── lisa_monthly_results.parquet          # Phase 2 output
├── morans_i_monthly.csv                  # Phase 2 output
├── concentration_monthly.csv             # Phase 2 output
├── hh_clusters_monthly.parquet           # Phase 2 output (connected-component clusters)
├── hh_regional_composition.csv           # Phase 2 output
└── hh_cross_tabulation_latest.csv        # Phase 2 output

manuscript/
├── figures/
│   ├── fig1_time_series_by_status.{pdf,png}
│   ├── fig2_gini_time_series.{pdf,png}
│   ├── fig3_lorenz_curves.{pdf,png}
│   ├── fig4_morans_i_time_series.{pdf,png}
│   ├── fig5_lisa_maps_latest.{pdf,png}
│   ├── fig6_hh_trend_norte_bajio.{pdf,png}
│   ├── fig7_lisa_maps_2015_vs_2024.{pdf,png}
│   └── fig8_sex_disaggregation_maps.{pdf,png}
└── tables/
    ├── table1_dataset_summary.tex
    ├── table2_summary_statistics.tex
    ├── table3_concentration_metrics.tex
    ├── table4_lisa_classification.tex
    ├── table5_hh_cross_tabulation.tex
    ├── table6_regional_composition.tex
    ├── table7_trend_slopes.tex
    └── table8_sex_hh_counts.tex
```

### Key Data Schemas

**panel_monthly_counts.parquet:**

| Column | Type | Description |
|--------|------|-------------|
| cvegeo | str | 5-digit INEGI composite code |
| cve_estado | str | 2-digit state code |
| cve_mun | str | 3-digit municipal code |
| state | str | State name (Spanish) |
| municipality | str | Municipality name (Spanish) |
| year | int | 2015–2025 |
| month | int | 1–12 |
| status_id | int | 0=total, 7=not located, 2=located alive, 3=located dead |
| male | int | Male count |
| female | int | Female count |
| undefined | int | Undefined sex count |
| total | int | male + female + undefined |
| region | str | Sur/Centro/Centro-Norte/Norte/Norte-Occidente |
| is_bajio | bool | Bajío sub-flag |

**Sentinel geocodes (99998, XX998, XX999) must be EXCLUDED** from the panel. They represent unresolvable geography.

**Zero-infilling:** For every valid municipality × month × status_id combination that does NOT appear in the CSV, insert a row with male=0, female=0, undefined=0, total=0. This is critical — missing rows mean zero cases, not missing data.

**lisa_monthly_results.parquet:**

| Column | Type | Description |
|--------|------|-------------|
| cvegeo | str | Municipality code |
| year | int | Year |
| month | int | Month |
| status_id | int | Outcome status |
| sex | str | 'total', 'male', or 'female' |
| local_i | float | Local Moran's I statistic |
| p_value | float | Pseudo p-value |
| cluster_label | str | 'HH', 'LL', 'HL', 'LH', 'NS' (not significant) |
| z_score | float | Z-score |

---

## 4) FAILURE CONDITIONS

Any of the following **reject the output**:

1. **Pandas used for data wrangling** where Polars could do the job (loading CSVs, joins, aggregations, pivots, filtering)
2. **EPSG:4326 used for mapping or distance calculations** instead of EPSG:6372
3. **Sentinel geocodes (99998, XX998, XX999) present** in spatial analysis outputs
4. **Zero-infilling not applied** — if the panel has fewer rows than expected (2,422 valid municipalities × 132 months × 4 statuses ≈ 1,278,816 rows), zero-infilling was missed
5. **Figures below 300 DPI** or missing PDF vector version
6. **LaTeX tables not compilable** — each .tex file must be a standalone `tabular` environment (not a full document)
7. **Hardcoded absolute paths** in any script (use relative paths from project root, or config constants)
8. **New packages installed without approval**
9. **Existing scripts (01–09) modified** without approval
10. **Existing files in `data/processed/` overwritten** — new outputs use new filenames as specified above
11. **Phase boundary crossed without approval** — agent must stop and present results after each phase

---

## 5) TEST PLAN

### Phase 1 Checks
- [ ] `panel_monthly_counts.parquet` row count ≈ 1,278,816 (±5% for edge cases)
- [ ] No sentinel cvegeo values (99998, XX998, XX999) in panel
- [ ] `total == male + female + undefined` for every row
- [ ] All 4 status_id values present (0, 2, 3, 7)
- [ ] All 132 year-month combinations present (2015-01 through 2025-12)
- [ ] Sum of `total` column for status_id=0 matches approximate known RNPDNO total (~250k persons)
- [ ] `region` and `is_bajio` columns populated for all rows
- [ ] Spatial weights matrix has 2,422 ± 50 observations

### Phase 2 Checks
- [ ] `morans_i_monthly.csv` has 528 rows (4 statuses × 132 months)
- [ ] All Moran's I p-values < 0.05 (spatial clustering expected in all periods)
- [ ] `lisa_monthly_results.parquet` has entries for all 5 cluster labels (HH, LL, HL, LH, NS)
- [ ] HH cluster counts are plausible (50–200 municipalities per status per period)
- [ ] Gini values in [0, 1] range; HHI values in [0, 1] range
- [ ] Connected-component clusters have minimum size 3

### Phase 3 Checks
- [ ] 8 figure files exist in both PDF and PNG
- [ ] All figures render correctly (no blank panels, no missing legends)
- [ ] Maps use EPSG:6372 projection
- [ ] Color scheme is consistent across figures

### Phase 4 Checks
- [ ] 8 .tex files compile without errors when included in a LaTeX document
- [ ] Tables have correct column counts and row labels
- [ ] Numerical values match computed outputs

---

## 6) HANDSHAKE

Before writing any code or installing any dependency:

1. **Summarize** the constraints (data engine rules, projection, approval gates, file naming)
2. **List your assumptions** about:
   - The existing `rnpdno_eda/models/spatial.py` module (what functions does it provide?)
   - The schema of the 4 RNPDNO CSVs (columns, types)
   - The structure of `municipios_2024.geoparquet` (CRS, join column name)
   - The Bajío municipality list format
   - Whether the existing scripts (01–09) need to run first or can be bypassed
3. **Ask 3–5 clarifying questions** about anything ambiguous
4. **Wait for explicit approval** before proceeding

**Do not write a single line of code until I say "proceed."**

---

## REFERENCE: Paper 1 Blueprint

See `paper1_merge_blueprint.md` in project root for the full section-by-section plan, figure/table specifications, and research questions. The pipeline outputs must support all analyses described in that document.

## REFERENCE: Existing Pipeline

Scripts `01_build_master_panel.py` through `09_publication_figures.py` represent the **annual-resolution** pipeline used for the earlier drafts. The new scripts (10+) build a **monthly-resolution** pipeline. Do NOT modify scripts 01–09. You may READ them to understand data structures and reuse logic, but all new work goes in scripts 10+.

The existing `rnpdno_eda/models/spatial.py` module likely contains reusable LISA/Moran's I wrapper functions. Read it first and reuse where possible. Extend if needed — do not rewrite.
