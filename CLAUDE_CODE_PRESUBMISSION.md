# CLAUDE CODE TASK — Pre-Submission Robustness (2026-04-09, v2)

**Project root:** `/home/marco/workspace/work/rnpdno-population-bands/`
**Environment:** `conda activate rnpdno_eda` (Python 3.10)

---

## CONTEXT

JQC paper in revision. External review identified 4 major issues + 7 minor. The Bajío regional
definition has been changed from ~200 CESOP municipalities to a **29-municipality industrial
corridor** based on Medina-Fernández et al. (2023, DOI: 10.3390/earth4010007) and the SUN 2018
catalog. This requires rerunning Figure 5, Table 6, and the breakpoint analysis.

**Critical data paths:**
- LISA results: `data/processed/lisa_monthly_results.parquet`
- Panel: `data/processed/monthly_panel.parquet`
- Weights: `data/processed/` (`.gal` or `.pkl`)
- Population (2024 snapshot): `~/pCloudDrive/Datasets/socioeconomic/conapo_proyecciones/processed/poblacion_2024_municipal.parquet`
- Full population series (1990-2070): `~/pCloudDrive/Datasets/socioeconomic/conapo_proyecciones/raw/poblacion_1990_2070_municipal.parquet`
- Master municipal: `~/pCloudDrive/Datasets/socioeconomic/processed/master_municipal_2024.parquet`

---

## BAJÍO CORRIDOR DEFINITION (29 municipalities)

Source: Medina-Fernández et al. (2023), "Surface Urban Heat Island... El Bajío Industrial
Corridor", Earth 4(1):93-150, DOI: 10.3390/earth4010007. Delimitation based on CONAPO/
SEDESOL/SEGOB, Catálogo Sistema Urbano Nacional 2018.

The corridor comprises 10 metropolitan areas + 4 conurbations. All 14 entities are connected
by the national highway axis from San Juan del Río (Querétaro) to Aguascalientes (Pérez
Calderón, 2015, EURE).

**Create this as a CSV file: `data/external/bajio_corridor_municipalities.csv`**

```csv
cvegeo,municipality,state,cve_estado,cve_mun,zm_entity,entity_type
01001,Aguascalientes,Aguascalientes,1,1,ZM Aguascalientes,metropolitana
01005,Jesús María,Aguascalientes,1,5,ZM Aguascalientes,metropolitana
01011,San Francisco de los Romo,Aguascalientes,1,11,ZM Aguascalientes,metropolitana
11003,San Miguel de Allende,Guanajuato,11,3,Conurbación San Miguel de Allende,conurbacion
11005,Apaseo el Grande,Guanajuato,11,5,ZM Querétaro,metropolitana
11007,Celaya,Guanajuato,11,7,ZM Celaya,metropolitana
11009,Comonfort,Guanajuato,11,9,ZM Celaya,metropolitana
11011,Cortázar,Guanajuato,11,11,ZM Celaya,metropolitana
11015,Guanajuato,Guanajuato,11,15,ZM Guanajuato,metropolitana
11017,Irapuato,Guanajuato,11,17,Conurbación Irapuato,conurbacion
11020,León,Guanajuato,11,20,ZM León,metropolitana
11021,Moroleón,Guanajuato,11,21,ZM Moroleón-Uriangato,metropolitana
11023,Pénjamo,Guanajuato,11,23,ZM La Piedad-Pénjamo,metropolitana
11025,Purísima del Rincón,Guanajuato,11,25,ZM San Francisco del Rincón,metropolitana
11027,Salamanca,Guanajuato,11,27,Conurbación Salamanca,conurbacion
11031,San Francisco del Rincón,Guanajuato,11,31,ZM San Francisco del Rincón,metropolitana
11037,Silao de la Victoria,Guanajuato,11,37,ZM León,metropolitana
11041,Uriangato,Guanajuato,11,41,ZM Moroleón-Uriangato,metropolitana
11044,Villagrán,Guanajuato,11,44,ZM Celaya,metropolitana
16055,La Piedad,Michoacán,16,55,ZM La Piedad-Pénjamo,metropolitana
22006,Corregidora,Querétaro,22,6,ZM Querétaro,metropolitana
22008,Huimilpan,Querétaro,22,8,ZM Querétaro,metropolitana
22011,El Marqués,Querétaro,22,11,ZM Querétaro,metropolitana
22014,Querétaro,Querétaro,22,14,ZM Querétaro,metropolitana
22017,San Juan del Río,Querétaro,22,17,Conurbación San Juan del Río,conurbacion
24010,Ciudad Fernández,San Luis Potosí,24,10,ZM Rioverde,metropolitana
24024,Rioverde,San Luis Potosí,24,24,ZM Rioverde,metropolitana
24028,San Luis Potosí,San Luis Potosí,24,28,ZM San Luis Potosí,metropolitana
24035,Soledad de Graciano Sánchez,San Luis Potosí,24,35,ZM San Luis Potosí,metropolitana
```

