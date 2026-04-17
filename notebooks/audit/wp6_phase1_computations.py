"""
WP6 Phase 1 — All five CC computations.

CC-1  WP6_table5_proportions.csv + WP6_table5_raw_counts.csv
CC-2  WP6_persistence_national.csv + WP6_persistence_bajio.csv
CC-3  WP6_bajio_piecewise.csv
CC-4  WP6_ced_state_slopes.csv
CC-5  WP6_mannwhitney.csv
"""
from pathlib import Path
import numpy as np
import pandas as pd
from scipy import stats as scipy_stats
from statsmodels.regression.linear_model import OLS
from statsmodels.tools.tools import add_constant
from statsmodels.stats.sandwich_covariance import cov_hac
from statsmodels.discrete.discrete_model import Poisson
from statsmodels.stats.multitest import multipletests

PROJECT_ROOT = Path("/home/marco/workspace/work/rnpdno-population-bands")
DATA_PROC    = PROJECT_ROOT / "data" / "processed"
DATA_EXT     = PROJECT_ROOT / "data" / "external"
OUT_DIR      = PROJECT_ROOT / "audit" / "outputs"
OUT_DIR.mkdir(parents=True, exist_ok=True)

STATUS_MAP = {0: "total", 7: "nl", 2: "la", 3: "ld"}
STATUSES   = [0, 7, 2, 3]
BREAK_IDX  = 24   # January 2017 (0-indexed: Jan2015=0, Jan2016=12, Jan2017=24)
N_MONTHS   = 132  # Jan 2015 – Dec 2025

# Month-index grid: shape (132,) where t=0 → Jan 2015
def _month_grid():
    months = []
    for y in range(2015, 2026):
        for m in range(1, 13):
            months.append((y, m))
    assert len(months) == N_MONTHS
    return pd.DataFrame(months, columns=["year", "month"])

MONTH_GRID = _month_grid()

# ── helper: stars ──────────────────────────────────────────────────────────────
def stars(p):
    if p is None or np.isnan(p): return "ns"
    if p < 0.001: return "***"
    if p < 0.01:  return "**"
    if p < 0.05:  return "*"
    return "ns"

# ── helper: OLS + HAC ─────────────────────────────────────────────────────────
def ols_hac_slope(y, bw=12):
    """Returns (slope_yr, ols_p, hac_p, hac_se_yr)."""
    t    = np.arange(len(y), dtype=float)
    X    = add_constant(t)
    mod  = OLS(y.astype(float), X).fit()
    # OLS p
    ols_p = float(mod.pvalues[1])
    # HAC
    cov = cov_hac(mod, nlags=bw)
    se_mo = np.sqrt(cov[1, 1])
    t_hac = mod.params[1] / se_mo
    hac_p = float(2 * (1 - scipy_stats.t.cdf(abs(t_hac), df=mod.df_resid)))
    slope_yr  = float(mod.params[1]) * 12
    hac_se_yr = se_mo * 12
    return slope_yr, ols_p, hac_p, hac_se_yr

# ── helper: Poisson HAC ───────────────────────────────────────────────────────
def poisson_hac(y, offset=None, bw=12):
    """Poisson GLM with HAC SEs. offset must be log-scale. Returns (irr_yr, hac_p)."""
    try:
        t  = np.arange(len(y), dtype=float)
        X  = add_constant(t)
        yi = y.astype(int)
        if offset is not None:
            m = Poisson(yi, X, offset=offset).fit(
                cov_type="HAC", cov_kwds={"maxlags": bw},
                disp=0, maxiter=100)
        else:
            m = Poisson(yi, X).fit(
                cov_type="HAC", cov_kwds={"maxlags": bw},
                disp=0, maxiter=100)
        beta_mo  = float(m.params[1])
        irr_yr   = float(np.exp(beta_mo * 12))
        hac_p    = float(m.pvalues[1])
        return irr_yr, hac_p
    except Exception:
        return None, None


# ══════════════════════════════════════════════════════════════════════════════
# CC-1  Table 5 with proportional DV
# ══════════════════════════════════════════════════════════════════════════════
print("\n=== CC-1: Table 5 proportional DV ===")

panel    = pd.read_parquet(DATA_PROC / "panel_monthly_counts.parquet")
hh_bfs   = pd.read_parquet(DATA_PROC / "hh_clusters_monthly.parquet")
lisa_raw = pd.read_parquet(DATA_PROC / "lisa_monthly_results.parquet")
bajio_df = pd.read_csv(DATA_EXT / "bajio_corridor_municipalities.csv")

