"""
WP1 — Data Integrity and Panel Reconstruction
==============================================
Audit notebook for RNPDNO manuscript pre-submission audit.
Every result is written to audit/outputs/WP1_*.csv with companion .json metadata.

Marco's pivot-table finding:
  After excluding cvegeo == 99998 and cvegeo == 99999 only,
  NL total = 92,321  (male=71,848, female=20,285, undefined=188)
  Manuscript JQC claims NL = 89,631 after sentinel exclusion.
  → scripts use broader definition: all cvegeo ending in 998 or 999.
  WP1 must characterise both exclusion definitions and identify ground truth.
"""

import hashlib
import json
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd

# ── paths ────────────────────────────────────────────────────────────────────
PROJECT_ROOT = Path("/home/marco/workspace/work/rnpdno-population-bands")
DATA_RAW     = PROJECT_ROOT / "data" / "raw"
DATA_PROC    = PROJECT_ROOT / "data" / "processed"
DATA_EXT     = PROJECT_ROOT / "data" / "external"
AUDIT_DIR    = PROJECT_ROOT / "audit"
OUT_DIR      = AUDIT_DIR / "outputs"
OUT_DIR.mkdir(parents=True, exist_ok=True)

AUDIT_SEED      = 42
RUN_TIMESTAMP   = datetime.now().isoformat()
AUDIT_LOG: dict = {"seed": AUDIT_SEED, "timestamp": RUN_TIMESTAMP, "hashes": {}}

CSV_FILES = {
    "total":     "rnpdno_total.csv",
    "nl":        "rnpdno_disappeared_not_located.csv",
    "la":        "rnpdno_located_alive.csv",
    "ld":        "rnpdno_located_dead.csv",
}

STATUS_LABELS = {
    "total": "Total",
    "nl":    "Not Located",
    "la":    "Located Alive",
    "ld":    "Located Dead",
}

# manuscript expected values (JQC) for cross-reference
JQC = {
    "row_counts":         {"total": 57_373, "nl": 34_617, "la": 37_379, "ld": 9_936},
    "persons_incl_sent":  {"total": 269_507, "nl": 92_486, "la": 160_901, "ld": 15_777},  # EDA
    "persons_excl_sent":  {"total": 263_402, "nl": 89_631, "la": 157_990, "ld": 15_438},  # JQC
    "excluded_persons":   {"total": 6_105, "nl": 2_855, "la": 2_911, "ld": 339},           # JQC
    "nonzero_rows":       {"total": 55_568, "nl": 33_359, "la": 36_541, "ld": 9_696},      # JQC
    "june2025_active":    {"total": 573, "nl": 357, "la": 391, "ld": 91},                  # EDA
    "june2025_counts":    {"total": 3_098, "nl": 1_173, "la": 1_788, "ld": 144},           # EDA
    "june2025_zero_rate": {"total": 0.770, "nl": 0.857, "la": 0.842, "ld": 0.963},        # JQC
    "gini_mean":          {"total": 0.935, "nl": 0.946, "la": 0.955, "ld": 0.979},
}

# Marco's pivot-table result (narrow exclusion: cvegeo == 99998 or == 99999)
MARCO_PIVOT = {"nl": {"male": 71_848, "female": 20_285, "undefined": 188, "total": 92_321}}

SEX_LABEL_MAP = {0: "male", 1: "female", 2: "undefined", 9: "undefined"}

results: list[dict] = []  # accumulate all check rows

# ─────────────────────────────────────────────────────────────────────────────
def pass_fail(observed, expected, tol_pct: float = 0.5) -> str:
    if expected is None:
        return "N/A"
    if isinstance(expected, float):
        return "PASS" if abs(observed - expected) / max(abs(expected), 1e-9) <= tol_pct / 100 else "FAIL"
    return "PASS" if observed == expected else "FAIL"


