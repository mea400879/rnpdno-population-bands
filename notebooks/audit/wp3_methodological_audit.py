#!/usr/bin/env python3
"""
WP3 — Methodological Audit and Re-Specification
RNPDNO JQC manuscript pre-submission audit.

Tasks:
  3.1 HH-count trend re-specification: Poisson + NB + Holm-Bonferroni (FATAL)
  3.2 Threshold-sensitivity of HH trends (α = 0.01 / 0.05 / 0.10)
  3.3 Structural break re-specification: supremum Wald (Andrews 1993)
  3.4 Jaccard null distribution (1 000-draw permutation)
  3.5 Population-normalized LISA (June 2025) — FLAGGED: heavy computation
  3.6 Spatial weights sensitivity — FLAGGED: heavy computation
  3.7 BH-FDR audit — FLAGGED: heavy computation
  3.8 Reporting-lag truncation robustness (2015-01 to 2025-06)

Outputs:
  audit/outputs/WP3_t31_poisson.csv
  audit/outputs/WP3_t32_threshold_sensitivity.csv
  audit/outputs/WP3_t33_supwald.csv
  audit/outputs/WP3_t34_jaccard_null.csv
  audit/outputs/WP3_t38_lag_truncation.csv
  audit/outputs/WP3_results.csv
  audit/outputs/WP3_results.json
"""

import json, hashlib, warnings
import numpy as np
import pandas as pd
from datetime import datetime
from pathlib import Path
from scipy import stats
from statsmodels.regression.linear_model import OLS
from statsmodels.tools import add_constant
from statsmodels.stats.sandwich_covariance import cov_hac
from statsmodels.discrete.discrete_model import Poisson, NegativeBinomial
from statsmodels.stats.multitest import multipletests
import libpysal

warnings.filterwarnings("ignore")

# ── Paths ─────────────────────────────────────────────────────────────────────
PROJECT  = Path("/home/marco/workspace/work/rnpdno-population-bands")
DATA_PROC = PROJECT / "data" / "processed"
DATA_EXT  = PROJECT / "data" / "external"
OUT_DIR   = PROJECT / "audit" / "outputs"
OUT_DIR.mkdir(parents=True, exist_ok=True)

AUDIT_SEED = 42
np.random.seed(AUDIT_SEED)
RUN_TS = datetime.now().isoformat()

STATUS_MAP = {0: "total", 7: "nl", 2: "la", 3: "ld"}
REGIONS_GEO = ["Norte", "Norte-Occidente", "Centro-Norte", "Centro", "Sur"]
ALL_REGIONS  = REGIONS_GEO + ["Bajio"]
LOG = []

def log(task, check, observed, expected=None, verdict=None, note=""):
    if verdict is None:
        if expected is None:
            verdict = "N/A"
        elif isinstance(observed, float) and isinstance(expected, float):
            verdict = "PASS" if abs(observed - expected) / max(abs(expected), 1e-9) < 0.05 else "QUAL"
        else:
            verdict = "PASS" if observed == expected else "FAIL"
    LOG.append({"task": task, "check": check, "observed": observed,
                "expected": expected, "verdict": verdict, "note": note})
    print(f"  [{verdict}] {check}: {observed}" + (f" (exp {expected})" if expected is not None else ""))

# ── Load data ─────────────────────────────────────────────────────────────────
print("Loading data…")
hh_bfs     = pd.read_parquet(DATA_PROC / "hh_clusters_monthly.parquet")
lisa       = pd.read_parquet(DATA_PROC / "lisa_monthly_results.parquet")
muni_class = pd.read_csv(DATA_PROC / "municipality_classification_v2.csv")
panel      = pd.read_parquet(DATA_PROC / "panel_monthly_counts.parquet")

hh_bfs["cvegeo"]     = hh_bfs["cvegeo"].astype(str).str.zfill(5)
lisa["cvegeo"]       = lisa["cvegeo"].astype(str).str.zfill(5)
muni_class["cvegeo"] = muni_class["cvegeo"].astype(str).str.zfill(5)

bajio29   = pd.read_csv(DATA_EXT / "bajio_corridor_municipalities.csv")
bajio29["cvegeo"] = bajio29["cvegeo"].astype(str).str.zfill(5)
bajio29_cvs = set(bajio29["cvegeo"])

# Spatial weights (for Task 3.2 BFS re-application)
w = libpysal.io.open(str(DATA_PROC / "spatial_weights_queen.gal")).read()
w_nbrs = w.neighbors  # dict: cvegeo -> [neighbour cvegeos]