bajio_df["cvegeo"] = bajio_df["cvegeo"].astype(str).str.zfill(5)
BAJIO_SET = set(bajio_df["cvegeo"])

# Total municipalities per region (from panel, any month, status_id==0)
panel_s0 = panel[panel["status_id"] == 0]
region_total = (panel_s0.groupby("region")["cvegeo"]
                .nunique().to_dict())   # {'Centro': 602, ...}

# BFS-filtered HH per (year, month, status_id, region)
cve_region = panel_s0[["cvegeo", "region"]].drop_duplicates()
hh_rgn     = hh_bfs.merge(cve_region, on="cvegeo", how="left")
bfs_counts = (hh_rgn.groupby(["year", "month", "status_id", "region"])["cvegeo"]
              .nunique().reset_index(name="n_hh"))

# Bajío raw LISA HH among 29-muni corridor
lisa_tot = lisa_raw[lisa_raw["sex"] == "total"]
bajio_hh = (lisa_tot[lisa_tot["cvegeo"].isin(BAJIO_SET) &
                      (lisa_tot["cluster_label"] == "HH")]
            .groupby(["year", "month", "status_id"])["cvegeo"]
            .nunique().reset_index(name="n_hh"))
bajio_hh["region"] = "Bajio"

REGIONS      = ["Norte", "Norte-Occidente", "Centro-Norte", "Centro", "Sur", "Bajio"]
DENOM        = {**region_total, "Bajio": 29}

cc1_rows_prop = []
cc1_rows_raw  = []

all_hac_p = []   # collect for Holm across 24 cells

for region in REGIONS:
    denom = DENOM[region]
    for sid in STATUSES:
        if region == "Bajio":
            sub = bajio_hh[bajio_hh["status_id"] == sid]
        else:
            sub = bfs_counts[(bfs_counts["region"] == region) &
                              (bfs_counts["status_id"] == sid)]
        # Merge with full 132-month grid
        ts = (MONTH_GRID.merge(sub[["year", "month", "n_hh"]],
                               on=["year", "month"], how="left")
              .fillna(0))
        y_raw  = ts["n_hh"].values
        y_prop = y_raw / denom * 100

        slope_raw, ols_p_raw, hac_p_raw, hac_se_raw = ols_hac_slope(y_raw)
        slope_prop, ols_p_prop, hac_p_prop, hac_se_prop = ols_hac_slope(y_prop)
        irr_yr, pois_hac_p = poisson_hac(
            y_raw,
            offset=np.full(N_MONTHS, np.log(denom))
        )
        all_hac_p.append(hac_p_prop)

        cc1_rows_prop.append({
            "region": region, "status": STATUS_MAP[sid],
            "denom": denom,
            "slope_pct_yr": round(slope_prop, 4),
            "hac_se_pct_yr": round(hac_se_prop, 4),
            "ols_p": round(ols_p_prop, 4),
            "ols_stars": stars(ols_p_prop),
            "hac_p": round(hac_p_prop, 4),
            "hac_stars": stars(hac_p_prop),
            "pois_irr_yr": round(irr_yr, 4) if irr_yr else None,
            "pois_hac_p": round(pois_hac_p, 4) if pois_hac_p else None,
            "pois_hac_stars": stars(pois_hac_p) if pois_hac_p is not None else "ns",
        })
        cc1_rows_raw.append({
            "region": region, "status": STATUS_MAP[sid],
            "slope_yr": round(slope_raw, 4),
            "hac_se_yr": round(hac_se_raw, 4),
            "ols_p": round(ols_p_raw, 4),
            "ols_stars": stars(ols_p_raw),
            "hac_p": round(hac_p_raw, 4),
            "hac_stars": stars(hac_p_raw),
        })

# Holm on proportional HAC p-values (24 tests)
_, p_holm, _, _ = multipletests(all_hac_p, method="holm")
for i, row in enumerate(cc1_rows_prop):
    row["holm_p"]    = round(float(p_holm[i]), 4)
    row["holm_stars"] = stars(float(p_holm[i]))

df_prop = pd.DataFrame(cc1_rows_prop)
df_raw  = pd.DataFrame(cc1_rows_raw)

df_prop.to_csv(OUT_DIR / "WP6_table5_proportions.csv", index=False)
df_raw.to_csv(OUT_DIR / "WP6_table5_raw_counts.csv", index=False)

