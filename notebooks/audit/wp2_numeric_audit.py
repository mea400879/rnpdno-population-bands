"""
WP2 — Numeric Audit of Reported Results
=========================================
Verifies every major number in the JQC manuscript against recomputed values.
Approach:
  - Tasks computable from panel/LISA outputs: re-derive and compare.
  - Computationally expensive spatial stats (Moran's I, LISA permutations):
    verify stored processed outputs against manuscript claims.
Strategy: stored processed files are valid (WP1 confirmed data unchanged).
"""

import hashlib
import json
import warnings
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
import scipy.stats as stats
from statsmodels.stats.sandwich_covariance import cov_hac
from statsmodels.regression.linear_model import OLS
from statsmodels.tools.tools import add_constant

warnings.filterwarnings("ignore")

PROJECT_ROOT = Path("/home/marco/workspace/work/rnpdno-population-bands")
DATA_PROC    = PROJECT_ROOT / "data" / "processed"
DATA_EXT     = PROJECT_ROOT / "data" / "external"
AUDIT_DIR    = PROJECT_ROOT / "audit"
OUT_DIR      = AUDIT_DIR / "outputs"
OUT_DIR.mkdir(parents=True, exist_ok=True)

RUN_TIMESTAMP = datetime.now().isoformat()
AUDIT_SEED    = 42
np.random.seed(AUDIT_SEED)

results: list[dict] = []

STATUS_MAP = {0: "total", 2: "la", 3: "ld", 7: "nl"}
STATUS_NAME = {0: "Total", 2: "Located Alive", 3: "Located Dead", 7: "Not Located"}

# ── helpers ──────────────────────────────────────────────────────────────────
def log(task, check, observed, expected, note=""):
    tol = 0.5  # percentage
    if expected is None:
        verdict = "N/A"
    elif isinstance(expected, float):
        rel = abs(observed - expected) / max(abs(expected), 1e-9)
        verdict = "PASS" if rel <= tol / 100 else ("QUAL" if rel <= 0.05 else "FAIL")
    elif isinstance(expected, (int, np.integer)):
        verdict = "PASS" if int(observed) == int(expected) else "FAIL"
    else:
        verdict = "PASS" if observed == expected else "FAIL"
    marker = {"PASS": "✅", "QUAL": "⚠️", "FAIL": "❌", "N/A": "·"}[verdict]
    print(f"  {marker}  {task} | {check}: obs={observed}  exp={expected}  [{verdict}]  {note}")
    results.append({"task": task, "check": check, "observed": observed,
                    "expected": expected, "verdict": verdict, "note": note})

def gini(x):
    """Gini coefficient of a non-negative array."""
    x = np.sort(np.asarray(x, dtype=float))
    n = len(x)
    if n == 0 or x.sum() == 0:
        return np.nan
    idx = np.arange(1, n + 1)
    return 2 * np.sum(idx * x) / (n * x.sum()) - (n + 1) / n

def ols_hac_slope(y, bw=12):
    """OLS slope with Newey-West HAC SEs. Returns (slope_yr, p_value)."""
    t = np.arange(len(y))
    X = add_constant(t)
    model = OLS(y, X).fit()
    cov = cov_hac(model, nlags=bw)
    se_slope = np.sqrt(cov[1, 1])
    t_stat = model.params[1] / se_slope
    p = 2 * (1 - stats.t.cdf(abs(t_stat), df=model.df_resid))
    # convert monthly slope to yearly
    slope_yr = model.params[1] * 12
    se_yr = se_slope * 12
    t_yr = model.params[1] / se_slope   # t-stat unchanged by scaling
    return slope_yr, p, t_yr

def jaccard(set_a, set_b):
    if len(set_a) == 0 and len(set_b) == 0:
        return 0.0
    return len(set_a & set_b) / len(set_a | set_b)

# ── Load data ─────────────────────────────────────────────────────────────────
print("Loading data…")
panel      = pd.read_parquet(DATA_PROC / "panel_monthly_counts.parquet")
lisa       = pd.read_parquet(DATA_PROC / "lisa_monthly_results.parquet")
conc       = pd.read_csv(DATA_PROC / "concentration_monthly.csv")
morans     = pd.read_csv(DATA_PROC / "morans_i_monthly.csv")
hh_reg     = pd.read_csv(DATA_PROC / "hh_regional_composition.csv")
bajio_ts   = pd.read_csv(DATA_PROC / "bajio_corridor_hh_timeseries.csv")
ced_ts     = pd.read_csv(DATA_PROC / "ced_state_hh_timeseries.csv")
ced_align  = pd.read_csv(DATA_PROC / "ced_temporal_alignment.csv")
muni_class = pd.read_csv(DATA_PROC / "municipality_classification_v2.csv")

print(f"  Panel: {panel.shape}, LISA: {lisa.shape}, Conc: {conc.shape}, Morans: {morans.shape}")

# 29-muni Bajío corridor (used for Chow test and Table 6 Bajío row)
bajio29 = pd.read_csv(DATA_EXT / "bajio_corridor_municipalities.csv")
bajio29["cvegeo"] = bajio29["cvegeo"].astype(str).str.zfill(5)
bajio29_cvs = set(bajio29["cvegeo"])
print(f"  29-muni Bajío corridor: {len(bajio29_cvs)} municipalities")