def log_result(task: str, check: str, observed, expected, note: str = "") -> None:
    verdict = pass_fail(observed, expected)
    row = {
        "task":     task,
        "check":    check,
        "observed": observed,
        "expected": expected,
        "verdict":  verdict,
        "note":     note,
    }
    results.append(row)
    marker = "✅" if verdict == "PASS" else ("⚠️" if verdict == "N/A" else "❌")
    print(f"  {marker}  {task} | {check}: observed={observed}  expected={expected}  [{verdict}]  {note}")


# ─────────────────────────────────────────────────────────────────────────────
# PRE-TASK: hash raw CSVs
# ─────────────────────────────────────────────────────────────────────────────
print("\n=== PRE-TASK: Source Integrity ===")
for key, fname in CSV_FILES.items():
    fpath = DATA_RAW / fname
    assert fpath.exists(), f"Missing: {fpath}"
    with open(fpath, "rb") as fh:
        h = hashlib.sha256(fh.read()).hexdigest()
    AUDIT_LOG["hashes"][fname] = h
    print(f"  {fname}: {h}")

print(f"\n  Timestamp: {RUN_TIMESTAMP}")
(OUT_DIR / "WP1_audit_log.json").write_text(json.dumps(AUDIT_LOG, indent=2))

# ─────────────────────────────────────────────────────────────────────────────
# LOAD RAW CSVs
# ─────────────────────────────────────────────────────────────────────────────
print("\n=== Loading CSVs ===")
dfs: dict[str, pd.DataFrame] = {}
for key, fname in CSV_FILES.items():
    df = pd.read_csv(DATA_RAW / fname, dtype={"cvegeo": str})
    dfs[key] = df
    print(f"  {key}: {len(df):,} rows × {len(df.columns)} cols  | cols: {list(df.columns)}")

# ─────────────────────────────────────────────────────────────────────────────
# TASK 1.1 — Row counts and schema
# ─────────────────────────────────────────────────────────────────────────────
print("\n=== TASK 1.1: Row counts and schema ===")
for key in CSV_FILES:
    n = len(dfs[key])
    log_result("1.1", f"row_count_{key}", n, JQC["row_counts"][key])

# ─────────────────────────────────────────────────────────────────────────────
# TASK 1.2 — Person-registrations BEFORE sentinel exclusion
# ─────────────────────────────────────────────────────────────────────────────
print("\n=== TASK 1.2: Person-registrations (ALL rows, sum of 'total') ===")
for key in CSV_FILES:
    df = dfs[key]
    total_col = "total" if "total" in df.columns else df.columns[-1]
    persons = int(df[total_col].sum())
    log_result("1.2", f"persons_incl_sentinels_{key}", persons, JQC["persons_incl_sent"][key])

# ─────────────────────────────────────────────────────────────────────────────
# TASK 1.3 — Sentinel exclusion: characterise both definitions
# ─────────────────────────────────────────────────────────────────────────────
print("\n=== TASK 1.3: Sentinel exclusion — two definitions ===")

def narrow_mask(df: pd.DataFrame) -> pd.Series:
    """Marco's definition: cvegeo == '99998' or '99999'."""
    return df["cvegeo"].isin(["99998", "99999"])

def broad_mask(df: pd.DataFrame) -> pd.Series:
    """JQC definition: cvegeo ending in '998' or '999' OR cvegeo == '99998'."""
    return df["cvegeo"].str.endswith("998") | df["cvegeo"].str.endswith("999")

print("\n  -- Narrow exclusion (cvegeo == 99998 or 99999) --")
narrow_exclusions: dict[str, dict] = {}
for key in CSV_FILES:
    df = dfs[key]
    total_col = "total" if "total" in df.columns else df.columns[-1]
    mask = narrow_mask(df)
    excl_rows    = int(mask.sum())
    excl_persons = int(df.loc[mask, total_col].sum())
    kept_persons = int(df.loc[~mask, total_col].sum())
    narrow_exclusions[key] = {"excl_rows": excl_rows, "excl_persons": excl_persons, "kept_persons": kept_persons}
    print(f"  {key}: excluded rows={excl_rows}, excluded persons={excl_persons}, kept persons={kept_persons:,}")