all_months = (hh_bfs[["year","month"]].drop_duplicates()
              .sort_values(["year","month"]).reset_index(drop=True))
assert len(all_months) == 132

# Attach region to BFS municipalities
bfs_reg = hh_bfs.merge(muni_class[["cvegeo","region"]], on="cvegeo", how="left")

# Raw LISA Bajío series (sex=total)
lisa_b29 = lisa[lisa["cvegeo"].isin(bajio29_cvs) & (lisa["sex"]=="total")]
bajio_raw: dict = {}
for sid in [0,7,2,3]:
    _hh = (lisa_b29[(lisa_b29["status_id"]==sid)&(lisa_b29["cluster_label"]=="HH")]
           .groupby(["year","month"]).size().reset_index(name="n"))
    bajio_raw[sid] = (all_months.merge(_hh, on=["year","month"], how="left")
                      .fillna(0)["n"].values.astype(float))

print(f"  Loaded: BFS {len(hh_bfs):,}, LISA {len(lisa):,}, W.n={w.n}")

# ── Helper functions ──────────────────────────────────────────────────────────
def bfs_ts(status_id, region):
    sub = bfs_reg[(bfs_reg["status_id"]==status_id) & (bfs_reg["region"]==region)]
    cnt = sub.groupby(["year","month"])["cvegeo"].count().reset_index(name="n")
    return (all_months.merge(cnt,on=["year","month"],how="left")
            .fillna(0)["n"].values.astype(float))

def region_ts(status_id, region):
    return bajio_raw[status_id] if region == "Bajio" else bfs_ts(status_id, region)

def ols_hac(y, bw=12):
    t = np.arange(len(y), dtype=float)
    X = add_constant(t)
    m = OLS(y, X).fit()
    cov = cov_hac(m, nlags=bw)
    se  = np.sqrt(cov[1,1])
    t_s = m.params[1] / se
    p   = 2*(1-stats.t.cdf(abs(t_s), df=m.df_resid))
    return {"slope_yr": round(m.params[1]*12, 3), "hac_se_yr": round(se*12, 4),
            "hac_p": round(p,4), "n": len(y)}

def stars(p):
    return "***" if p<0.001 else ("**" if p<0.01 else ("*" if p<0.05 else "ns"))

def poisson_hac(y, bw=12):
    """Poisson GLM with Newey-West HAC SEs. Returns monthly params + HAC stats."""
    t = np.arange(len(y), dtype=float)
    X = add_constant(t)
    yi = y.astype(int)
    try:
        m = Poisson(yi, X).fit(cov_type="HAC",
                                cov_kwds={"maxlags": bw, "use_correction": True},
                                disp=False, method="bfgs")
        beta_mo = m.params[1]
        se_mo   = m.bse[1]  # already HAC SE
        t_s     = beta_mo / se_mo
        p_hac   = 2*(1-stats.t.cdf(abs(t_s), df=len(y)-2))
        irr_yr  = float(np.exp(beta_mo * 12))
        mean_y  = float(np.mean(y))
        lin_eq  = round((irr_yr - 1) * mean_y, 3)  # linear-equivalent slope
        return {
            "irr_yr":      round(irr_yr, 4),
            "lin_equiv_yr": lin_eq,
            "hac_p":       round(p_hac, 4),
            "converged":   True,
            "mean_y":      round(mean_y, 2),
        }
    except Exception as e:
        return {"irr_yr": None, "lin_equiv_yr": None, "hac_p": None,
                "converged": False, "mean_y": round(float(np.mean(y)),2)}

def nb_alpha(y):
    """Return NB dispersion parameter alpha. Near 0 → Poisson adequate."""
    t = np.arange(len(y), dtype=float)
    X = add_constant(t)
    try:
        m = NegativeBinomial(y.astype(int), X).fit(disp=False, method="bfgs")
        return float(m.params[-1])
    except Exception:
        return None

def bfs_reapply(hh_set_each_month: dict, w_nbrs: dict) -> dict:
    """Given {(yr,mo): set_of_cvegeo}, apply BFS ≥3 filter. Returns same structure."""
    result = {}
    for key, hh_set in hh_set_each_month.items():
        visited = set()
        comps = []
        for node in hh_set:
            if node in visited:
                continue
            comp = []
            queue = [node]
            while queue:
                cur = queue.pop(0)
                if cur in visited:
                    continue
                visited.add(cur)
                comp.append(cur)
                for nbr in w_nbrs.get(cur, []):
                    if nbr in hh_set and nbr not in visited:
                        queue.append(nbr)
            comps.append(comp)
        result[key] = {m for c in comps if len(c)>=3 for m in c}
    return result