# Build full 132-month index (sorted)
_all_months = (panel[["year","month"]].drop_duplicates()
               .sort_values(["year","month"]).reset_index(drop=True))

# Pre-compute monthly HH counts for 29-muni corridor (sex=total, all statuses)
lisa_b29 = lisa[lisa["cvegeo"].isin(bajio29_cvs) & (lisa["sex"] == "total")]
bajio29_hh: dict[int, np.ndarray] = {}  # status_id -> 132-element array
for _sid in [0, 7, 2, 3]:
    _hh = (lisa_b29[(lisa_b29["status_id"]==_sid) & (lisa_b29["cluster_label"]=="HH")]
           .groupby(["year","month"]).size().reset_index(name="hh_count"))
    _merged = _all_months.merge(_hh, on=["year","month"], how="left").fillna(0)
    bajio29_hh[_sid] = _merged["hh_count"].values
print(f"  bajio29_hh shapes: {[len(v) for v in bajio29_hh.values()]}")

# ── TASK 2.12 — Abstract and Section 1 counts ─────────────────────────────────
print("\n=== TASK 2.12: Abstract and Section 1 counts ===")
n_munis   = panel["cvegeo"].nunique()
n_months  = panel[["year","month"]].drop_duplicates().shape[0]
n_statuses = panel["status_id"].nunique()   # 4
n_sexes    = 3                              # total, male, female
lisa_runs  = n_statuses * n_sexes * n_months
persons_total = int(panel[panel["status_id"]==0]["total"].sum())

log("2.12", "n_municipalities_panel",  n_munis,  2_478)
log("2.12", "n_months",               n_months,  132)
log("2.12", "lisa_runs",              lisa_runs, 1_584,  note="4 status × 3 sex × 132 months")
log("2.12", "persons_total_JQC",  persons_total, 263_402, note="after broad exclusion")

# ── TASK 2.1 — Concentration / Gini ──────────────────────────────────────────
print("\n=== TASK 2.1: Gini concentration ===")

# Verify stored concentration_monthly.csv structure
log("2.1", "conc_rows", len(conc), 528, note="4 statuses × 132 months")

# Re-derive Gini from panel independently
panel_clean = panel.copy()
gini_records = []
for (sid, yr, mo), grp in panel_clean.groupby(["status_id","year","month"]):
    g = gini(grp["total"].values)
    gini_records.append({"status_id": sid, "year": yr, "month": mo, "gini_computed": g})
gini_df = pd.DataFrame(gini_records)

# Compare to stored
merged = gini_df.merge(conc[["status_id","year","month","gini"]],
                       on=["status_id","year","month"])
max_diff = (merged["gini_computed"] - merged["gini"]).abs().max()
mean_diff = (merged["gini_computed"] - merged["gini"]).abs().mean()
log("2.1", "gini_recompute_max_diff", round(max_diff, 6), None,
    note=f"max abs diff vs stored (mean={mean_diff:.6f})")

# Verify manuscript summary statistics from stored
for sid in [0, 7, 2, 3]:
    sub = conc[conc["status_id"]==sid]["gini"]
    exp = {0: (0.935, 0.915, 0.958), 7: (0.946, 0.926, 0.966),
           2: (0.955, 0.935, 0.978), 3: (0.979, 0.963, 0.993)}[sid]
    log(f"2.1", f"gini_mean_{STATUS_MAP[sid]}",  round(sub.mean(), 3), exp[0])
    log(f"2.1", f"gini_min_{STATUS_MAP[sid]}",   round(sub.min(),  3), exp[1])
    log(f"2.1", f"gini_max_{STATUS_MAP[sid]}",   round(sub.max(),  3), exp[2])

# Verify Gini trend slopes (Newey-West, bw=12)
for sid in [0, 7, 2, 3]:
    sub = conc[conc["status_id"]==sid].sort_values(["year","month"])["gini"].values
    slope_yr, p, _ = ols_hac_slope(sub)
    exp_slope = {0: -0.004, 7: -0.003, 2: -0.004, 3: -0.002}[sid]
    log("2.1", f"gini_trend_{STATUS_MAP[sid]}", round(slope_yr, 3), exp_slope)

# June 2025 concentration counts (50% cutoff)
print("\n  June 2025 concentration counts:")
panel_jun25 = panel[(panel["year"]==2025) & (panel["month"]==6)]
for sid, label, exp_muni, exp_desc in [
        (7, "NL",    42, "50% of NL in 42 muni (1.7%)"),
        (3, "LD",    22, "50% of LD in 22 (0.9%)"),
        (0, "Total", 48, "50% of Total in 48 (1.9%)")]:
    sub = panel_jun25[panel_jun25["status_id"]==sid][["cvegeo","total"]].sort_values("total", ascending=False)
    total_persons = sub["total"].sum()
    cumsum = sub["total"].cumsum()
    n_muni_50 = int((cumsum <= total_persons * 0.5).sum() + 1)
    log("2.1", f"jun25_50pct_munis_{label}", n_muni_50, exp_muni, note=exp_desc)