print("\n  -- Broad exclusion (cvegeo ends with 998 or 999) --")
broad_exclusions: dict[str, dict] = {}
for key in CSV_FILES:
    df = dfs[key]
    total_col = "total" if "total" in df.columns else df.columns[-1]
    mask = broad_mask(df)
    excl_rows    = int(mask.sum())
    excl_persons = int(df.loc[mask, total_col].sum())
    kept_persons = int(df.loc[~mask, total_col].sum())
    broad_exclusions[key] = {"excl_rows": excl_rows, "excl_persons": excl_persons, "kept_persons": kept_persons}
    print(f"  {key}: excluded rows={excl_rows}, excluded persons={excl_persons}, kept persons={kept_persons:,}")
    log_result("1.3", f"persons_excl_sentinels_broad_{key}", kept_persons, JQC["persons_excl_sent"][key],
               note="broad exclusion (ends 998/999)")
    log_result("1.3", f"excl_persons_broad_{key}", excl_persons, JQC["excluded_persons"][key])

# Which sentinel cvegeo values exist?
print("\n  -- Distinct sentinel cvegeo values per CSV --")
for key in CSV_FILES:
    df = dfs[key]
    broad_mask_vals = broad_mask(df)
    sentinel_vals = df.loc[broad_mask_vals, "cvegeo"].value_counts().to_dict()
    print(f"  {key}: {sentinel_vals}")

# Cross-paper reconciliation: EDA "4,141 rows excluded" vs JQC "6,105 persons excluded"
print("\n  -- Marco pivot vs narrow exclusion (NL CSV) --")
df_nl = dfs["nl"]
total_col = "total" if "total" in df_nl.columns else df_nl.columns[-1]
# Check sex columns if they exist
sex_cols = [c for c in df_nl.columns if "sex" in c.lower() or "sexo" in c.lower()]
print(f"  NL columns: {list(df_nl.columns)}")
print(f"  Sex-like columns: {sex_cols}")

mask_narrow_nl = narrow_mask(df_nl)
kept_nl = df_nl.loc[~mask_narrow_nl]
print(f"  Narrow exclusion NL: kept {len(kept_nl):,} rows, {int(kept_nl[total_col].sum()):,} persons")
print(f"  Marco's pivot result: {MARCO_PIVOT['nl']}")

# ─────────────────────────────────────────────────────────────────────────────
# TASK 1.2b — Person-registrations AFTER broad sentinel exclusion
# ─────────────────────────────────────────────────────────────────────────────
print("\n=== TASK 1.2b: Person-registrations after broad exclusion ===")
for key in CSV_FILES:
    kept = broad_exclusions[key]["kept_persons"]
    log_result("1.2b", f"persons_after_broad_exclusion_{key}", kept, JQC["persons_excl_sent"][key])

# ─────────────────────────────────────────────────────────────────────────────
# TASK 1.4 — Non-zero cell counts
# ─────────────────────────────────────────────────────────────────────────────
print("\n=== TASK 1.4: Non-zero cell counts (rows where total > 0, after broad exclusion) ===")
for key in CSV_FILES:
    df = dfs[key]
    total_col = "total" if "total" in df.columns else df.columns[-1]
    mask = ~broad_mask(df)
    nonzero = int((df.loc[mask, total_col] > 0).sum())
    log_result("1.4", f"nonzero_rows_after_exclusion_{key}", nonzero, JQC["nonzero_rows"][key])

# ─────────────────────────────────────────────────────────────────────────────
# TASK 1.5 — Unique municipality count (before exclusion)
# ─────────────────────────────────────────────────────────────────────────────
print("\n=== TASK 1.5: Unique cvegeo (pre-exclusion) ===")
unique_all = set()
for key in CSV_FILES:
    df = dfs[key]
    unique_set = set(df["cvegeo"].unique())
    unique_all |= unique_set
    n_unique = len(unique_set)
    print(f"  {key}: {n_unique:,} unique cvegeo")

