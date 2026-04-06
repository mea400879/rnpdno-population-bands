# CLAUDE CODE TASK — Full Pipeline Rerun (Unattended Overnight)

**Date:** 2026-04-06
**Principal:** Marco (asleep — do NOT pause for approval gates)
**Mode:** Fully autonomous. Run everything end-to-end. Log decisions to `logs/rerun_2026-04-06.md`.
**Project root:** `/home/marco/workspace/work/rnpdno-population-bands/`
**Environment:** `conda activate rnpdno_eda` (Python 3.10)

**CRITICAL: `data/processed/` has been wiped clean.** Every intermediate and output file must be regenerated from scratch. If any script expects a file in `data/processed/` that a prior script should have created, and it's missing, that means the prior script failed — stop and log the error.

---

## LOCKED DECISIONS (do not revisit)

- **Temporal window:** Jan 2015 – Dec 2025 (132 months)
- **Cross-section reference month:** JUNE (not December). All LISA snapshot maps, cross-tabulations, and tables that show a single-period snapshot use **June 2025** (year=2025, month=6). Full 132-month time series for trend analysis remain unchanged.
- **Bookend comparison:** Jun 2015 vs Jun 2025
- **Fig 3:** Replace Lorenz curves with **Gini time series** (4 lines, one per status, 132 months)
- **Fig 5:** LL suppressed to grey (#D9D9D9)
- **Fig 6:** Add **Centro** as third line alongside Norte and Bajío
- **Fig 9:** NEW figure — Regional HH heatmap (2×2 grid by status, y=region, x=11 June snapshots, color=HH count)
- **Fig 10:** NEW figure — CED state-level HH small-multiples (8 panels)
- **Municipality count:** 2,478 (from shapefile at `data/external/municipios_2024.geoparquet`)

---

## Step 0 — Verify Data Symlinks

Symlinks already exist in `data/raw/`. Verify they resolve correctly:

```bash
cd ~/workspace/work/rnpdno-population-bands/
ls -la data/raw/rnpdno_*.csv
head -3 data/raw/rnpdno_total.csv
```

All 4 symlinks should point to `~/pCloudDrive/Datasets/crime/rnpdno/`. If any are broken (pCloud not mounted), **stop and log the error**.

Also verify external data:
```bash
ls -la data/external/municipios_2024.geoparquet
ls -la data/external/ageeml_catalog.csv
```

---

## Step 1 — Pre-Flight Check (log only, do not block)

Quantify the delta between the March 18 scrape and the fresh April 6 scrape. Write results to `logs/rerun_2026-04-06.md`.

```python
import polars as pl

files = {
    0: "data/raw/rnpdno_total.csv",
    7: "data/raw/rnpdno_disappeared_not_located.csv",
    2: "data/raw/rnpdno_located_alive.csv",
    3: "data/raw/rnpdno_located_dead.csv",
}

# National monthly totals from March 18 scrape (baseline for comparison)
baselines_dec = {0: 1750, 7: 852, 2: 868, 3: 41}
baselines_nov = {0: 2510, 7: 1110, 2: 1336, 3: 69}
baselines_jun = {0: 3094, 7: 1169, 2: 1788, 3: 144}

for sid, path in files.items():
    df = pl.read_csv(path)
    print(f"\n=== status_id={sid} | rows={len(df)} ===")

    for label, yr, mo, base in [
        ("Jun 2025", 2025, 6, baselines_jun),
        ("Nov 2025", 2025, 11, baselines_nov),
        ("Dec 2025", 2025, 12, baselines_dec),
    ]:
        subset = df.filter((pl.col("year") == yr) & (pl.col("month") == mo))
        total = subset["total"].sum()
        delta = total - base.get(sid, 0)
        print(f"  {label}: {total} (delta vs Mar-18: {delta:+d})")
```

**Log output. Then proceed regardless** — June cross-sections are not affected by Dec reporting lag.

---

## Step 2 — Script 10: Monthly Panel

```bash
python scripts/10_build_monthly_panel.py
```

**Validate:**
- Output: `data/processed/panel_monthly_counts.parquet`
- Expected rows: 1,308,384 (2,478 × 4 × 132)
- `total == male + female + undefined` for all rows
- No sentinel cvegeo (99998, XX998, XX999)
- All 132 year-month combos present
- Columns include: `cvegeo, cve_estado, cve_mun, state, municipality, year, month, status_id, male, female, undefined, total, region, is_bajio`

**If `region` or `is_bajio` columns are missing:** The script may need the regional classification and Bajío municipality list. These were previously in `data/processed/bajio_cvegeo_list_v2.csv` and `municipality_classification_v2.csv`, which have been deleted. The script must regenerate them from the 5-region CESOP scheme (see PAPER1_BLUEPRINT.md for the state→region mapping). If the script fails because these files are missing, read the script source to understand what it needs, reconstruct the lookup from the state codes in the panel, and re-run.

---

## Step 3 — Script 11: Spatial Weights

```bash
python scripts/11_build_spatial_weights.py
```

**Validate:**
- Output: `data/processed/spatial_weights_queen.gal`
- N obs = 2,478
- 52 islands (zero Queen neighbors)

---

## Step 4 — Script 12: LISA (1,584 runs, ~45–90 min)

```bash
python scripts/12_compute_lisa_monthly.py
```

**Validate:**
- Output: `data/processed/lisa_monthly_results.parquet` (3,925,152 rows = 2,478 × 4 statuses × 3 sexes × 132 months)
- Also produces: `morans_i_monthly.csv`, `hh_clusters_monthly.parquet`, `hh_regional_composition.csv`, `hh_cross_tabulation_latest.csv`
- All 5 cluster labels present (HH, LL, HL, LH, NS)
- All Moran's I p-values < 0.05 for Total and Not Located

**Note:** This script may also need `region` and `is_bajio` to compute `hh_regional_composition.csv`. If it reads those from the panel, no problem. If it reads from a separate lookup file that no longer exists, see the note in Step 2.

---

## Step 5 — Script 13: Concentration

```bash
python scripts/13_compute_concentration.py
```

**Validate:**
- Output: `data/processed/concentration_monthly.csv` (528 rows = 4 statuses × 132 months)
- Gini in [0, 1], HHI in [0, 1]

---

## Step 6 — Script 14: Figures (WITH ALL FIXES)

### BEFORE running, read `scripts/14_generate_figures.py` and apply these edits:

### FIX 1 — All cross-section snapshots → June 2025

Find all references to the cross-section period. Change:
- Any `year=2024, month=12` or `year=2025, month=12` → `year=2025, month=6`
- Any title/label strings "December 2024" or "December 2025" → "June 2025"
- Bookend early period: `year=2015, month=6` ("June 2015")

This affects: **Fig 5** (LISA maps), **Fig 7** (bookend comparison), **Fig 8** (sex maps)

Figures using full 132-month time series are NOT changed: **Fig 1, 2, 4, 6**

### FIX 2 — Fig 3: Replace Lorenz curves with Gini time series

Replace the entire Lorenz curve function. The new Fig 3:

- **4 lines** (one per status: Total, Not Located, Located Alive, Located Dead)
- **X-axis:** 132 months (Jan 2015 – Dec 2025)
- **Y-axis:** Gini coefficient
- **Data source:** `data/processed/concentration_monthly.csv`
- **Annotations:** OLS trend slope (per decade) and significance for each status
- **Title:** "Gini Coefficient of Disappearance Case Counts by Outcome Status, 2015–2025"
- **Horizontal reference line** at Gini = 0.90
- **Output:** `manuscript/figures/fig3_gini_time_series.{pdf,png}`

### FIX 3 — Fig 5: LL suppressed to grey

```python
lisa_colors = {"HH": "#d7191c", "HL": "#fdae61", "LH": "#abd9e9", "LL": "#D9D9D9", "NS": "#f0f0f0"}
```

Legend label: "LL (suppressed)" or "LL (not interpreted)"

### FIX 4 — Fig 6: Add Centro line

Three regions instead of two:
- **Norte:** solid line
- **Bajío:** dashed line
- **Centro:** solid line, distinct color (`#2ca02c` green or `#9467bd` purple)

Data source: `data/processed/hh_regional_composition.csv` (produced by Script 12).

Add OLS slope annotations (munis/yr, p-value) for all three lines in each panel.

### FIX 5 — NEW Fig 9: Regional HH Heatmap

Add a new function:

- **Data:** `data/processed/lisa_monthly_results.parquet`, filter `sex == "total"`, `cluster_label == "HH"`, `month == 6`
- **Join** with `data/processed/panel_monthly_counts.parquet` for `region` and `is_bajio` (join on cvegeo, deduplicate to get one row per municipality)
- **Aggregate:** count HH municipalities per (year, region, status_id) for 11 June snapshots (2015–2025)
- **Layout:** 2×2 subplot grid (one panel per status)
- **Each panel:** Heatmap, y-axis = 6 groups (5 regions + Bajío), x-axis = 11 years, color = HH count, annotated cells
- **Color scale:** Sequential (e.g., YlOrRd), shared across panels
- **Output:** `manuscript/figures/fig9_regional_hh_heatmap.{pdf,png}`

### After all edits:

```bash
python scripts/14_generate_figures.py
```

**Validate:** 9 figures in `manuscript/figures/` (fig1–fig9), each in PDF + PNG, 300 DPI, non-zero file size.

---

## Step 7 — Script 15: Tables

### BEFORE running, read `scripts/15_generate_tables.py` and apply:

**All cross-section tables → June 2025** (year=2025, month=6):
- Table 4 (LISA classification): Jun 2025
- Table 5 (HH cross-tabulation / Jaccard): Jun 2025
- Table 7 (sex HH counts): Jun 2025

Tables using full time series are unchanged: Tables 1, 2, 3, 6.

```bash
python scripts/15_generate_tables.py
```

**Validate:** All .tex files in `manuscript/tables/`, non-zero size, compilable LaTeX.

---

## Step 8 — Post-Run Validation

Write to `logs/rerun_2026-04-06.md` (append):

1. **Row counts:** Panel, LISA, concentration — match expected values
2. **Headline numbers (Jun 2025 cross-section):**
   - Jaccard NL↔LD (Jun 2025)
   - Jaccard LA↔LD (Jun 2025)
   - HH municipality counts per status (Jun 2025)
   - Centro NL slope (full 132 months)
   - Bajío Total slope (full 132 months)
3. **Figure inventory:** All 9 figures with file sizes
4. **Table inventory:** All tables with file sizes

---

## Step 9 — Regenerate Verification Reports

The reports in `reports/paper1_verification/` are from the March 18 run and are now stale. Regenerate the executive summary with June 2025 reference period.

Compute and write to `reports/paper1_verification/08_executive_summary_v2.md`:

1. How many municipalities in the analytical sample?
2. Jaccard NL↔LD (Jun 2025)
3. Which region has the largest positive HH trend slope for each status?
4. Is the "rising Bajío" hypothesis supported? (yes/no + slope + p)
5. Does Centro show significant HH expansion? Monthly and annual?
6. What percentage of municipalities account for 50% of NL cases in Jun 2025?
7. Male vs female HH Jaccard for Not Located (Jun 2025)
8. Is there a statistical power problem for female Located Dead LISA?
9. Are key findings robust to reference period? (Jun 2025 vs Jun 2024 Jaccard)
10. Total LISA runs performed

---

## Step 9.5 — CED-Aligned State-Level HH Analysis (Post-Processing)

**Context:** On April 2, 2026, the UN Committee on Enforced Disappearances (CED) issued Decision CED/C/MEX/A.34/D/1, concluding that enforced disappearances in Mexico constitute crimes against humanity via "multiple widespread or systematic attacks at different moments and in different parts of the territory." This step extracts state-level HH dynamics from the LISA output to align our findings with the CED's geographic claims.

**No new LISA computation.** Post-processing on `data/processed/lisa_monthly_results.parquet`.

### Task 9.5.1 — State-Level HH Time Series

From `lisa_monthly_results.parquet`, filter `sex == "total"` and `cluster_label == "HH"`. Join with `panel_monthly_counts.parquet` to get `cve_estado` and state name. Count HH municipalities per month per status for these 8 CED-named states:

| State | cve_estado | CED temporal claim | Region |
|-------|-----------|-------------------|--------|
| Jalisco | 14 | "currently highest number of disappeared" | Centro-Norte |
| Guanajuato | 11 | "eightfold increase since 2017", 723 clandestine graves | Centro |
| Coahuila | 05 | Patterns documented 2009–2016 | Norte |
| Veracruz | 30 | Patterns documented 2010–2016 | Sur |
| Nayarit | 18 | Patterns documented 2011–2017 | Norte-Occidente |
| Tabasco | 27 | "exponential increase 2024–2025, girls and young women" | Sur |
| Nuevo León | 19 | Named in civil society contributions | Norte |
| Estado de México | 15 | Named in civil society contributions | Centro |

**Output:** `data/processed/ced_state_hh_timeseries.csv` (columns: `cve_estado, state, status_id, year, month, n_hh_munis`)

### Task 9.5.2 — CED Temporal Alignment Table

For each CED-named state × status:
- HH municipality count in Jun 2015 and Jun 2025
- Peak HH month and count across 132 months
- OLS slope (munis/year) with p-value
- Whether peak aligns with CED's claimed temporal window

**Output:** `data/processed/ced_temporal_alignment.csv` and `reports/paper1_verification/10_ced_alignment.md`

### Task 9.5.3 — CED State-Level Figure (Fig 10)

- **Layout:** 2×4 grid (8 panels, one per CED-named state)
- **Each panel:** 4 lines (one per status), x = 132 months, y = HH municipality count
- **Annotations:** Vertical shaded bands for CED's claimed temporal windows (e.g., Coahuila 2009–2016 → shade Jan 2015 – Dec 2016)
- **Title:** "HH Cluster Municipality Counts in CED-Named States, 2015–2025"
- **Output:** `manuscript/figures/fig10_ced_states.{pdf,png}` (300 DPI)

Zero HH lines should appear as flat zero — this is informative.

### Task 9.5.4 — Tabasco Sex Disaggregation Check

CED flags Tabasco for "girls and young women as principal victims" in 2024–2025. Extract:
- Tabasco (cve_estado=27) HH counts for female Not Located and female Located Alive, monthly, 2023–2025
- Compare to male HH counts same state/period
- Report whether female-specific clustering emerges

**Output:** Append to `reports/paper1_verification/10_ced_alignment.md`

---

## Step 10 — Git Commit

```bash
git add -A
git commit -m "rerun: full pipeline with April 2026 re-scrape + figure fixes

Data:
- Fresh RNPDNO scrape (2026-04-06), same period Jan 2015 – Dec 2025
- Cross-section reference: June 2025 (not December)
- data/processed/ wiped and regenerated from scratch

Figure fixes:
- Fig 3: Lorenz curves → Gini time series (132 months × 4 statuses)
- Fig 5: LL suppressed to grey (island artifact)
- Fig 6: Centro trend line added (largest HH slope, all statuses)
- NEW Fig 9: Regional HH heatmap (11 June snapshots × 6 regions × 4 statuses)

CED alignment (post-processing):
- State-level HH time series for 8 CED-named states
- Temporal alignment with CED-claimed attack windows
- NEW Fig 10: CED states small-multiples
- Tabasco female disaggregation check

Tables:
- All cross-section tables updated to June 2025
- All numbers regenerated from fresh data"
```

---

## CONSTRAINTS

1. **Polars mandatory** for all data wrangling. Pandas only for GIS/PySAL interfaces.
2. **EPSG:6372** for all spatial operations.
3. **No sentinel cvegeo** (99998, XX998, XX999) in any output.
4. **300 DPI**, PDF + PNG for all figures.
5. **Do NOT modify scripts 01–09.** Only edit scripts 10–15.
6. **Do NOT install new packages.**
7. **Newey-West HAC** (bandwidth=12) for OLS trends on monthly data.
8. **999 permutations** for all LISA/Moran's I.
9. **α = 0.05** for significance.
10. **Min cluster size = 3** for connected-component HH clusters.

---

## IF SOMETHING FAILS

1. **pCloud symlink broken:** Stop. Log error. Filesystem not mounted.
2. **Script crashes because a file from `data/processed/` is missing:** This means a prior script in the pipeline failed. Do NOT look for stale copies elsewhere. Fix the failing prior script first.
3. **Script crashes because a lookup file (Bajío list, regional classification, municipality metadata) is missing:** These were previously in `data/processed/` and have been deleted. Read the script source to understand what it needs, reconstruct from the panel or shapefile, and re-run.
4. **LISA takes >3 hours:** Something is wrong. Check municipality count (should be 2,478, not more).
5. **Figure generation fails:** Generate what you can. Log which figures failed and why.
6. **Any data anomaly:** Log prominently with "⚠️ ANOMALY" prefix.

---

## EXECUTION ORDER SUMMARY

```
0.  Verify data symlinks
1.  Pre-flight check (log only)
2.  Script 10 (panel)
3.  Script 11 (weights)
4.  Script 12 (LISA — long step, ~45-90 min)
5.  Script 13 (concentration)
6.  Edit + run Script 14 (figures — 5 changes + 1 new)
7.  Edit + run Script 15 (tables — June cross-sections)
8.  Post-run validation
9.  Regenerate verification reports
9.5 CED state-level HH analysis (post-processing)
10. Git commit
```

Total estimated time: 2–4 hours. The LISA step dominates.