# ── TASK 2.2 — Global Moran's I ──────────────────────────────────────────────
print("\n=== TASK 2.2: Global Moran's I ===")
log("2.2", "morans_rows", len(morans), 528, note="4 statuses × 132 months")

# Significance counts
for sid in [0, 7, 2, 3]:
    sub = morans[morans["status_id"]==sid]
    n_sig = int((sub["p_value"] <= 0.05).sum())
    exp = {0: 132, 7: 132, 2: 127, 3: 122}[sid]
    log("2.2", f"n_significant_{STATUS_MAP[sid]}", n_sig, exp)

# Mean and range
for sid, label in [(0,"total"),(7,"nl"),(2,"la"),(3,"ld")]:
    sub = morans[morans["status_id"]==sid]["morans_i"]
    exp = {0: (0.199, 0.038, 0.374), 7: (0.163, 0.043, 0.280),
           2: (0.187, 0.011, 0.401), 3: (0.101, -0.006, 0.298)}[sid]
    log("2.2", f"moran_mean_{label}",  round(sub.mean(), 3), exp[0])
    log("2.2", f"moran_min_{label}",   round(sub.min(),  3), exp[1])
    log("2.2", f"moran_max_{label}",   round(sub.max(),  3), exp[2])

# Trend slopes on Moran's I series
for sid, label in [(0,"total"),(7,"nl"),(2,"la"),(3,"ld")]:
    sub = morans[morans["status_id"]==sid].sort_values(["year","month"])["morans_i"].values
    slope_yr, p, _ = ols_hac_slope(sub)
    exp_slope = {0: 0.019, 7: 0.007, 2: 0.020, 3: 0.005}[sid]
    log("2.2", f"moran_trend_{label}", round(slope_yr, 3), exp_slope)

# LD trend non-significance
sub_ld = morans[morans["status_id"]==3].sort_values(["year","month"])["morans_i"].values
_, p_ld, _ = ols_hac_slope(sub_ld)
log("2.2", "moran_trend_ld_pvalue", round(p_ld, 3), None, note="manuscript says p=0.224")

# ── TASK 2.3 — LISA classification Table 3 (June 2025, sex=total) ────────────
print("\n=== TASK 2.3: LISA classification Table 3 (June 2025, sex=total) ===")

lisa_jun25_total = lisa[(lisa["year"]==2025) & (lisa["month"]==6) & (lisa["sex"]=="total")]

expected_t3 = {
    0: {"HH": 106, "LL": 50, "HL": 1,  "LH": 62, "NS": 2259},
    7: {"HH": 93,  "LL": 2,  "HL": 2,  "LH": 52, "NS": 2329},
    2: {"HH": 110, "LL": 5,  "HL": 35, "LH": 69, "NS": 2259},
    3: {"HH": 35,  "LL": 7,  "HL": 38, "LH": 105,"NS": 2293},
}

lisa_t3_counts: dict[int, dict] = {}
for sid in [0, 7, 2, 3]:
    sub = lisa_jun25_total[lisa_jun25_total["status_id"]==sid]
    counts = sub["cluster_label"].value_counts().to_dict()
    lisa_t3_counts[sid] = counts
    for lbl in ["HH", "LL", "HL", "LH", "NS"]:
        obs = counts.get(lbl, 0)
        exp = expected_t3[sid][lbl]
        log("2.3", f"{STATUS_MAP[sid]}_{lbl}_jun25", obs, exp)

# ── TASK 2.4 — Jaccard pairwise Table 4 (June 2025) ──────────────────────────
print("\n=== TASK 2.4: Jaccard pairwise Table 4 (June 2025) ===")

hh_sets = {}
for sid in [0, 7, 2, 3]:
    sub = lisa_jun25_total[lisa_jun25_total["status_id"]==sid]
    hh_sets[sid] = set(sub[sub["cluster_label"]=="HH"]["cvegeo"].values)

# Diagonal (HH counts)
expected_diag = {0: 106, 7: 93, 2: 110, 3: 35}
for sid in [0, 7, 2, 3]:
    log("2.4", f"HH_diag_{STATUS_MAP[sid]}", len(hh_sets[sid]), expected_diag[sid])

# Intersection counts
pairs = [(0,7,"total-nl",71), (0,2,"total-la",87), (0,3,"total-ld",24),
         (7,2,"nl-la",56),    (7,3,"nl-ld",16),    (2,3,"la-ld",19)]
for sid_a, sid_b, label, exp_inter in pairs:
    inter = len(hh_sets[sid_a] & hh_sets[sid_b])
    log("2.4", f"intersection_{label}", inter, exp_inter)

# Jaccard coefficients
jaccard_expected = {
    "nl-ld": 0.143, "la-ld": 0.151,
    "total-la": 0.674, "nl-la": 0.381,
}
for sid_a, sid_b, label, _ in pairs:
    j = round(jaccard(hh_sets[sid_a], hh_sets[sid_b]), 3)
    exp_j = jaccard_expected.get(label)
    log("2.4", f"jaccard_{label}", j, exp_j)