# After broad exclusion
print("\n  After broad exclusion:")
unique_clean = set()
for key in CSV_FILES:
    df = dfs[key]
    mask = ~broad_mask(df)
    unique_set = set(df.loc[mask, "cvegeo"].unique())
    unique_clean |= unique_set
    n_unique = len(unique_set)
    print(f"  {key}: {n_unique:,} unique cvegeo")

print(f"\n  Union across all statuses (pre-exclusion): {len(unique_all):,}")
print(f"  Union across all statuses (post-exclusion): {len(unique_clean):,}")
log_result("1.5", "unique_muni_post_exclusion_union", len(unique_clean), 2_025,
           note="EDA reports 2,025 unique munis; JQC balanced panel has 2,478")

# ─────────────────────────────────────────────────────────────────────────────
# TASK 1.6 — Cross-status consistency: NL + LA + LD == Total
# ─────────────────────────────────────────────────────────────────────────────
print("\n=== TASK 1.6: Cross-status consistency (NL + LA + LD vs Total) ===")
dfs_clean: dict[str, pd.DataFrame] = {}
for key in CSV_FILES:
    df = dfs[key].copy()
    dfs_clean[key] = df[~broad_mask(df)].copy()

# Build merge key: cvegeo + year + month
def get_time_cols(df: pd.DataFrame):
    year_col  = [c for c in df.columns if "year" in c.lower() or "año" in c.lower()][0]
    month_col = [c for c in df.columns if "month" in c.lower() or "mes" in c.lower()][0]
    return year_col, month_col

year_col, month_col = get_time_cols(dfs_clean["total"])
total_col = "total" if "total" in dfs_clean["total"].columns else dfs_clean["total"].columns[-1]

print(f"  Time columns: year='{year_col}', month='{month_col}', total='{total_col}'")

agg_total = (dfs_clean["total"]
             .groupby(["cvegeo", year_col, month_col])[total_col].sum()
             .rename("total_from_total"))
agg_nl = (dfs_clean["nl"]
          .groupby(["cvegeo", year_col, month_col])[total_col].sum()
          .rename("total_nl"))
agg_la = (dfs_clean["la"]
          .groupby(["cvegeo", year_col, month_col])[total_col].sum()
          .rename("total_la"))
agg_ld = (dfs_clean["ld"]
          .groupby(["cvegeo", year_col, month_col])[total_col].sum()
          .rename("total_ld"))

consistency = (agg_total.reset_index()
               .merge(agg_nl.reset_index(), on=["cvegeo", year_col, month_col], how="outer")
               .merge(agg_la.reset_index(), on=["cvegeo", year_col, month_col], how="outer")
               .merge(agg_ld.reset_index(), on=["cvegeo", year_col, month_col], how="outer")
               .fillna(0))
consistency["sum_components"] = (consistency["total_nl"] +
                                  consistency["total_la"] +
                                  consistency["total_ld"])
consistency["residual"] = consistency["total_from_total"] - consistency["sum_components"]
nonzero_residual = (consistency["residual"].abs() > 0).sum()
max_residual = consistency["residual"].abs().max()
print(f"  Rows with non-zero residual: {nonzero_residual:,}")
print(f"  Max absolute residual: {max_residual}")
log_result("1.6", "cross_status_nonzero_residuals", int(nonzero_residual), 0,
           note=f"max residual = {max_residual}")
if nonzero_residual > 0:
    sample = consistency[consistency["residual"].abs() > 0].head(5)
    print("  Sample of inconsistent rows:")
    print(sample.to_string())
    sample.to_csv(OUT_DIR / "WP1_cross_status_inconsistencies.csv", index=False)

# ─────────────────────────────────────────────────────────────────────────────
# TASK 1.7 — June 2025 zero-inflation rates
# ─────────────────────────────────────────────────────────────────────────────
print("\n=== TASK 1.7: June 2025 zero-inflation ===")