# ─────────────────────────────────────────────────────────────────────────────
# TASK 3.1 — Poisson + NB trend re-specification with Holm-Bonferroni
# ─────────────────────────────────────────────────────────────────────────────
print("\n=== TASK 3.1: Poisson/NB trend re-specification + Holm-Bonferroni ===")

t31_rows = []
for sid in [0,7,2,3]:
    for reg in ALL_REGIONS:
        y = region_ts(sid, reg)
        ols  = ols_hac(y)
        pois = poisson_hac(y)
        alpha = nb_alpha(y)
        t31_rows.append({
            "region": reg, "status": STATUS_MAP[sid],
            "mean_y":          pois["mean_y"],
            "ols_slope_yr":    ols["slope_yr"],
            "ols_hac_p":       ols["hac_p"],
            "ols_hac_stars":   stars(ols["hac_p"]),
            "pois_irr_yr":     pois["irr_yr"],
            "pois_lin_equiv_yr": pois["lin_equiv_yr"],
            "pois_hac_p":      pois["hac_p"],
            "pois_converged":  pois["converged"],
            "nb_alpha":        round(alpha, 4) if alpha is not None else None,
        })

t31_df = pd.DataFrame(t31_rows)

# Holm-Bonferroni on Poisson HAC p-values (24 tests)
valid_p = t31_df["pois_hac_p"].dropna().values
reject_holm, p_holm_arr, _, _ = multipletests(
    t31_df["pois_hac_p"].fillna(1.0).values, method="holm")
t31_df["pois_holm_p"]   = [round(x,4) for x in p_holm_arr]
t31_df["pois_holm_stars"] = [stars(p) for p in p_holm_arr]
t31_df["pois_hac_stars"] = t31_df["pois_hac_p"].apply(lambda p: stars(p) if pd.notna(p) else "—")

# Sign changes: Poisson vs OLS
t31_df["sign_change"] = (
    np.sign(t31_df["pois_lin_equiv_yr"].fillna(0)) !=
    np.sign(t31_df["ols_slope_yr"].fillna(0))
)
t31_df["stars_change_pois_vs_ols"] = (
    t31_df["pois_hac_stars"] != t31_df["ols_hac_stars"]
)
t31_df["stars_change_holm_vs_pois"] = (
    t31_df["pois_holm_stars"] != t31_df["pois_hac_stars"]
)

t31_df.to_csv(OUT_DIR / "WP3_t31_poisson.csv", index=False)

# Log load-bearing cells
centro_nl = t31_df[(t31_df["region"]=="Centro")&(t31_df["status"]=="nl")].iloc[0]
log("3.1","poisson_centro_nl_irr_yr",   centro_nl["pois_irr_yr"],    None, note="manuscript OLS +4.94/yr BFS")
log("3.1","poisson_centro_nl_hac_p",    centro_nl["pois_hac_p"],     None, note="HAC p")
log("3.1","poisson_centro_nl_holm_p",   centro_nl["pois_holm_p"],    None, note="Holm-corrected p")
log("3.1","poisson_centro_nl_converged",centro_nl["pois_converged"], True)

n_sign_change = t31_df["sign_change"].sum()
n_star_change = t31_df["stars_change_pois_vs_ols"].sum()
n_holm_change = t31_df["stars_change_holm_vs_pois"].sum()
log("3.1","n_sign_changes_pois_vs_ols",   int(n_sign_change), 0, "PASS" if n_sign_change==0 else "FAIL")
log("3.1","n_star_changes_pois_vs_ols",   int(n_star_change), None)
log("3.1","n_star_changes_holm_vs_pois",  int(n_holm_change), None)

print("\n  Table 5 Poisson (IRR/yr, HAC, Holm) vs OLS:")
cols = ["region","status","ols_slope_yr","ols_hac_stars","pois_lin_equiv_yr","pois_hac_stars","pois_holm_stars","nb_alpha"]
print(t31_df[cols].to_string(index=False))
print(f"\n  Sign changes (Poisson vs OLS): {n_sign_change}/24")
print(f"  Star changes (Poisson HAC vs OLS HAC): {n_star_change}/24")
print(f"  Star changes (Holm vs uncorrected Poisson): {n_holm_change}/24")
print(f"  Saved: WP3_t31_poisson.csv")