**First step of every task below:** Load this CSV and use it as the Bajío corridor flag.
Replace any existing CESOP-based "Bajío" flag in the pipeline with this 29-municipality set.

---

## EXECUTION ORDER

```
0. Create bajio_corridor_municipalities.csv
1. Task 1a (population comparison)  ← BLOCKING
   → passes → footnote, skip 1b → Task 2
   → fails  → Task 1b → Task 2
2. Task 2 (FDR correction)
3. Task 3 (Bajío corridor trend recomputation — NEW, replaces old breakpoint task)
4. Task 4 (Poisson robustness)
5. Task 5 (Figure 5 regeneration with new Bajío)
6. Task 6 (Table 6 regeneration with new Bajío)
7. Task 7 (Figure/Table consistency check)
8. Git commit
```

---

## TASK 0 — Create Bajío Corridor Municipality File

Save the CSV above to `data/external/bajio_corridor_municipalities.csv`.
Verify: 29 rows, 5 states (AGS=3, GTO=16, MICH=1, QRO=5, SLP=4), no duplicates.

**MANDATORY: Verify all 28 cvegeo codes against AGEEML.**
The INEGI catalog should be at `data/external/` or available via the project's geoparquet:

```python
import polars as pl

# Option 1: check against the municipal geoparquet used in the pipeline
gdf = pl.read_parquet("data/external/municipios_2024.geoparquet", columns=["cvegeo", "NOMGEO"])
bajio = pl.read_csv("data/external/bajio_corridor_municipalities.csv")

# Left join: every bajio cvegeo must match
joined = bajio.join(gdf, on="cvegeo", how="left")
missing = joined.filter(pl.col("NOMGEO").is_null())
if len(missing) > 0:
    print("⚠️ FATAL: cvegeo codes not found in AGEEML:")
    print(missing.select("cvegeo", "municipality"))
    # STOP. Fix the CSV before proceeding.
else:
    print(f"✅ All {len(bajio)} cvegeo codes verified against AGEEML")

# Also verify names roughly match (accent differences are OK)
print(joined.select("cvegeo", "municipality", "NOMGEO"))
```

If any cvegeo fails: STOP. Do not proceed. Flag for Marco.
Common issues: zero-padding (e.g., `01001` vs `1001`), post-2020 municipality splits.

Also verify all 28 cvegeo appear in the LISA results:
```python
lisa = pl.read_parquet("data/processed/lisa_monthly_results.parquet", columns=["cvegeo"]).unique()
in_lisa = bajio.join(lisa, on="cvegeo", how="semi")
print(f"Matched in LISA: {len(in_lisa)}/28")
```
If < 28: check dtype (int vs str) and zero-padding.

---

## TASK 1a — Population Distribution Comparison (BLOCKING, ~30 min)

**Goal:** Test if Located Dead HH municipalities are systematically larger than Not Located HH
municipalities. If not → population cannot explain Jaccard → footnote → done.

1. Load `lisa_monthly_results.parquet`, filter June 2025, sex=total, α=0.05
2. Extract HH cvegeo sets per status (0, 7, 2, 3)
3. Join with 2025 population on cvegeo (use `poblacion_2024_municipal.parquet` or
   the full series file for 2025 projections)
4. Per HH set: N, median, P25, P75, min, max, mean population
5. Pairwise Mann-Whitney U tests (3 key pairs):
   - LD HH vs NL HH
   - LD HH vs LA HH
   - NL HH vs LA HH
   - Report: U, p-value, rank-biserial r