# June 2015 and June 2020 Jaccard
for yr, mo, exp_nl_ld, exp_la_ld in [(2015, 6, 0.103, 0.000), (2020, 6, 0.164, 0.198)]:
    sub = lisa[(lisa["year"]==yr) & (lisa["month"]==mo) & (lisa["sex"]=="total")]
    hh_7 = set(sub[(sub["status_id"]==7) & (sub["cluster_label"]=="HH")]["cvegeo"])
    hh_2 = set(sub[(sub["status_id"]==2) & (sub["cluster_label"]=="HH")]["cvegeo"])
    hh_3 = set(sub[(sub["status_id"]==3) & (sub["cluster_label"]=="HH")]["cvegeo"])
    j_nl_ld = round(jaccard(hh_7, hh_3), 3)
    j_la_ld = round(jaccard(hh_2, hh_3), 3)
    log("2.4", f"jaccard_nl_ld_jun{yr}", j_nl_ld, exp_nl_ld)
    log("2.4", f"jaccard_la_ld_jun{yr}", j_la_ld, exp_la_ld)

# ── TASK 2.5 — Mann-Whitney U on HH populations ───────────────────────────────
print("\n=== TASK 2.5: Mann-Whitney U on HH populations (June 2025) ===")

pop_2025 = (pd.read_parquet(DATA_EXT / "conapo_poblacion_1990_2070.parquet")
            .query("year == 2025")
            .rename(columns={"cve_geo": "cvegeo", "pob_total": "poblacion"})
            [["cvegeo","year","poblacion"]])
pop_2025["cvegeo"] = pop_2025["cvegeo"].astype(str).str.zfill(5)

# Build HH sets with populations
hh_pops = {}
for sid in [0, 7, 2, 3]:
    hh_cvs = list(hh_sets[sid])
    pops = pop_2025[pop_2025["cvegeo"].isin(hh_cvs)]["poblacion"].values
    hh_pops[sid] = pops

# Pairwise Mann-Whitney tests
mw_pairs = [(0,7,"total-nl"), (0,2,"total-la"), (0,3,"total-ld"),
            (7,2,"nl-la"),   (7,3,"nl-ld"),    (2,3,"la-ld")]
all_p_above_05 = True
for sid_a, sid_b, label in mw_pairs:
    if len(hh_pops[sid_a]) > 0 and len(hh_pops[sid_b]) > 0:
        stat, p = stats.mannwhitneyu(hh_pops[sid_a], hh_pops[sid_b],
                                     alternative="two-sided")
        above = p > 0.50
        print(f"  {label}: U={stat:.0f}, p={p:.4f}  {'✅ p>0.50' if above else '❌ p≤0.50'}")
        if not above:
            all_p_above_05 = False
log("2.5", "all_pairwise_mw_p_gt_0.50", all_p_above_05, True,
    note="manuscript: all pairwise p > 0.50")

# KS test as manuscript also runs it
for sid_a, sid_b, label in mw_pairs:
    if len(hh_pops[sid_a]) > 0 and len(hh_pops[sid_b]) > 0:
        ks_stat, ks_p = stats.ks_2samp(hh_pops[sid_a], hh_pops[sid_b])
        print(f"  KS {label}: D={ks_stat:.4f}, p={ks_p:.4f}")

# ── TASK 2.6 — Regional trends Table 5 ───────────────────────────────────────
print("\n=== TASK 2.6: Regional trends Table 5 (Newey-West HAC, bw=12) ===")

# Build 6-region timeseries:
# Bajío = is_bajio=True (any region); others = geographic region totals
hh_reg_grouped = hh_reg[hh_reg["grouping_type"] == "region"].copy()

def build_region_ts(status_id):
    """Return monthly HH counts for 6 regions. Bajío uses 29-muni corridor from LISA."""
    sub = hh_reg_grouped[hh_reg_grouped["status_id"] == status_id]
    ts = {}
    # Bajío corridor: 29-muni definition (correct for Chow / Table 6)
    bajio_df = pd.DataFrame({
        "year": _all_months["year"].values,
        "month": _all_months["month"].values,
        "n_hh_munis": bajio29_hh[status_id],
    })
    ts["Bajio"] = bajio_df.set_index(["year","month"])["n_hh_munis"]
    # Geographic regions (full, Bajío included)
    for reg in ["Centro","Centro-Norte","Norte","Norte-Occidente","Sur"]:
        reg_sub = sub[sub["region"]==reg].groupby(["year","month"])["n_hh_munis"].sum().reset_index()
        ts[reg] = reg_sub.set_index(["year","month"])["n_hh_munis"]
    return ts

# Expected Table 5 values (slope/yr, significance) — load-bearing cells
# Format: (expected_slope_yr, significance_stars)
TABLE5_EXPECTED = {
    ("Centro", 7):   (4.96, "***"),
    ("Bajio",  7):   (0.50, "***"),
}