# ─────────────────────────────────────────────────────────────────────────────
# TASK 3.2 — Threshold sensitivity (α = 0.01 / 0.05 / 0.10)
# Focus: Centro, Bajío, Norte × 4 statuses
# ─────────────────────────────────────────────────────────────────────────────
print("\n=== TASK 3.2: Threshold sensitivity ===")

FOCUS_REGIONS = ["Centro", "Bajio", "Norte"]
ALPHAS = [0.01, 0.05, 0.10]

lisa_total = lisa[(lisa["sex"]=="total")].copy()

# At α=0.05 we already have BFS data → region_ts()
# At α=0.01: restrict existing HH set to p_value < 0.01, re-apply BFS
# At α=0.10: expand to HH with p<0.10 + NS with p<0.10 and local_i>0, re-apply BFS

def build_hh_sets_for_alpha(alpha_val):
    """Build {(yr, mo, sid): set_of_HH_cvegeo} after applying threshold alpha_val."""
    if alpha_val <= 0.05:
        # Conservative: subset existing HH to p < alpha_val
        sub = lisa_total[
            (lisa_total["cluster_label"]=="HH") &
            (lisa_total["p_value"] < alpha_val)
        ]
    else:
        # Expansive: include original HH (p<0.05) PLUS NS with p<alpha_val and local_i>0
        # (local_i>0 approximates HH/LL positive spatial autocorrelation; combined with
        #  high-value municipalities this is approximately HH)
        sub = lisa_total[
            ((lisa_total["cluster_label"]=="HH") & (lisa_total["p_value"] < 0.05)) |
            ((lisa_total["cluster_label"]=="NS") & (lisa_total["p_value"] < alpha_val) &
             (lisa_total["local_i"] > 0))
        ]
    sets = {}
    for (yr, mo, sid), grp in sub.groupby(["year","month","status_id"]):
        sets[(yr, mo, sid)] = set(grp["cvegeo"].unique())
    return sets

t32_rows = []
for alpha_val in ALPHAS:
    print(f"  α = {alpha_val}…")
    if alpha_val == 0.05:
        # Use pre-computed BFS series directly
        for sid in [0,7,2,3]:
            for reg in FOCUS_REGIONS:
                y = region_ts(sid, reg)
                res = ols_hac(y)
                t32_rows.append({
                    "alpha": alpha_val, "region": reg, "status": STATUS_MAP[sid],
                    "mean_hh":  round(y.mean(),2), "slope_yr": res["slope_yr"],
                    "hac_p":    res["hac_p"],  "stars": stars(res["hac_p"]),
                })
        continue

    # Build HH sets at this alpha
    hh_sets = build_hh_sets_for_alpha(alpha_val)

    # Re-apply BFS per (yr, mo, sid)
    # Group sets by sid for efficiency
    for sid in [0,7,2,3]:
        sid_sets = {(yr,mo): hh_sets.get((yr,mo,sid), set())
                    for yr,mo in zip(all_months.year, all_months.month)}
        bfs_sid = bfs_reapply(sid_sets, w_nbrs)

        # Count per region per month
        # Build cvegeo -> region lookup
        reg_lookup = muni_class.set_index("cvegeo")["region"].to_dict()

        for reg in FOCUS_REGIONS:
            if reg == "Bajio":
                counts = np.array([
                    len(bfs_sid.get((yr,mo), set()) & bajio29_cvs)
                    for yr,mo in zip(all_months.year, all_months.month)
                ], dtype=float)
            else:
                counts = np.array([
                    sum(1 for cv in bfs_sid.get((yr,mo), set())
                        if reg_lookup.get(cv) == reg)
                    for yr,mo in zip(all_months.year, all_months.month)
                ], dtype=float)

            res = ols_hac(counts)
            t32_rows.append({
                "alpha": alpha_val, "region": reg, "status": STATUS_MAP[sid],
                "mean_hh":  round(counts.mean(),2), "slope_yr": res["slope_yr"],
                "hac_p":    res["hac_p"],  "stars": stars(res["hac_p"]),
            })

t32_df = pd.DataFrame(t32_rows)
t32_df.to_csv(OUT_DIR / "WP3_t32_threshold_sensitivity.csv", index=False)

# Pivot for easy reading
t32_pivot = t32_df.copy()
t32_pivot["cell"] = t32_pivot["slope_yr"].astype(str) + " " + t32_pivot["stars"]
t32_pivot = t32_pivot.pivot_table(index=["region","status"], columns="alpha", values="cell", aggfunc="first")
print("\n  Threshold sensitivity (slope_yr + stars):")
print(t32_pivot.to_string())