print(df_prop[["region", "status", "slope_pct_yr", "hac_stars", "pois_hac_stars", "holm_stars"]].to_string(index=False))
print(f"\nSaved WP6_table5_proportions.csv and WP6_table5_raw_counts.csv")


# ══════════════════════════════════════════════════════════════════════════════
# CC-2  Municipality-level persistence
# ══════════════════════════════════════════════════════════════════════════════
print("\n=== CC-2: Municipality persistence ===")

# BFS-filtered persistence nationally
# A (cvegeo, status_id) is BFS-HH in month t if it appears in hh_clusters_monthly
bfs_presence = (hh_bfs.groupby(["cvegeo", "status_id"])
                .apply(lambda g: len(g[["year", "month"]].drop_duplicates()),
                       include_groups=False)
                .reset_index(name="n_months_hh"))
bfs_presence["persistence"] = bfs_presence["n_months_hh"] / N_MONTHS

# Keep > 0.25
national_pers = bfs_presence[bfs_presence["persistence"] > 0.25].copy()

# Add municipality metadata
muni_meta = (panel_s0[["cvegeo", "state", "municipality", "region"]]
             .drop_duplicates())
national_pers = national_pers.merge(muni_meta, on="cvegeo", how="left")
national_pers["status"] = national_pers["status_id"].map(STATUS_MAP)
national_pers = (national_pers[["cvegeo", "municipality", "state", "region",
                                  "status_id", "status", "n_months_hh", "persistence"]]
                 .sort_values(["status_id", "persistence"], ascending=[True, False])
                 .reset_index(drop=True))

national_pers.to_csv(OUT_DIR / "WP6_persistence_national.csv", index=False)
print(f"  National persistence >0.25: {len(national_pers)} rows "
      f"across {national_pers['cvegeo'].nunique()} unique municipalities")
print(national_pers.groupby("status")["cvegeo"].count())

# Bajío persistence — raw LISA HH, pre/post-break
all_months    = MONTH_GRID.copy()
all_months["t_idx"] = np.arange(N_MONTHS)

bajio_per_rows = []
for _, row in bajio_df.iterrows():
    cvg   = row["cvegeo"]
    state = row["state"]
    muni  = row["municipality"]

    for sid in STATUSES:
        sub = (lisa_tot[(lisa_tot["cvegeo"] == cvg) &
                         (lisa_tot["status_id"] == sid) &
                         (lisa_tot["cluster_label"] == "HH")]
               [["year", "month"]].drop_duplicates())

        hh_set = set(zip(sub["year"], sub["month"]))

        # Pre-break: Jan2015–Dec2016 (t=0..23)
        pre_months  = MONTH_GRID.iloc[:BREAK_IDX]  # 24 months
        n_pre_hh    = sum((r.year, r.month) in hh_set
                         for _, r in pre_months.iterrows())
        # Post-break: Jan2017–Dec2025 (t=24..131)
        post_months = MONTH_GRID.iloc[BREAK_IDX:]  # 108 months
        n_post_hh   = sum((r.year, r.month) in hh_set
                         for _, r in post_months.iterrows())

        bajio_per_rows.append({
            "cvegeo": cvg, "municipality": muni, "state": state,
            "status_id": sid, "status": STATUS_MAP[sid],
            "n_pre_hh": n_pre_hh, "pre_persistence": round(n_pre_hh / BREAK_IDX, 3),
            "n_post_hh": n_post_hh, "post_persistence": round(n_post_hh / (N_MONTHS - BREAK_IDX), 3),
        })

df_bajio_per = pd.DataFrame(bajio_per_rows)
df_bajio_per.to_csv(OUT_DIR / "WP6_persistence_bajio.csv", index=False)
print(f"\n  Bajío persistence rows: {len(df_bajio_per)}")
print(df_bajio_per.groupby("status")[["pre_persistence", "post_persistence"]].mean().round(3))


# ══════════════════════════════════════════════════════════════════════════════
# CC-3  Bajío piecewise proportional
# ══════════════════════════════════════════════════════════════════════════════
print("\n=== CC-3: Bajío piecewise proportional ===")

# Use separate segment OLS (same approach as WP2 Chow piecewise), consistent
# with short pre-break window (24 months). HAC bandwidth scaled per segment.

cc3_rows = []