# First establish what n_municipalities the panel uses (balanced = 2,478)
panel_path = DATA_PROC / "panel_monthly_counts.parquet"
panel = pd.read_parquet(panel_path)
print(f"  Panel shape: {panel.shape}")
print(f"  Panel columns: {list(panel.columns)}")

panel_munis = panel["cvegeo"].nunique() if "cvegeo" in panel.columns else None
print(f"  Unique cvegeo in panel: {panel_munis}")

# June 2025 in raw data (broad exclusion)
for key in CSV_FILES:
    df = dfs_clean[key]
    june25 = df[(df[year_col] == 2025) & (df[month_col] == 6)]
    n_june = len(june25)
    persons_june = int(june25[total_col].sum())
    active = int((june25[total_col] > 0).sum())
    log_result("1.7", f"june2025_active_{key}", active, JQC["june2025_active"][key],
               note=f"rows with total>0 in raw clean data")
    log_result("1.7", f"june2025_persons_{key}", persons_june, JQC["june2025_counts"][key])

# Zero-inflation rate using 2,478 denominator (JQC balanced panel)
print("\n  Zero-inflation with 2,478 denominator:")
for key in CSV_FILES:
    df = dfs_clean[key]
    june25 = df[(df[year_col] == 2025) & (df[month_col] == 6)]
    active = int((june25[total_col] > 0).sum())
    zero_rate = (2_478 - active) / 2_478
    log_result("1.7", f"june2025_zero_rate_{key}", round(zero_rate, 3),
               JQC["june2025_zero_rate"][key], note="denom=2,478")

# ─────────────────────────────────────────────────────────────────────────────
# TASK 1.8 — Female LD mean and zero rate
# ─────────────────────────────────────────────────────────────────────────────
print("\n=== TASK 1.8: Female LD mean and zero rate ===")
df_ld = dfs_clean["ld"]
sex_cols_ld = [c for c in df_ld.columns if "sex" in c.lower() or "sexo" in c.lower() or "femenin" in c.lower()]
print(f"  LD columns: {list(df_ld.columns)}")
print(f"  Sex-like columns: {sex_cols_ld}")

female_col = None
for c in df_ld.columns:
    if "fem" in c.lower() or "mujer" in c.lower() or c in ["1", "sexo_1"]:
        female_col = c
        break
# Try to detect by checking if value sums are lower (female is minority in LD)
if female_col is None:
    # look for columns with smaller totals that could be female
    numeric_cols = df_ld.select_dtypes(include="number").columns.tolist()
    print(f"  Numeric columns: {numeric_cols}")
else:
    female_mean = df_ld[female_col].mean()
    female_zero_rate = (df_ld[female_col] == 0).mean()
    print(f"  Female col '{female_col}': mean={female_mean:.4f}, zero_rate={female_zero_rate:.3f}")
    log_result("1.8", "female_ld_mean_per_muni_month", round(female_mean, 4), 0.0065)
    log_result("1.8", "female_ld_zero_rate", round(female_zero_rate, 3), 0.994)

# ─────────────────────────────────────────────────────────────────────────────
# TASK 1.9 — Reporting lag: Dec 2025 / Jul 2025 ratio
# ─────────────────────────────────────────────────────────────────────────────
print("\n=== TASK 1.9: Reporting lag (Dec 2025 / Jul 2025) ===")
for key in CSV_FILES:
    df = dfs_clean[key]
    jul25  = df[(df[year_col] == 2025) & (df[month_col] == 7)][total_col].sum()
    dec25  = df[(df[year_col] == 2025) & (df[month_col] == 12)][total_col].sum()
    if jul25 > 0:
        ratio = dec25 / jul25
        print(f"  {key}: Jul={int(jul25):,}, Dec={int(dec25):,}, ratio={ratio:.3f}")
        log_result("1.9", f"lag_ratio_dec_jul_{key}", round(ratio, 3), None,
                   note="JQC expects 0.46-0.72 range")
    else:
        print(f"  {key}: Jul=0 (unexpected)")