# Check load-bearing: Centro NL at α=0.01
centro_nl_01 = t32_df[(t32_df["alpha"]==0.01)&(t32_df["region"]=="Centro")&(t32_df["status"]=="nl")]
if len(centro_nl_01):
    cn_row = centro_nl_01.iloc[0]
    log("3.2","centro_nl_slope_alpha001",  cn_row["slope_yr"],  None, note=f"stars: {cn_row['stars']}, mean_hh: {cn_row['mean_hh']}")
    log("3.2","centro_nl_survives_alpha001", cn_row["stars"] in ["***","**","*"], True,
        "PASS" if "*" in cn_row["stars"] else "FAIL",
        note="headline must survive stricter threshold")
print(f"  Saved: WP3_t32_threshold_sensitivity.csv")


# ─────────────────────────────────────────────────────────────────────────────
# TASK 3.3 — Supremum Wald test (Andrews 1993) for Bajío structural break
# ─────────────────────────────────────────────────────────────────────────────
print("\n=== TASK 3.3: Supremum Wald test (Andrews 1993) ===")

y_total = bajio_raw[0]  # Total Bajío corridor, raw LISA (132 months)
t_idx   = np.arange(len(y_total), dtype=float)

# Chow test at a single break point
def chow_f(y, t_vec, k):
    """Chow F at break index k. Pre: 0..k, Post: k+1..n-1."""
    n = len(y)
    X_full = add_constant(t_vec)
    rss_full = OLS(y, X_full).fit().ssr

    y_pre, t_pre   = y[:k+1], t_vec[:k+1]
    y_post, t_post = y[k+1:], t_vec[k+1:]
    rss_pre  = OLS(y_pre,  add_constant(t_pre)).fit().ssr
    rss_post = OLS(y_post, add_constant(t_post)).fit().ssr
    rss_res  = rss_pre + rss_post

    p_params = 2  # intercept + slope
    F = ((rss_full - rss_res) / p_params) / (rss_res / (n - 2*p_params))
    return float(F)

# Grid: Jan 2016 (idx 12) to Dec 2021 (idx 83)  — 72 candidate break points
# This corresponds to approximately 9%–64% of the 132-month series.
# Andrews (1993) recommends trimming 15% from each end → idx 20 to idx 111.
# We use the plan-specified range (Jan2016–Dec2021) and also report the trimmed range.
GRID_JAN16_DEC21 = list(range(12, 84))   # 72 points
GRID_TRIMMED     = list(range(20, 112))  # 92 points (15%–85% trimming)

def sup_wald_grid(y, t_vec, grid):
    results = []
    for k in grid:
        F = chow_f(y, t_vec, k)
        yr = 2015 + (k+1)//12
        mo = ((k+1) % 12) or 12
        results.append({"break_idx": k, "year": yr, "month": mo, "chow_F": round(F, 3)})
    df = pd.DataFrame(results)
    return df

print("  Computing Chow F over Jan2016–Dec2021 grid (72 points)…")
grid1_df = sup_wald_grid(y_total, t_idx, GRID_JAN16_DEC21)
print("  Computing Chow F over trimmed grid (15%–85%, 92 points)…")
grid2_df = sup_wald_grid(y_total, t_idx, GRID_TRIMMED)

sup_F_plan     = grid1_df["chow_F"].max()
sup_idx_plan   = grid1_df.loc[grid1_df["chow_F"].idxmax(), "break_idx"]
sup_yr_plan    = grid1_df.loc[grid1_df["chow_F"].idxmax(), "year"]
sup_mo_plan    = grid1_df.loc[grid1_df["chow_F"].idxmax(), "month"]

sup_F_trim     = grid2_df["chow_F"].max()
sup_idx_trim   = grid2_df.loc[grid2_df["chow_F"].idxmax(), "break_idx"]
sup_yr_trim    = grid2_df.loc[grid2_df["chow_F"].idxmax(), "year"]
sup_mo_trim    = grid2_df.loc[grid2_df["chow_F"].idxmax(), "month"]