# Full expected table for all 24 cells
# Using manuscript Table 5 values — fill in as known
# Stars: *** p<0.001, ** p<0.01, * p<0.05
TABLE5_SLOPES_ALL = {
    # (region, status_id): slope_yr
    ("Centro",          0): None,   # fill from manuscript
    ("Centro",          7): 4.96,
    ("Centro",          2): None,
    ("Centro",          3): None,
    ("Bajio",           0): None,
    ("Bajio",           7): 0.50,
    ("Bajio",           2): None,
    ("Bajio",           3): None,
    ("Centro-Norte",    0): None,
    ("Centro-Norte",    7): None,
    ("Centro-Norte",    2): None,
    ("Centro-Norte",    3): None,
    ("Norte",           0): None,
    ("Norte",           7): None,
    ("Norte",           2): None,
    ("Norte",           3): None,
    ("Norte-Occidente", 0): None,
    ("Norte-Occidente", 7): None,
    ("Norte-Occidente", 2): None,
    ("Norte-Occidente", 3): None,
    ("Sur",             0): None,
    ("Sur",             7): None,
    ("Sur",             2): None,
    ("Sur",             3): None,
}

t5_rows = []
for sid in [0, 7, 2, 3]:
    ts_dict = build_region_ts(sid)
    for reg_key, ts in ts_dict.items():
        ts_sorted = ts.reset_index().sort_values(["year","month"])["n_hh_munis"].values
        slope_yr, p, t_stat = ols_hac_slope(ts_sorted)
        stars = "***" if p < 0.001 else ("**" if p < 0.01 else ("*" if p < 0.05 else "ns"))
        exp_slope = TABLE5_SLOPES_ALL.get((reg_key, sid))
        t5_rows.append({
            "region": reg_key, "status_id": sid, "status": STATUS_MAP[sid],
            "slope_yr": round(slope_yr, 3), "p_value": round(p, 4),
            "stars": stars, "expected_slope": exp_slope,
        })
        if exp_slope is not None:
            log("2.6", f"slope_{reg_key}_{STATUS_MAP[sid]}", round(slope_yr, 3), exp_slope)

t5_df = pd.DataFrame(t5_rows)
print("\n  Full Table 5 re-estimation:")
print(t5_df[["region","status","slope_yr","stars","expected_slope"]].to_string(index=False))
t5_df.to_csv(OUT_DIR / "WP2_table5_regional_trends.csv", index=False)

# ── TASK 2.7 — Bajío structural break ────────────────────────────────────────
print("\n=== TASK 2.7: Bajío structural break (Chow test, Feb 2017) ===")

# Total HH count in 29-muni Bajío corridor (correct source for Chow test)
y = bajio29_hh[0]
t = np.arange(len(y))

# Feb 2017 = month_idx 25  (Jan2015=0, ..., Dec2015=11, Jan2016=12, ..., Feb2017=25)
break_idx = 25

# Chow test: compare RSS_restricted vs RSS_pre + RSS_post
def ols_rss(y_seg, t_seg):
    X = add_constant(t_seg.astype(float))
    model = OLS(y_seg, X).fit()
    return model.ssr, model

X_full = add_constant(t.astype(float))
model_full = OLS(y, X_full).fit()
rss_full = model_full.ssr

y_pre  = y[:break_idx+1]
t_pre  = t[:break_idx+1]
y_post = y[break_idx+1:]
t_post = t[break_idx+1:]

rss_pre,  m_pre  = ols_rss(y_pre,  t_pre)
rss_post, m_post = ols_rss(y_post, t_post)
rss_restricted = rss_pre + rss_post

k = 2  # number of parameters (intercept + slope)
n = len(y)
chow_F = ((rss_full - rss_restricted) / k) / (rss_restricted / (n - 2 * k))
chow_p = 1 - stats.f.cdf(chow_F, k, n - 2 * k)
print(f"  Chow F = {chow_F:.2f}, p = {chow_p:.4f}")
log("2.7", "chow_F", round(chow_F, 2), 78.13)
log("2.7", "chow_p_lt_001", chow_p < 0.001, True)

# Piecewise slopes (convert to per-year)
slope_pre_yr  = m_pre.params[1]  * 12
slope_post_yr = m_post.params[1] * 12
print(f"  Pre-break slope:  {slope_pre_yr:.2f}/yr (expected -8.82/yr)")
print(f"  Post-break slope: {slope_post_yr:.2f}/yr (expected +0.47/yr)")
log("2.7", "slope_pre_break_yr",  round(slope_pre_yr, 2),  -8.82)
log("2.7", "slope_post_break_yr", round(slope_post_yr, 2),  0.47)