6. Kolmogorov-Smirnov for each pair
7. Box plot: population distributions by HH status

**Decision:**
- ALL pairwise p > 0.05 → STOP. Write footnote. Skip Task 1b.
- LD vs NL p < 0.05 → Proceed to Task 1b.

**Output:** `reports/paper1_verification/11_population_robustness.md`

---

## TASK 1b — EB-Smoothed Rate LISA (ONLY IF 1a FAILS)

Adaptive Empirical Bayes smoothing per Escobar et al. (2026), Public Health 254:106238,
Section 2.2.2. Self-cite for methodology.

**7 population bands (NEW: "millonaria" > 1M):**

| Band | Range | α |
|------|-------|---|
| Community | < 2,500 | 8,000 |
| Rural | 2,500–15,000 | 4,000 |
| Semi-urban | 15,000–50,000 | 1,500 |
| Small city | 50,000–150,000 | 800 |
| Medium city | 150,000–500,000 | 400 |
| City | 500,000–1,000,000 | 200 |
| Millonaria | > 1,000,000 | 100 |

The 6 original bands (α=8000 to α=200) are from the published VAWRI paper Table 2.
The 7th "millonaria" band (α=100) is new — near-zero smoothing for municipalities
with populations > 1M where counts are inherently stable.

**Steps:**
1. Join June 2025 counts with 2025 population
2. Assign population band per municipality
3. Crude rates per 100,000 per status × municipality
4. Per band: winsorised (P10/P90) population-weighted prior r_band
5. EB weight: wi = Ni / (Ni + α_band)
6. Smoothed rate: r̃i = wi·ri + (1−wi)·r_band. Zero counts stay zero.
7. LISA on smoothed rates, June 2025, 4 statuses, total sex only
   - Same weights matrix, 999 perms, α=0.05, min-cluster=3 BFS
8. Jaccard on rate-based HH sets
9. Compare with raw-count Jaccard

**Output:** Append to `11_population_robustness.md`

---

## TASK 2 — FDR-Corrected LISA Thresholds (PRIORITY 2, ~2 hours)

1. Load LISA results, June 2025, 4 statuses × total sex
2. Per status: extract pseudo-p-values for all 2,478 municipalities
3. Apply Benjamini-Hochberg FDR at q = 0.05
4. Recompute HH sets (FDR-significant only) + min-cluster=3 BFS
5. Jaccard on FDR-corrected HH sets
6. Compare with uncorrected

**Note:** α=0.001 showing zero survivors is a permutation resolution artefact (999 perms →
min achievable p = 0.001). State explicitly. If reviewer demands it, increase to 9,999
permutations for June 2025 cross-section only (4 runs).

**Output:** `reports/paper1_verification/12_fdr_correction.md`

---

## TASK 3 — Bajío Corridor Trend Recomputation (PRIORITY 1, ~3 hours)

**This is new.** The old Bajío trend used ~200 CESOP municipalities. Now we use 29.

### 3a. Recompute HH count time series for new Bajío corridor

1. Load `lisa_monthly_results.parquet` (full 132 months)
2. Load `data/external/bajio_corridor_municipalities.csv`
3. For each month × status × sex=total:
   - Count HH municipalities that are IN the 29-municipality corridor
   - This gives: monthly HH count within Bajío corridor, per status
4. Save as `data/processed/bajio_corridor_hh_timeseries.csv`

### 3b. Fit trend models on new Bajío corridor series

For each status (Total, NL, LA, LD):
1. OLS with Newey-West HAC (bandwidth=12): HH_count ~ month_index
2. Report slope, SE, p-value, CI

### 3c. Breakpoint test on Bajío corridor Total

1. Visual inspection: does the 29-municipality series still show inverted-U?
2. If yes: test structural break using `ruptures` (Bai-Perron, pen=BIC)
   OR Chow test at candidates 2018-01 through 2021-12
3. If breakpoint confirmed:
   - Fit two-segment piecewise OLS with Newey-West HAC
   - Report: breakpoint date, pre-break slope + CI, post-break slope + CI
4. If the series is monotonic (no inverted-U with 28 munis): report linear slope only

### 3d. Compare old vs new Bajío