for sid in STATUSES:
    # Raw LISA HH in corridor / 29 × 100
    sub = bajio_hh[bajio_hh["status_id"] == sid]
    ts  = (MONTH_GRID.merge(sub[["year", "month", "n_hh"]],
                             on=["year", "month"], how="left")
           .fillna(0))
    y_raw  = ts["n_hh"].values
    y_prop = y_raw / 29 * 100

    # ── Full period ─────────────────────────────────────────────────────────
    slope_full, ols_p_full, hac_p_full, hac_se_full = ols_hac_slope(y_prop, bw=12)

    # ── Separate segments ───────────────────────────────────────────────────
    y_pre  = y_prop[:BREAK_IDX]   # Jan2015–Dec2016, n=24
    y_post = y_prop[BREAK_IDX:]   # Jan2017–Dec2025, n=108

    # Pre-break: bw=6 (24 months → 1/4 of T is 6)
    slope_pre,  ols_p_pre,  hac_p_pre,  hac_se_pre  = ols_hac_slope(y_pre,  bw=6)
    # Post-break: bw=12
    slope_post, ols_p_post, hac_p_post, hac_se_post = ols_hac_slope(y_post, bw=12)

    # Chow F-statistic on raw count series (integer y, proportional gives same F)
    t_full   = np.arange(N_MONTHS, dtype=float)
    X_full   = add_constant(t_full)
    rss_full = float(OLS(y_prop, X_full).fit().ssr)

    def seg_rss(y_seg, start):
        t_seg = np.arange(len(y_seg), dtype=float)
        return float(OLS(y_seg, add_constant(t_seg)).fit().ssr)

    rss_pre  = seg_rss(y_pre,  0)
    rss_post = seg_rss(y_post, BREAK_IDX)
    k        = 2
    n        = N_MONTHS
    chow_F   = ((rss_full - (rss_pre + rss_post)) / k) / ((rss_pre + rss_post) / (n - 2 * k))
    chow_p   = float(1 - scipy_stats.f.cdf(chow_F, k, n - 2 * k))

    cc3_rows.extend([
        {
            "status": STATUS_MAP[sid],
            "analysis": "full_period",
            "segment": "full (Jan2015–Dec2025)",
            "n": N_MONTHS,
            "slope_pct_yr": round(slope_full, 4),
            "hac_se_pct_yr": round(hac_se_full, 4),
            "hac_p": round(hac_p_full, 4),
            "hac_stars": stars(hac_p_full),
            "ols_p": round(ols_p_full, 4),
            "ols_stars": stars(ols_p_full),
            "chow_F": None, "chow_p": None,
        },
        {
            "status": STATUS_MAP[sid],
            "analysis": "piecewise_segment",
            "segment": "pre (Jan2015–Dec2016)",
            "n": BREAK_IDX,
            "slope_pct_yr": round(slope_pre, 4),
            "hac_se_pct_yr": round(hac_se_pre, 4),
            "hac_p": round(hac_p_pre, 4),
            "hac_stars": stars(hac_p_pre),
            "ols_p": round(ols_p_pre, 4),
            "ols_stars": stars(ols_p_pre),
            "chow_F": round(chow_F, 3), "chow_p": round(chow_p, 4),
        },
        {
            "status": STATUS_MAP[sid],
            "analysis": "piecewise_segment",
            "segment": "post (Jan2017–Dec2025)",
            "n": N_MONTHS - BREAK_IDX,
            "slope_pct_yr": round(slope_post, 4),
            "hac_se_pct_yr": round(hac_se_post, 4),
            "hac_p": round(hac_p_post, 4),
            "hac_stars": stars(hac_p_post),
            "ols_p": round(ols_p_post, 4),
            "ols_stars": stars(ols_p_post),
            "chow_F": None, "chow_p": None,
        },
    ])

df_cc3 = pd.DataFrame(cc3_rows)
df_cc3.to_csv(OUT_DIR / "WP6_bajio_piecewise.csv", index=False)
print(df_cc3[["status","analysis","segment","slope_pct_yr","hac_stars","ols_stars"]].to_string(index=False))
print(f"\nSaved WP6_bajio_piecewise.csv")


# ══════════════════════════════════════════════════════════════════════════════
# CC-4  CED state slopes (raw count HH, OLS + HAC)
# ══════════════════════════════════════════════════════════════════════════════
print("\n=== CC-4: CED state slopes ===")

ced = pd.read_csv(DATA_PROC / "ced_state_hh_timeseries.csv")