# Full-period sub-component slopes for 29-muni corridor (Table 6 Bajío row).
# Manuscript text "driven primarily by Not Located (+0.50/year, p<0.001)" cites
# the NL full-period slope from Table 6, not a separate post-break computation.
# NOTE: Table 6 caption states HAC SEs; Bajío row significance matches plain OLS SEs.
#       Discrepancy documented as F_BajioSE in audit report.
print("  Full-period sub-component slopes (Table 6 Bajío row):")
t6_bajio_expected = {7: (0.50, "***"), 3: (0.15, "*"), 2: (-0.35, "**"), 0: (-0.31, "*")}
for sid, (exp_slope, exp_stars) in t6_bajio_expected.items():
    y_full = bajio29_hh[sid]
    t_full = np.arange(len(y_full))
    X_full2 = add_constant(t_full.astype(float))
    m = OLS(y_full, X_full2).fit()
    cov = cov_hac(m, nlags=12)
    se_hac = np.sqrt(cov[1, 1])
    t_hac = m.params[1] / se_hac
    p_hac = 2 * (1 - stats.t.cdf(abs(t_hac), df=m.df_resid))
    p_ols = m.pvalues[1]
    stars_hac = "***" if p_hac < 0.001 else ("**" if p_hac < 0.01 else ("*" if p_hac < 0.05 else "ns"))
    stars_ols = "***" if p_ols < 0.001 else ("**" if p_ols < 0.01 else ("*" if p_ols < 0.05 else "ns"))
    slope_yr = m.params[1] * 12
    match_note = f"HAC:{stars_hac} OLS:{stars_ols} manuscript:{exp_stars}"
    print(f"    {STATUS_MAP[sid]}: slope={slope_yr:.3f}/yr (exp={exp_slope})  {match_note}")
    log("2.7", f"t6_bajio_slope_{STATUS_MAP[sid]}", round(slope_yr, 3), exp_slope,
        note=match_note)

# ── TASK 2.8 — Chi-square bookend tests Figure 7 ─────────────────────────────
print("\n=== TASK 2.8: Chi-square bookend tests (June 2015 vs June 2025) ===")

# Build regional HH counts per status for June 2015 and June 2025
# Use full geographic regions (including Bajío portions)
expected_chi2 = {
    0: (9.5,  0.050),
    7: (16.5, 0.002),
    2: (17.7, 0.001),
    3: (14.1, 0.007),
}

REGIONS_ORDER = ["Centro", "Centro-Norte", "Norte", "Norte-Occidente", "Sur"]

for sid in [0, 7, 2, 3]:
    sub = hh_reg_grouped[hh_reg_grouped["status_id"]==sid]
    counts_15 = []
    counts_25 = []
    for reg in REGIONS_ORDER:
        c15 = sub[(sub["year"]==2015) & (sub["month"]==6) & (sub["region"]==reg)]["n_hh_munis"].sum()
        c25 = sub[(sub["year"]==2025) & (sub["month"]==6) & (sub["region"]==reg)]["n_hh_munis"].sum()
        counts_15.append(c15)
        counts_25.append(c25)

    # Chi-square test of independence (2 periods × 5 regions)
    contingency = np.array([counts_15, counts_25])
    chi2, p, dof, _ = stats.chi2_contingency(contingency)
    exp_chi2, exp_p = expected_chi2[sid]
    print(f"  {STATUS_MAP[sid]}: χ²={chi2:.1f} (exp={exp_chi2}), p={p:.3f} (exp={exp_p}), dof={dof}")
    print(f"    Jun 2015: {counts_15}")
    print(f"    Jun 2025: {counts_25}")
    log("2.8", f"chi2_{STATUS_MAP[sid]}", round(chi2, 1), exp_chi2)
    log("2.8", f"chi2_p_{STATUS_MAP[sid]}", round(p, 3), exp_p)

# ── TASK 2.9 — Sex disaggregation Table 6 (June 2025) ────────────────────────
print("\n=== TASK 2.9: Sex disaggregation Table 6 (June 2025) ===")

expected_t6 = {
    0: {"male": 121, "female": 99,  "shared": 74, "jaccard": 0.507},
    7: {"male": 85,  "female": 50,  "shared": 28, "jaccard": 0.262},
    2: {"male": 83,  "female": 90,  "shared": 58, "jaccard": 0.504},
    3: {"male": 27,  "female": 0,   "shared": 0,  "jaccard": 0.000},
}

lisa_jun25 = lisa[(lisa["year"]==2025) & (lisa["month"]==6)]
for sid in [0, 7, 2, 3]:
    sub = lisa_jun25[lisa_jun25["status_id"]==sid]
    hh_m = set(sub[(sub["sex"]=="male")   & (sub["cluster_label"]=="HH")]["cvegeo"])
    hh_f = set(sub[(sub["sex"]=="female") & (sub["cluster_label"]=="HH")]["cvegeo"])
    shared = hh_m & hh_f
    j = round(jaccard(hh_m, hh_f), 3)
    e = expected_t6[sid]
    log("2.9", f"HH_male_{STATUS_MAP[sid]}",   len(hh_m),  e["male"])
    log("2.9", f"HH_female_{STATUS_MAP[sid]}", len(hh_f),  e["female"])
    log("2.9", f"shared_{STATUS_MAP[sid]}",    len(shared),e["shared"])
    log("2.9", f"jaccard_sex_{STATUS_MAP[sid]}",j,         e["jaccard"])

# "If female set matched male size, 28 shared = 33%" counterfactual (NL)
# 28 shared out of hypothetical 85 female = 28/85 = 33%
nl_shared = len(set(lisa_jun25[(lisa_jun25["status_id"]==7) & (lisa_jun25["sex"]=="male")   & (lisa_jun25["cluster_label"]=="HH")]["cvegeo"]) &
               set(lisa_jun25[(lisa_jun25["status_id"]==7) & (lisa_jun25["sex"]=="female") & (lisa_jun25["cluster_label"]=="HH")]["cvegeo"]))