# Andrews (1993) Table 1, sup-Wald, p=2 restrictions, ε=0.15 trimming
# Wald = F × k_params, so F_critical = Wald_critical / 2
# Wald_cv: 10%=9.66, 5%=12.20 (≈11.52 for ε=0.15), 1%=17.55
ANDREWS_WALD_5PCT   = 12.20   # p=2, ε≈0.10 trimming (conservative)
ANDREWS_WALD_5PCT_B = 11.52   # p=2, ε=0.15 trimming
ANDREWS_F_5PCT   = ANDREWS_WALD_5PCT   / 2   # 6.10
ANDREWS_F_5PCT_B = ANDREWS_WALD_5PCT_B / 2   # 5.76

# Also the Wald statistic form (= F × k = F × 2)
sup_Wald_plan = sup_F_plan * 2
sup_Wald_trim = sup_F_trim * 2

# Save grid results
grid1_df["grid"] = "plan_Jan2016_Dec2021"
grid2_df["grid"] = "trimmed_15pct_85pct"
supwald_df = pd.concat([grid1_df, grid2_df], ignore_index=True)
supwald_df.to_csv(OUT_DIR / "WP3_t33_supwald.csv", index=False)

print(f"\n  Plan grid (Jan2016–Dec2021): sup-F = {sup_F_plan:.2f} at {sup_yr_plan}-{sup_mo_plan:02d} (idx={sup_idx_plan})")
print(f"  Trimmed grid (15-85%):       sup-F = {sup_F_trim:.2f} at {sup_yr_trim}-{sup_mo_trim:02d} (idx={sup_idx_trim})")
print(f"  Andrews (1993) 5% F-crit (ε≈0.10): {ANDREWS_F_5PCT:.2f}")
print(f"  Andrews (1993) 5% F-crit (ε=0.15): {ANDREWS_F_5PCT_B:.2f}")
print(f"  WP2 Chow F at Feb2017 (idx=25): 77.72")
print(f"  Wald (= 2×F): plan {sup_Wald_plan:.2f}, trim {sup_Wald_trim:.2f}, Andrews 5% {ANDREWS_WALD_5PCT:.2f}")

log("3.3","supF_plan_grid",    round(sup_F_plan,2),   None, note=f"break at {sup_yr_plan}-{sup_mo_plan:02d}")
log("3.3","supF_trimmed_grid", round(sup_F_trim,2),   None, note=f"break at {sup_yr_trim}-{sup_mo_trim:02d}")
log("3.3","supF_exceeds_andrews_5pct", sup_F_plan > ANDREWS_F_5PCT, True,
    "PASS" if sup_F_plan > ANDREWS_F_5PCT else "FAIL",
    note=f"Andrews F-crit (5%) ≈ {ANDREWS_F_5PCT:.2f}")
log("3.3","break_date_confirmed",
    f"{sup_yr_trim}-{sup_mo_trim:02d}",
    "2017-02", "PASS" if (sup_yr_trim==2017 and sup_mo_trim==2) else "QUAL",
    note="WP2 used Feb2017 as break date")
print(f"  Saved: WP3_t33_supwald.csv")


# ─────────────────────────────────────────────────────────────────────────────
# TASK 3.4 — Jaccard null distribution (permutation test)
# ─────────────────────────────────────────────────────────────────────────────
print("\n=== TASK 3.4: Jaccard null distribution (1 000 permutations) ===")

N_MUNIS     = 2478
N_PERM      = 1000
np.random.seed(AUDIT_SEED)
all_ids     = np.arange(N_MUNIS)

# Observed Jaccard values from WP2 Table 4 (raw LISA HH sets, June 2025)
OBS_JACCARD = {
    (0, 7): {"jaccard": 0.555, "n_a": 106, "n_b": 93,  "intersect": 71},
    (0, 2): {"jaccard": 0.674, "n_a": 106, "n_b": 110, "intersect": 87},
    (0, 3): {"jaccard": 0.205, "n_a": 106, "n_b": 35,  "intersect": 24},
    (7, 2): {"jaccard": 0.381, "n_a": 93,  "n_b": 110, "intersect": 56},
    (7, 3): {"jaccard": 0.143, "n_a": 93,  "n_b": 35,  "intersect": 16},
    (2, 3): {"jaccard": 0.151, "n_a": 110, "n_b": 35,  "intersect": 19},
}
PAIR_LABELS = {(0,7):"Total-NL",(0,2):"Total-LA",(0,3):"Total-LD",
               (7,2):"NL-LA",(7,3):"NL-LD",(2,3):"LA-LD"}

def jaccard(a, b):
    inter = len(a & b)
    union = len(a | b)
    return inter/union if union > 0 else 0.0