cc4_rows = []
for state in sorted(ced["state"].unique()):
    for sid in STATUSES:
        sub = ced[(ced["state"] == state) & (ced["status_id"] == sid)]
        ts  = (MONTH_GRID.merge(sub[["year", "month", "n_hh_munis"]],
                                 on=["year", "month"], how="left")
               .fillna(0))
        y = ts["n_hh_munis"].values

        # Only regress if there is at least one non-zero month
        if y.sum() == 0:
            cc4_rows.append({
                "state": state, "status": STATUS_MAP[sid],
                "mean_hh": 0.0, "max_hh": 0,
                "slope_yr": None, "hac_p": None, "hac_stars": "ns",
                "ols_p": None, "ols_stars": "ns",
            })
            continue

        slope_yr, ols_p, hac_p, hac_se_yr = ols_hac_slope(y)
        cc4_rows.append({
            "state": state, "status": STATUS_MAP[sid],
            "mean_hh": round(float(y.mean()), 2),
            "max_hh": int(y.max()),
            "slope_yr": round(slope_yr, 4),
            "hac_p": round(hac_p, 4),
            "hac_stars": stars(hac_p),
            "ols_p": round(ols_p, 4),
            "ols_stars": stars(ols_p),
        })

df_cc4 = pd.DataFrame(cc4_rows)
df_cc4.to_csv(OUT_DIR / "WP6_ced_state_slopes.csv", index=False)
print(df_cc4[["state","status","slope_yr","hac_stars","ols_stars"]].to_string(index=False))
print(f"\nSaved WP6_ced_state_slopes.csv")


# ══════════════════════════════════════════════════════════════════════════════
# CC-5  Mann-Whitney with INEGI 2020 populations
# ══════════════════════════════════════════════════════════════════════════════
print("\n=== CC-5: Mann-Whitney with INEGI 2020 populations ===")

conapo = pd.read_parquet(DATA_EXT / "conapo_poblacion_1990_2070.parquet")
pop_2020 = conapo[conapo["year"] == 2020].copy()
pop_2020["cvegeo"] = pop_2020["cve_geo"].astype(str).str.zfill(5)
pop_map = pop_2020.set_index("cvegeo")["pob_total"].to_dict()

# BFS-filtered HH sets for June 2025 (per status_id)
lisa_jun25 = lisa_tot[(lisa_tot["year"] == 2025) & (lisa_tot["month"] == 6)]
hh_bfs_jun25 = hh_bfs[(hh_bfs["year"] == 2025) & (hh_bfs["month"] == 6)]

hh_bfs_sets = {}
for sid in STATUSES:
    # BFS-HH for this status in June 2025
    bfs_sid = set(hh_bfs_jun25[hh_bfs_jun25["status_id"] == sid]["cvegeo"])
    hh_bfs_sets[sid] = bfs_sid

print("  BFS-filtered HH sizes June 2025:")
for sid in STATUSES:
    print(f"    {STATUS_MAP[sid]}: {len(hh_bfs_sets[sid])} municipalities")

def get_pops(cvs):
    return np.array([pop_map.get(c, np.nan) for c in cvs
                     if pop_map.get(c) is not None], dtype=float)

PAIRS = [
    (0, 7,  "Total-NL"),
    (0, 2,  "Total-LA"),
    (0, 3,  "Total-LD"),
    (7, 2,  "NL-LA"),
    (7, 3,  "NL-LD"),
    (2, 3,  "LA-LD"),
]

cc5_rows = []
for sid_a, sid_b, label in PAIRS:
    pops_a = get_pops(hh_bfs_sets[sid_a])
    pops_b = get_pops(hh_bfs_sets[sid_b])

    u_stat, mw_p  = scipy_stats.mannwhitneyu(pops_a, pops_b, alternative="two-sided")
    ks_stat, ks_p = scipy_stats.ks_2samp(pops_a, pops_b)

    cc5_rows.append({
        "pair": label,
        "n_a": len(pops_a), "n_b": len(pops_b),
        "median_a": int(np.median(pops_a)), "median_b": int(np.median(pops_b)),
        "u_stat": round(float(u_stat), 1),
        "mw_p": round(float(mw_p), 4),
        "mw_p_gt050": bool(mw_p > 0.50),
        "mw_p_gt005": bool(mw_p > 0.05),
        "ks_stat": round(float(ks_stat), 4),
        "ks_p": round(float(ks_p), 4),
    })

df_cc5 = pd.DataFrame(cc5_rows)
df_cc5.to_csv(OUT_DIR / "WP6_mannwhitney.csv", index=False)
print(df_cc5.to_string(index=False))
print(f"\nSaved WP6_mannwhitney.csv")

print("\n=== All CC outputs written to audit/outputs/ ===")