counterfactual = round(nl_shared / 85, 2)  # 28/85 = 0.33
log("2.9", "nl_counterfactual_28_of_85", counterfactual, 0.33,
    note="if female set = 85, shared fraction = 28/85 = 33%")

# ── TASK 2.10 — CED state trajectories ───────────────────────────────────────
print("\n=== TASK 2.10: CED state trajectories ===")

# Map state codes to names
state_map = {14: "Jalisco", 11: "Guanajuato", 5: "Coahuila", 30: "Veracruz",
             18: "Nayarit",  27: "Tabasco",    19: "Nuevo León", 15: "Estado de México"}

# Compute slopes from ced_state_hh_timeseries per state × status
ced_slopes = {}
for cve_e, state_name in state_map.items():
    for sid in [0, 7, 2, 3]:
        sub = (ced_ts[(ced_ts["cve_estado"]==cve_e) & (ced_ts["status_id"]==sid)]
               .sort_values(["year","month"]).reset_index(drop=True))
        if len(sub) < 10:
            continue
        # Fill missing months with 0
        all_months = pd.DataFrame({"month_idx": range(132)})
        sub["month_idx"] = (sub["year"] - 2015) * 12 + (sub["month"] - 1)
        merged_s = all_months.merge(sub[["month_idx","n_hh_munis"]], on="month_idx", how="left").fillna(0)
        y_s = merged_s["n_hh_munis"].values
        slope_yr, p, _ = ols_hac_slope(y_s)
        ced_slopes[(state_name, STATUS_MAP[sid])] = (round(slope_yr, 3), round(p, 4))

# Verify quoted slopes
expected_ced = {
    ("Estado de México", "nl"): (2.36, 0.001),
    ("Estado de México", "la"): (1.81, 0.001),
    ("Nuevo León",       "la"): (1.34, 0.001),
    ("Nuevo León",       "ld"): (0.80, 0.001),
    ("Guanajuato",       "nl"): (0.75, 0.001),
    ("Guanajuato",       "la"): (-0.57, 0.001),
}
for (state, st), (exp_slope, exp_p_thresh) in expected_ced.items():
    if (state, st) in ced_slopes:
        obs_slope, obs_p = ced_slopes[(state, st)]
        log("2.10", f"ced_slope_{state}_{st}", obs_slope, exp_slope,
            note=f"p={obs_p} (expected p<{exp_p_thresh})")
    else:
        print(f"  WARNING: no data for ({state}, {st})")

# Jalisco registration collapse
print("\n  Jalisco Total registrations by year (from panel):")
# Manuscript cites Total (status_id=0): 3,825 (2021) → 216 (2024) persons; 103 → 41 municipalities
panel_jalisco = panel[(panel["status_id"]==0) & (panel["cvegeo"].str.startswith("14"))]
for yr in [2021, 2024]:
    reg_total = int(panel_jalisco[panel_jalisco["year"]==yr]["total"].sum())
    n_munis_active = int((panel_jalisco[panel_jalisco["year"]==yr]
                          .groupby("cvegeo")["total"].sum() > 0).sum())
    print(f"  Jalisco {yr}: NL registrations={reg_total:,}, active munis={n_munis_active}")
log("2.10", "jalisco_total_registrations_2021",
    int(panel_jalisco[panel_jalisco["year"]==2021]["total"].sum()), 3_825)
log("2.10", "jalisco_total_registrations_2024",
    int(panel_jalisco[panel_jalisco["year"]==2024]["total"].sum()), 216)
log("2.10", "jalisco_total_active_munis_2021",
    int((panel_jalisco[panel_jalisco["year"]==2021].groupby("cvegeo")["total"].sum() > 0).sum()), 103)
log("2.10", "jalisco_total_active_munis_2024",
    int((panel_jalisco[panel_jalisco["year"]==2024].groupby("cvegeo")["total"].sum() > 0).sum()), 41)

# ── TASK 2.11 — Temporal stability Appendix A.1 ───────────────────────────────
print("\n=== TASK 2.11: Temporal stability (Spearman local_i, Jun 2024 vs Jun 2025) ===")

lisa_jun24 = lisa[(lisa["year"]==2024) & (lisa["month"]==6)]
lisa_jun25_ = lisa[(lisa["year"]==2025) & (lisa["month"]==6)]

spearman_rows = []
for sid in [0, 7, 2, 3]:
    for sx in ["total", "male", "female"]:
        a = lisa_jun24[(lisa_jun24["status_id"]==sid) & (lisa_jun24["sex"]==sx)][["cvegeo","local_i"]]
        b = lisa_jun25_[(lisa_jun25_["status_id"]==sid) & (lisa_jun25_["sex"]==sx)][["cvegeo","local_i"]]
        m = a.merge(b, on="cvegeo", suffixes=("_24","_25"))
        rho, p = stats.spearmanr(m["local_i_24"], m["local_i_25"])
        spearman_rows.append({"status": STATUS_MAP[sid], "sex": sx,
                               "rho": round(rho, 3), "p": round(p, 4)})
        print(f"  {STATUS_MAP[sid]}/{sx}: ρ={rho:.3f}, p={p:.4f}")