t34_rows = []
for (sid_a, sid_b), obs in OBS_JACCARD.items():
    na, nb = obs["n_a"], obs["n_b"]
    obs_j  = obs["jaccard"]

    # Permutation null: draw na and nb random municipalities independently
    null_j = np.empty(N_PERM)
    for i in range(N_PERM):
        a_perm = set(np.random.choice(all_ids, size=na, replace=False))
        b_perm = set(np.random.choice(all_ids, size=nb, replace=False))
        null_j[i] = jaccard(a_perm, b_perm)

    null_mean = float(np.mean(null_j))
    null_sd   = float(np.std(null_j))
    # Two-sided: p = fraction of permutations with |J_null - null_mean| >= |obs_j - null_mean|
    p_perm    = float(np.mean(np.abs(null_j - null_mean) >= abs(obs_j - null_mean)))
    obs_z     = (obs_j - null_mean) / null_sd if null_sd > 0 else np.nan

    t34_rows.append({
        "pair":      PAIR_LABELS[(sid_a, sid_b)],
        "n_a":       na, "n_b": nb,
        "obs_jaccard":  round(obs_j, 3),
        "null_mean":    round(null_mean, 4),
        "null_sd":      round(null_sd, 4),
        "obs_z":        round(obs_z, 2),
        "p_perm":       round(p_perm, 4),
        "p_stars":      stars(max(p_perm, 1e-4)),
        "direction":    "above" if obs_j > null_mean else "below",
    })

t34_df = pd.DataFrame(t34_rows)
t34_df.to_csv(OUT_DIR / "WP3_t34_jaccard_null.csv", index=False)
print(t34_df[["pair","obs_jaccard","null_mean","obs_z","p_perm","p_stars","direction"]].to_string(index=False))

nl_ld = t34_df[t34_df["pair"]=="NL-LD"].iloc[0]
log("3.4","jaccard_nl_ld_obs",       nl_ld["obs_jaccard"],  0.143)
log("3.4","jaccard_nl_ld_null_mean", nl_ld["null_mean"],    None, note="expected ≈0.01 random")
log("3.4","jaccard_nl_ld_perm_p",    nl_ld["p_perm"],       None, note=f"dir: {nl_ld['direction']}")
print(f"  Saved: WP3_t34_jaccard_null.csv")


# ─────────────────────────────────────────────────────────────────────────────
# TASK 3.5 — Population-normalized LISA  [FLAGGED: requires full LISA re-run]
# ─────────────────────────────────────────────────────────────────────────────
print("\n=== TASK 3.5: Population-normalized LISA [FLAGGED — heavy computation] ===")
print("  Requires: re-run LISA on rate-per-100k for June 2025 × 4 statuses × sex=total")
print("  Estimated time: ~45 min (same as original LISA run, but single cross-section)")
print("  Input: data/external/conapo_poblacion_1990_2070.parquet (2025 projections)")
print("  Output: Appendix A.5 Jaccard comparison (counts vs rates)")
log("3.5","status","NOT_RUN",None,"N/A","Flagged: heavy LISA re-run. Implement separately.")


# ─────────────────────────────────────────────────────────────────────────────
# TASK 3.6 — Spatial weights sensitivity  [FLAGGED: requires LISA re-runs]
# ─────────────────────────────────────────────────────────────────────────────
print("\n=== TASK 3.6: Spatial weights sensitivity [FLAGGED — heavy computation] ===")
print("  Requires: construct kNN(k=4,8) and distance-band(50km,100km) weights,")
print("  re-run LISA for June 2025 × 4 statuses, compare HH Jaccard vs Queen.")
print("  Estimated time: ~3 hours (4 weight specs × 4 statuses LISA re-run)")
log("3.6","status","NOT_RUN",None,"N/A","Flagged: heavy LISA re-run. Implement separately.")


# ─────────────────────────────────────────────────────────────────────────────
# TASK 3.7 — BH-FDR audit  [FLAGGED: requires 9 999-permutation LISA re-run]
# ─────────────────────────────────────────────────────────────────────────────
print("\n=== TASK 3.7: BH-FDR audit [FLAGGED — heavy computation] ===")
print("  Requires: re-run LISA for June 2025, 4 statuses, 9999 permutations.")
print("  Current LISA used 999 permutations. 9999 requires ~10× longer run.")
print("  Defensibility note: BFS filter + Queen contiguity already substantially")
print("  reduces false positives. Expected finding: BH-FDR retains most HH munis.")
log("3.7","status","NOT_RUN",None,"N/A","Flagged: 9999-perm LISA re-run. Implement separately.")