# ─────────────────────────────────────────────────────────────────────────────
# TASK 1.10 — Temporal coverage: no gaps, no duplicate (cvegeo, year, month)
# ─────────────────────────────────────────────────────────────────────────────
print("\n=== TASK 1.10: Temporal coverage ===")
for key in CSV_FILES:
    df = dfs[key]  # use pre-exclusion for temporal check
    n_months = df[[year_col, month_col]].drop_duplicates().shape[0]
    dups = df.duplicated(subset=["cvegeo", year_col, month_col]).sum()
    print(f"  {key}: {n_months} unique (year,month) combos, {int(dups)} duplicate (cvegeo,year,month) rows")
    log_result("1.10", f"unique_yearmonth_{key}", n_months, 132)
    log_result("1.10", f"duplicates_{key}", int(dups), 0)

# ─────────────────────────────────────────────────────────────────────────────
# TASK 1.11 — Compare raw CSVs against processed panel
# ─────────────────────────────────────────────────────────────────────────────
print("\n=== TASK 1.11: Compare raw vs processed panel ===")
print(f"  Panel columns: {list(panel.columns)}")
print(f"  Panel dtypes (sample):\n{panel.dtypes}")
panel_shape = panel.shape
print(f"  Panel shape: {panel_shape}")

# Expected: 2,478 munis × 132 months × 4 statuses (if status stacked) or wide
# Check how panel is structured
if "status" in panel.columns or "status_id" in panel.columns:
    status_col = "status" if "status" in panel.columns else "status_id"
    print(f"  Panel is long-form with status col '{status_col}'")
    n_rows_expected = 2_478 * 132
    for s in panel[status_col].unique():
        n = panel[panel[status_col] == s].shape[0]
        print(f"    status={s}: {n:,} rows (expected {n_rows_expected:,})")
else:
    print("  Panel appears wide-form")
    print(f"  Unique cvegeo in panel: {panel['cvegeo'].nunique() if 'cvegeo' in panel.columns else 'N/A'}")

# Compare total person-counts: panel vs raw
# Panel total persons (status 0 = total)
if "status_id" in panel.columns:
    panel_total_col = [c for c in panel.columns if "count" in c.lower() or "total" in c.lower()]
    print(f"  Panel count-like columns: {panel_total_col}")

log_result("1.11", "panel_shape_rows", panel_shape[0], None, note="inspect manually")

# ─────────────────────────────────────────────────────────────────────────────
# TASK 1.12 — Sex composition cross-check (Marco pivot vs raw data)
# ─────────────────────────────────────────────────────────────────────────────
print("\n=== TASK 1.12: Sex composition cross-check ===")
print("  Checking sex column structure in each CSV:")
for key in CSV_FILES:
    df = dfs[key]
    sex_like = [c for c in df.columns if any(x in c.lower() for x in
                ["sex", "sexo", "masc", "fem", "male", "female", "hombre", "mujer", "masculin"])]
    print(f"  {key}: {sex_like}")

# For NL CSV: reproduce Marco's pivot (narrow exclusion, by sex)
df_nl_narrow = dfs["nl"][~narrow_mask(dfs["nl"])].copy()
total_col_nl = "total" if "total" in df_nl_narrow.columns else df_nl_narrow.columns[-1]
print(f"\n  NL after narrow exclusion:")
print(f"    Rows: {len(df_nl_narrow):,}, Persons: {int(df_nl_narrow[total_col_nl].sum()):,}")
print(f"    Marco's pivot: total={MARCO_PIVOT['nl']['total']:,}")
log_result("1.12", "nl_persons_narrow_exclusion",
           int(df_nl_narrow[total_col_nl].sum()), MARCO_PIVOT["nl"]["total"],
           note="should match Marco's pivot")

# ─────────────────────────────────────────────────────────────────────────────
# CROSS-PAPER RECONCILIATION
# ─────────────────────────────────────────────────────────────────────────────
print("\n=== CROSS-PAPER RECONCILIATION ===")