sp_df = pd.DataFrame(spearman_rows)
sp_df.to_csv(OUT_DIR / "WP2_appendix_A1_spearman.csv", index=False)
# Verify range 0.227–0.607
rho_min = sp_df["rho"].min()
rho_max = sp_df["rho"].max()
log("2.11", "spearman_range_min", round(rho_min, 3), None, note="manuscript: 0.227 to 0.607")
log("2.11", "spearman_range_max", round(rho_max, 3), None, note="manuscript: 0.227 to 0.607")
log("2.11", "spearman_all_positive", bool((sp_df["rho"] > 0).all()), True)

# ── TASK 2.13 — VAWRI external validation ─────────────────────────────────────
print("\n=== TASK 2.13: VAWRI external validation (June 2023, sex=total) ===")

vawri = pd.read_csv(DATA_EXT / "vawri" / "vawri_mexico_2023_data.csv")
# Build cvegeo (5-digit) from CVE_INEGI (which is already 4-digit: ENTMUN, e.g. 1001 → 01001)
vawri["cvegeo"] = vawri["CVE_INEGI"].astype(str).str.zfill(5)

# June 2023 HH municipalities (total sex)
lisa_jun23_total = lisa[(lisa["year"]==2023) & (lisa["month"]==6) & (lisa["sex"]=="total")]
hh_jun23 = {}
for sid in [0, 7, 2, 3]:
    sub = lisa_jun23_total[lisa_jun23_total["status_id"]==sid]
    hh_jun23[sid] = set(sub[sub["cluster_label"]=="HH"]["cvegeo"])

# Merge VAWRI with HH status
vawri_merged = vawri[["cvegeo","VAWRI"]].copy()

# Run Mann-Whitney HH vs non-HH for each status
print("  Mann-Whitney VAWRI: HH vs non-HH (June 2023, total sex)")
rb_vals = []
for sid in [0, 7, 2, 3]:
    hh_cv = hh_jun23[sid]
    all_cv = set(vawri_merged["cvegeo"].values)
    non_hh_cv = all_cv - hh_cv
    vawri_hh     = vawri_merged[vawri_merged["cvegeo"].isin(hh_cv)]["VAWRI"].dropna().values
    vawri_non_hh = vawri_merged[vawri_merged["cvegeo"].isin(non_hh_cv)]["VAWRI"].dropna().values
    if len(vawri_hh) > 0 and len(vawri_non_hh) > 0:
        u_stat, p = stats.mannwhitneyu(vawri_hh, vawri_non_hh, alternative="greater")
        # rank-biserial effect size = 2U/(n1*n2) - 1
        rb = 2 * u_stat / (len(vawri_hh) * len(vawri_non_hh)) - 1
        rb_vals.append(rb)
        print(f"  {STATUS_MAP[sid]}: n_HH={len(vawri_hh)}, n_nonHH={len(vawri_non_hh)}, "
              f"U={u_stat:.0f}, p={p:.4e}, rank-biserial={rb:.3f}")
    else:
        print(f"  {STATUS_MAP[sid]}: insufficient data")

if rb_vals:
    log("2.13", "vawri_rb_min", round(min(rb_vals), 2), None, note="manuscript: 0.76–0.96")
    log("2.13", "vawri_rb_max", round(max(rb_vals), 2), None, note="manuscript: 0.76–0.96")
    log("2.13", "vawri_rb_all_in_range",
        bool(all(0.70 <= r <= 1.0 for r in rb_vals)), True,
        note="all should be ≥0.70 (manuscript says 0.76–0.96)")

# ── SAVE RESULTS ──────────────────────────────────────────────────────────────
print("\n=== Saving outputs ===")
results_df = pd.DataFrame(results)
results_df.to_csv(OUT_DIR / "WP2_results.csv", index=False)

meta = {
    "seed": AUDIT_SEED, "timestamp": RUN_TIMESTAMP,
    "n_checks": len(results_df),
    "n_pass":  int((results_df["verdict"]=="PASS").sum()),
    "n_qual":  int((results_df["verdict"]=="QUAL").sum()),
    "n_fail":  int((results_df["verdict"]=="FAIL").sum()),
    "n_na":    int((results_df["verdict"]=="N/A").sum()),
}
(OUT_DIR / "WP2_results.json").write_text(json.dumps(meta, indent=2))

print(f"\n  SUMMARY: {meta['n_pass']} PASS / {meta['n_qual']} QUAL / "
      f"{meta['n_fail']} FAIL / {meta['n_na']} N/A  out of {meta['n_checks']} checks")

# Print all non-PASS items
non_pass = results_df[results_df["verdict"].isin(["FAIL","QUAL"])]
if len(non_pass) > 0:
    print("\n  NON-PASS items:")
    print(non_pass[["task","check","observed","expected","verdict","note"]].to_string(index=False))

print("\n=== WP2 script complete ===")
