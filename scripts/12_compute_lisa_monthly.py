"""Phase 2 — Monthly LISA computation.

Runs Local Moran's I for:
  4 statuses × 132 months × 3 sex categories = 1,584 LISA runs

Also computes Global Moran's I for total sex only:
  4 statuses × 132 months = 528 global runs

Outputs:
  data/processed/lisa_monthly_results.parquet
  data/processed/morans_i_monthly.csv
  data/processed/hh_clusters_monthly.parquet
"""

import sys
import logging
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import polars as pl
import libpysal
from esda.moran import Moran, Moran_Local

# ---------------------------------------------------------------------------
# CONFIG
# ---------------------------------------------------------------------------
ROOT = Path(__file__).resolve().parent.parent
DATA_PROC = ROOT / "data" / "processed"
LOGS_DIR = ROOT / "logs"

PANEL_FILE      = DATA_PROC / "panel_monthly_counts.parquet"
WEIGHTS_FILE    = DATA_PROC / "spatial_weights_queen.gal"
LISA_OUTPUT     = DATA_PROC / "lisa_monthly_results.parquet"
MORAN_OUTPUT    = DATA_PROC / "morans_i_monthly.csv"
HH_CLUSTERS_OUT = DATA_PROC / "hh_clusters_monthly.parquet"

STATUS_IDS  = [0, 2, 3, 7]
STATUS_IDX  = {0: 0, 2: 1, 3: 2, 7: 3}
SEX_COLS    = ["total", "male", "female"]
SEX_IDX     = {"total": 0, "male": 1, "female": 2}

YEARS       = list(range(2015, 2026))   # 11 years
MONTHS      = list(range(1, 13))        # 12 months
YEAR_MONTHS = [(y, m) for y in YEARS for m in MONTHS]  # 132 periods

PERMUTATIONS    = 999
ALPHA           = 0.05
MIN_CLUSTER_SZ  = 3
RANDOM_SEED     = 42
CHUNK_SIZE      = 100          # runs per partial-save

CLUSTER_CODE = {0: "NS", 1: "HH", 2: "LL", 3: "LH", 4: "HL"}

# ---------------------------------------------------------------------------
# LOGGING
# ---------------------------------------------------------------------------
LOGS_DIR.mkdir(exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    handlers=[
        logging.FileHandler(LOGS_DIR / "pipeline.log", mode="a"),
        logging.StreamHandler(sys.stdout),
    ],
)
log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# BFS connected components
# ---------------------------------------------------------------------------
def connected_components_hh(hh_set: set, neighbors: dict) -> list[list]:
    """Return list of connected components (each a list of cvegeo) with size >= MIN_CLUSTER_SZ."""
    visited = set()
    components = []
    for start in hh_set:
        if start in visited:
            continue
        comp = []
        queue = [start]
        while queue:
            node = queue.pop()
            if node in visited:
                continue
            visited.add(node)
            if node in hh_set:
                comp.append(node)
                for nb in neighbors.get(node, []):
                    if nb in hh_set and nb not in visited:
                        queue.append(nb)
        if comp:
            components.append(comp)
    return [c for c in components if len(c) >= MIN_CLUSTER_SZ]


# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------
def main():
    np.random.seed(RANDOM_SEED)

    # --- Spatial weights --------------------------------------------------
    log.info("Loading spatial weights...")
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        w = libpysal.io.open(str(WEIGHTS_FILE)).read()
    w.transform = "R"
    id_order = w.id_order          # list of cvegeo strings, length n_munis
    n_munis  = w.n
    log.info(f"Weights: {n_munis} obs, {w.mean_neighbors:.2f} mean neighbors, {len(w.islands)} islands")

    neighbors_dict = {cvegeo: list(w.neighbors[cvegeo]) for cvegeo in id_order}
    muni_to_idx = {cvegeo: i for i, cvegeo in enumerate(id_order)}

    # --- Panel → 5-D numpy array for O(1) value lookup -------------------
    # shape: (n_status, n_years, n_months, n_sex, n_munis)  float32
    log.info("Loading panel and building value lookup array...")
    panel = pl.read_parquet(PANEL_FILE)
    panel_pd = panel.select(
        ["cvegeo", "year", "month", "status_id", "total", "male", "female"]
    ).to_pandas()

    n_st, n_yr, n_mo = len(STATUS_IDS), len(YEARS), len(MONTHS)
    data_arr = np.zeros((n_st, n_yr, n_mo, 3, n_munis), dtype=np.float32)

    st_idx   = panel_pd["status_id"].map(STATUS_IDX).values
    yr_idx   = (panel_pd["year"] - 2015).values.astype(int)
    mo_idx   = (panel_pd["month"] - 1).values.astype(int)
    mu_idx   = panel_pd["cvegeo"].map(muni_to_idx).values

    # Drop rows whose cvegeo isn't in the weights matrix (should be none)
    valid = ~np.isnan(mu_idx.astype(float))
    if not valid.all():
        log.warning(f"{(~valid).sum()} panel rows not in weights — skipping")
        st_idx = st_idx[valid]; yr_idx = yr_idx[valid]
        mo_idx = mo_idx[valid]; mu_idx = mu_idx[valid].astype(int)
        panel_pd = panel_pd[valid]
    else:
        mu_idx = mu_idx.astype(int)

    for sex_i, sex_col in enumerate(SEX_COLS):
        vals = panel_pd[sex_col].values.astype(np.float32)
        data_arr[st_idx, yr_idx, mo_idx, sex_i, mu_idx] = vals

    log.info("Value lookup array ready.")
    del panel, panel_pd   # free memory

    # --- Accumulation arrays (pre-sized for efficiency) -------------------
    n_runs  = len(STATUS_IDS) * len(YEAR_MONTHS) * len(SEX_COLS)  # 1,584
    total_N = n_runs * n_munis  # ~3.9M rows

    log.info(f"Total LISA runs: {n_runs} → ~{total_N:,} output rows")

    # We accumulate in large pre-allocated numpy arrays
    cvegeo_out      = np.tile(np.array(id_order, dtype=object), n_runs)  # object arr of strs
    year_out        = np.empty(total_N, dtype=np.int16)
    month_out       = np.empty(total_N, dtype=np.int8)
    status_out      = np.empty(total_N, dtype=np.int8)    # raw status_id (use int8 since 0,2,3,7 fit)
    sex_code_out    = np.empty(total_N, dtype=np.int8)    # 0=total,1=male,2=female
    local_i_out     = np.empty(total_N, dtype=np.float32)
    pval_out        = np.empty(total_N, dtype=np.float32)
    cluster_out     = np.empty(total_N, dtype=np.int8)    # 0=NS,1=HH,2=LL,3=LH,4=HL
    zscore_out      = np.empty(total_N, dtype=np.float32)

    moran_rows   = []  # small: 528 dicts
    hh_clust_rows = []

    run_i = 0
    for sid in STATUS_IDS:
        si = STATUS_IDX[sid]
        for y, mo in YEAR_MONTHS:
            yi = y - 2015
            mi = mo - 1

            for sex_col in SEX_COLS:
                xi = SEX_IDX[sex_col]
                values = data_arr[si, yi, mi, xi, :]  # float32 array, length n_munis

                # Run Local LISA
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    lisa = Moran_Local(values, w, permutations=PERMUTATIONS)

                sig    = lisa.p_sim < ALPHA
                q      = lisa.q
                codes  = np.zeros(n_munis, dtype=np.int8)
                codes[sig & (q == 1)] = 1   # HH
                codes[sig & (q == 3)] = 2   # LL
                codes[sig & (q == 2)] = 3   # LH
                codes[sig & (q == 4)] = 4   # HL

                # Fill into pre-allocated arrays
                offset = run_i * n_munis
                year_out   [offset:offset+n_munis] = y
                month_out  [offset:offset+n_munis] = mo
                status_out [offset:offset+n_munis] = sid
                sex_code_out[offset:offset+n_munis] = xi
                local_i_out[offset:offset+n_munis] = lisa.Is.astype(np.float32)
                pval_out   [offset:offset+n_munis] = lisa.p_sim.astype(np.float32)
                cluster_out[offset:offset+n_munis] = codes
                zscore_out [offset:offset+n_munis] = lisa.z_sim.astype(np.float32)

                # Global Moran's I (total sex only)
                if sex_col == "total":
                    with warnings.catch_warnings():
                        warnings.simplefilter("ignore")
                        moran = Moran(values, w, permutations=PERMUTATIONS)
                    moran_rows.append({
                        "status_id": int(sid),
                        "year":      int(y),
                        "month":     int(mo),
                        "morans_i":  float(moran.I),
                        "p_value":   float(moran.p_sim),
                        "z_score":   float(moran.z_sim),
                    })

                    # HH connected components (total sex only)
                    hh_set = {id_order[i] for i in range(n_munis) if codes[i] == 1}
                    comps  = connected_components_hh(hh_set, neighbors_dict)
                    for comp_id, members in enumerate(comps):
                        for cvegeo in members:
                            hh_clust_rows.append({
                                "status_id":   int(sid),
                                "year":        int(y),
                                "month":       int(mo),
                                "cluster_id":  comp_id,
                                "cvegeo":      cvegeo,
                                "cluster_size": len(members),
                            })

                run_i += 1

                if run_i % CHUNK_SIZE == 0 or run_i == n_runs:
                    pct = run_i / n_runs * 100
                    log.info(
                        f"  Run {run_i:4d}/{n_runs} ({pct:5.1f}%) — "
                        f"status={sid} {y}-{mo:02d} {sex_col}"
                    )

    log.info("All LISA runs complete. Building output DataFrames...")

    # Map integer codes → strings
    sex_names     = np.array(["total", "male", "female"], dtype=object)
    cluster_names = np.array(["NS", "HH", "LL", "LH", "HL"], dtype=object)

    # --- lisa_monthly_results.parquet ---
    log.info("Writing lisa_monthly_results.parquet...")
    lisa_df = pl.DataFrame({
        "cvegeo":        cvegeo_out.tolist(),
        "year":          year_out,
        "month":         month_out,
        "status_id":     status_out.astype(np.int32),
        "sex":           sex_names[sex_code_out].tolist(),
        "local_i":       local_i_out,
        "p_value":       pval_out,
        "cluster_label": cluster_names[cluster_out].tolist(),
        "z_score":       zscore_out,
    })
    lisa_df.write_parquet(LISA_OUTPUT)
    log.info(f"  lisa_monthly_results.parquet: {lisa_df.shape[0]:,} rows")

    # --- morans_i_monthly.csv ---
    log.info("Writing morans_i_monthly.csv...")
    moran_df = pl.DataFrame(moran_rows)
    moran_df.write_csv(MORAN_OUTPUT)
    log.info(f"  morans_i_monthly.csv: {moran_df.shape[0]} rows (expected 528)")

    # --- hh_clusters_monthly.parquet ---
    log.info("Writing hh_clusters_monthly.parquet...")
    hh_df = pl.DataFrame(hh_clust_rows) if hh_clust_rows else pl.DataFrame({
        "status_id": pl.Series([], dtype=pl.Int32),
        "year":      pl.Series([], dtype=pl.Int32),
        "month":     pl.Series([], dtype=pl.Int32),
        "cluster_id":   pl.Series([], dtype=pl.Int32),
        "cvegeo":       pl.Series([], dtype=pl.Utf8),
        "cluster_size": pl.Series([], dtype=pl.Int32),
    })
    hh_df.write_parquet(HH_CLUSTERS_OUT)
    log.info(f"  hh_clusters_monthly.parquet: {hh_df.shape[0]:,} rows")

    # --- Quick sanity checks ---
    log.info("--- Sanity checks ---")
    labels_present = lisa_df["cluster_label"].unique().to_list()
    log.info(f"  Cluster labels present: {sorted(labels_present)}")
    hh_counts = (
        lisa_df.filter(pl.col("cluster_label") == "HH")
        .group_by(["status_id", "sex"])
        .agg(pl.len().alias("n"))
    )
    log.info(f"  HH counts by status/sex:\n{hh_counts}")
    log.info(f"  Moran's I range: {moran_df['morans_i'].min():.4f} – {moran_df['morans_i'].max():.4f}")
    p_all_sig = (moran_df["p_value"] < ALPHA).all()
    log.info(f"  All global Moran's I significant (p<{ALPHA}): {p_all_sig}")

    log.info("Script 12 complete.")


if __name__ == "__main__":
    main()