# 1. EDA total == JQC total + JQC excluded?
for key in CSV_FILES:
    eda_total  = JQC["persons_incl_sent"][key]
    jqc_clean  = JQC["persons_excl_sent"][key]
    jqc_excl   = JQC["excluded_persons"][key]
    arith_check = jqc_clean + jqc_excl
    match = "OK" if arith_check == eda_total else f"MISMATCH ({arith_check} ≠ {eda_total})"
    print(f"  {key}: JQC_clean + JQC_excl = {arith_check:,}  EDA_total = {eda_total:,}  → {match}")

# 2. Actual data vs both papers
print("\n  Actual data (broad exclusion) vs JQC and EDA:")
for key in CSV_FILES:
    actual_incl = int(dfs[key][total_col].sum()) if "total" in dfs[key].columns else None
    actual_excl = broad_exclusions[key]["kept_persons"]
    jqc_incl  = JQC["persons_incl_sent"][key]
    jqc_excl_n = JQC["persons_excl_sent"][key]
    match_eda = "✅" if actual_incl == jqc_incl else f"❌ ({actual_incl:,} vs {jqc_incl:,})"
    match_jqc = "✅" if actual_excl == jqc_excl_n else f"❌ ({actual_excl:,} vs {jqc_excl_n:,})"
    print(f"  {key}: incl_sentinels={actual_incl:,} vs EDA {jqc_incl:,} {match_eda}")
    print(f"        excl_sentinels={actual_excl:,} vs JQC {jqc_excl_n:,} {match_jqc}")

# ─────────────────────────────────────────────────────────────────────────────
# SAVE OUTPUTS
# ─────────────────────────────────────────────────────────────────────────────
print("\n=== Saving outputs ===")
results_df = pd.DataFrame(results)
results_df.to_csv(OUT_DIR / "WP1_results.csv", index=False)

# Summary table
print("\n  SUMMARY:")
print(results_df[["task", "check", "observed", "expected", "verdict"]].to_string(index=False))

# Exclusion comparison table
excl_summary = []
for key in CSV_FILES:
    excl_summary.append({
        "status":             key,
        "narrow_excl_rows":   narrow_exclusions[key]["excl_rows"],
        "narrow_excl_persons":narrow_exclusions[key]["excl_persons"],
        "narrow_kept_persons":narrow_exclusions[key]["kept_persons"],
        "broad_excl_rows":    broad_exclusions[key]["excl_rows"],
        "broad_excl_persons": broad_exclusions[key]["excl_persons"],
        "broad_kept_persons": broad_exclusions[key]["kept_persons"],
        "jqc_excl_persons":   JQC["excluded_persons"][key],
        "jqc_kept_persons":   JQC["persons_excl_sent"][key],
        "eda_total_persons":  JQC["persons_incl_sent"][key],
    })
excl_df = pd.DataFrame(excl_summary)
excl_df.to_csv(OUT_DIR / "WP1_exclusion_comparison.csv", index=False)
print("\n  Exclusion comparison:")
print(excl_df.to_string(index=False))

# Metadata
meta = {
    "seed": AUDIT_SEED,
    "timestamp": RUN_TIMESTAMP,
    "input_hashes": AUDIT_LOG["hashes"],
    "n_checks": len(results_df),
    "n_pass": int((results_df["verdict"] == "PASS").sum()),
    "n_fail": int((results_df["verdict"] == "FAIL").sum()),
    "n_na":   int((results_df["verdict"] == "N/A").sum()),
}
(OUT_DIR / "WP1_results.json").write_text(json.dumps(meta, indent=2))
print(f"\n  Saved: WP1_results.csv, WP1_exclusion_comparison.csv, WP1_results.json, WP1_audit_log.json")
print(f"\n  TOTALS: {meta['n_pass']} PASS / {meta['n_fail']} FAIL / {meta['n_na']} N/A out of {meta['n_checks']} checks")
print("\n=== WP1 script complete ===")