Create comparison table:
| Metric | Old Bajío (~200 CESOP) | New Bajío (29 corridor) |
|--------|----------------------|------------------------|
| Total slope | -1.09/yr (p=0.024) | ??? |
| NL slope | ... | ??? |
| LA slope | ... | ??? |
| LD slope | ... | ??? |
| Breakpoint | none tested | ??? |

**Output:** `reports/paper1_verification/13_bajio_corridor.md`

---

## TASK 4 — Poisson Trend Robustness (PRIORITY 5, ~1 hour)

1. For 4 key series: Centro NL, Centro Total, **new Bajío corridor Total**, Norte LD
   - Poisson regression: count ~ month_index, HAC robust SE
   - Compare sign + significance with OLS
2. Table: Series | OLS slope | OLS p | Poisson IRR | Poisson p

**Output:** Append to `11_population_robustness.md`

---

## TASK 5 — Regenerate Figure 5 with New Bajío (PRIORITY 1, ~2 hours)

Figure 5 currently shows HH municipality trends for Norte vs Bajío vs Centro.
The "Bajío" line must be recomputed using the 29-municipality corridor.

1. Load existing Figure 5 generation code from `scripts/14_generate_figures.py`
2. Replace the old Bajío municipality flag with the new 29-municipality set
3. Keep Norte and Centro definitions unchanged (CESOP regions)
4. Regenerate figure with:
   - Three lines: Norte, Bajío (29 corridor), Centro
   - OLS slope annotations updated with new values
   - Same formatting, 300 DPI, PDF + PNG
5. Save to `manuscript/figures/fig5_hh_trend_norte_bajio.{pdf,png}`

**IMPORTANT:** Do NOT modify the script's Norte or Centro definitions. Only change Bajío.
Propose the change as a diff first (per code consent policy), then apply after review.
If running autonomously, make a backup of the original script first:
`cp scripts/14_generate_figures.py scripts/14_generate_figures.py.bak`

**Output:** Updated figure + slope values logged

---

## TASK 6 — Regenerate Table 6 with New Bajío (PRIORITY 1, ~1 hour)

Table 6 contains trend slopes for all region × status combinations.
The Bajío rows must be recomputed.

1. Load existing Table 6 generation code from `scripts/15_generate_tables.py`
2. Replace the old Bajío municipality flag with the new 29-municipality set
3. Recompute Bajío rows only (Total, NL, LA, LD)
4. Keep all other regions unchanged
5. Regenerate .tex file

**Same code consent policy as Task 5.**

**Output:** Updated `manuscript/tables/table6_trend_slopes.tex`

---

## TASK 7 — Figure 5 vs Table 6 Consistency Check (~15 min)

After Tasks 5 and 6, verify all slope annotations in Figure 5 match Table 6 values.
Flag any discrepancy > 0.01.

**Output:** Console log or append to `13_bajio_corridor.md`

---

## REFERENCES FOR METHODS SECTION

When documenting the Bajío corridor in code comments or reports, use:

```
Bajío industrial corridor operationalization:
- Medina-Fernández, S.L. et al. (2023). Earth, 4(1), 93-150. DOI: 10.3390/earth4010007
  (14 urban entities = 10 ZMs + 4 conurbations from SUN 2018)
- CONAPO, SEDESOL, SEGOB (2018). Catálogo Sistema Urbano Nacional 2018.
  (municipality compositions per ZM)
- Pérez Calderón, P. (2015). EURE, 41(124), 243-267.
  (corridor concept: "San Juan del Río to Aguascalientes" highway axis)
```

---

## GIT COMMIT

```bash
git add -A
git commit -m "pre-submission: new Bajío corridor (29 munis) + robustness checks

- New Bajío definition: 29 municipalities from Medina-Fernández et al. (2023)
  SUN 2018, replacing ~200 CESOP flag
- Task 1a: Population distribution comparison of HH sets (Mann-Whitney U)
- Task 1b: EB-smoothed rate LISA (if 1a fails), 7 bands incl. millonaria
- Task 2: FDR-corrected LISA thresholds (BH q=0.05)
- Task 3: Bajío corridor trend recomputation + breakpoint test
- Task 4: Poisson trend robustness vs OLS
- Task 5: Figure 5 regenerated with new Bajío
- Task 6: Table 6 regenerated with new Bajío
- All outputs in reports/paper1_verification/"
```