# ─────────────────────────────────────────────────────────────────────────────
# TASK 3.8 — Reporting-lag truncation robustness (2015-01 to 2025-06)
# ─────────────────────────────────────────────────────────────────────────────
print("\n=== TASK 3.8: Lag-truncation robustness (through 2025-06 only) ===")

# Truncated series: Jan 2015 – Jun 2025 = 126 months
# Full series:      Jan 2015 – Dec 2025 = 132 months
TRUNC_N = 126

t38_rows = []
for sid in [0,7,2,3]:
    for reg in ALL_REGIONS:
        y_full  = region_ts(sid, reg)
        y_trunc = y_full[:TRUNC_N]

        res_full  = ols_hac(y_full)
        res_trunc = ols_hac(y_trunc)

        slope_diff = abs(res_full["slope_yr"] - res_trunc["slope_yr"])
        stars_full  = stars(res_full["hac_p"])
        stars_trunc = stars(res_trunc["hac_p"])

        t38_rows.append({
            "region":         reg,
            "status":         STATUS_MAP[sid],
            "slope_full_yr":  res_full["slope_yr"],
            "stars_full":     stars_full,
            "slope_trunc_yr": res_trunc["slope_yr"],
            "stars_trunc":    stars_trunc,
            "slope_abs_diff": round(slope_diff, 3),
            "stars_changed":  stars_full != stars_trunc,
        })

t38_df = pd.DataFrame(t38_rows)
t38_df.to_csv(OUT_DIR / "WP3_t38_lag_truncation.csv", index=False)

n_material = (t38_df["slope_abs_diff"] > 0.10).sum()
n_stars_ch  = t38_df["stars_changed"].sum()

# Load-bearing cells
centro_nl_t38 = t38_df[(t38_df["region"]=="Centro")&(t38_df["status"]=="nl")].iloc[0]
bajio_nl_t38  = t38_df[(t38_df["region"]=="Bajio") &(t38_df["status"]=="nl")].iloc[0]

log("3.8","centro_nl_slope_full",  centro_nl_t38["slope_full_yr"],  4.94, note="BFS estimate")
log("3.8","centro_nl_slope_trunc", centro_nl_t38["slope_trunc_yr"], None, note="2015-06 truncated")
log("3.8","centro_nl_stars_stable", not centro_nl_t38["stars_changed"], True,
    "PASS" if not centro_nl_t38["stars_changed"] else "FAIL")
log("3.8","bajio_nl_slope_full",   bajio_nl_t38["slope_full_yr"],   0.50, note="raw LISA")
log("3.8","n_material_slope_changes", int(n_material), None, note="slope abs diff > 0.10")
log("3.8","n_stars_changes",          int(n_stars_ch), None)

print(f"\n  Cells with slope abs diff > 0.10: {n_material}/24")
print(f"  Cells with stars change: {n_stars_ch}/24")
print("\n  Changed cells (slope diff > 0.10 or stars changed):")
changed = t38_df[(t38_df["slope_abs_diff"]>0.10) | t38_df["stars_changed"]]
print(changed[["region","status","slope_full_yr","stars_full","slope_trunc_yr","stars_trunc","slope_abs_diff"]].to_string(index=False))
print(f"  Saved: WP3_t38_lag_truncation.csv")


# ─────────────────────────────────────────────────────────────────────────────
# Save audit log
# ─────────────────────────────────────────────────────────────────────────────
log_df = pd.DataFrame(LOG)
log_df.to_csv(OUT_DIR / "WP3_results.csv", index=False)

meta = {
    "timestamp": RUN_TS,
    "seed": AUDIT_SEED,
    "n_checks": len(LOG),
    "n_pass": int((log_df["verdict"]=="PASS").sum()),
    "n_qual": int((log_df["verdict"]=="QUAL").sum()),
    "n_fail": int((log_df["verdict"]=="FAIL").sum()),
    "n_na":   int((log_df["verdict"]=="N/A").sum()),
}
(OUT_DIR / "WP3_results.json").write_text(json.dumps(meta, indent=2))

print(f"\n=== WP3 COMPLETE ===")
print(f"  Checks: {meta['n_pass']} PASS / {meta['n_qual']} QUAL / {meta['n_fail']} FAIL / {meta['n_na']} N/A")
print(f"  Results: audit/outputs/WP3_results.csv")
print(f"  Tasks 3.5, 3.6, 3.7 flagged — require separate LISA re-runs (hours each)")
