"""Phase 2 — Concentration metrics + regional HH composition.

Inputs:
  data/processed/panel_monthly_counts.parquet
  data/processed/lisa_monthly_results.parquet
  data/processed/hh_clusters_monthly.parquet

Outputs:
  data/processed/concentration_monthly.csv     — Gini + HHI per status per month
  data/processed/hh_regional_composition.csv   — HH cluster count by region/band
  data/processed/hh_cross_tabulation_latest.csv — cross-tab for the latest month
"""

import sys
import logging
from pathlib import Path

import numpy as np
import polars as pl

# ---------------------------------------------------------------------------
# CONFIG
# ---------------------------------------------------------------------------
ROOT = Path(__file__).resolve().parent.parent
DATA_PROC = ROOT / "data" / "processed"
LOGS_DIR  = ROOT / "logs"

PANEL_FILE     = DATA_PROC / "panel_monthly_counts.parquet"
LISA_FILE      = DATA_PROC / "lisa_monthly_results.parquet"
HH_FILE        = DATA_PROC / "hh_clusters_monthly.parquet"
CLASSIF_FILE   = DATA_PROC / "municipality_classification_v2.csv"

CONC_OUTPUT    = DATA_PROC / "concentration_monthly.csv"
REGIONAL_OUT   = DATA_PROC / "hh_regional_composition.csv"
CROSSTAB_OUT   = DATA_PROC / "hh_cross_tabulation_latest.csv"

STATUS_IDS = [0, 2, 3, 7]
STATUS_NAMES = {0: "total", 2: "located_alive", 3: "located_dead", 7: "not_located"}

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
# GINI + HHI (pure numpy, called per group via polars map_elements)
# ---------------------------------------------------------------------------
def gini(values: np.ndarray) -> float:
    """Gini coefficient on non-negative array."""
    v = np.sort(values[values >= 0].astype(np.float64))
    n = len(v)
    if n == 0 or v.sum() == 0:
        return 0.0
    idx = np.arange(1, n + 1)
    return float((2 * (idx * v).sum()) / (n * v.sum()) - (n + 1) / n)


def hhi(values: np.ndarray) -> float:
    """Herfindahl-Hirschman Index (normalised to [0,1])."""
    v = values[values >= 0].astype(np.float64)
    total = v.sum()
    if total == 0:
        return 0.0
    shares = v / total
    return float((shares ** 2).sum())


# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------
def main():
    # --- Load data --------------------------------------------------------
    log.info("Loading panel...")
    panel = pl.read_parquet(PANEL_FILE)

    log.info("Loading LISA results...")
    lisa = pl.read_parquet(LISA_FILE)

    log.info("Loading HH clusters...")
    hh = pl.read_parquet(HH_FILE)

    # Municipality classification (pop_band, region already in panel)
    # Use panel's region and is_bajio columns
    # For pop_band we need the classification file
    has_classif = CLASSIF_FILE.exists()
    if has_classif:
        classif = pl.read_csv(CLASSIF_FILE).select(["cvegeo", "pop_band"])
        classif = classif.with_columns(pl.col("cvegeo").cast(pl.Utf8).str.zfill(5))
    else:
        log.warning(f"Classification file not found: {CLASSIF_FILE} — pop_band skipped")
        classif = None

    # -----------------------------------------------------------------------
    # 1. Concentration metrics (Gini + HHI) per status × year-month
    # -----------------------------------------------------------------------
    log.info("Computing concentration metrics...")

    # Compute per (status_id, year, month) on total counts
    # Use polars group_by + map_groups
    conc_rows = []

    panel_total = panel.select(["status_id", "year", "month", "cvegeo", "total"])

    status_groups = panel_total.partition_by("status_id", maintain_order=True)

    for sg in status_groups:
        sid = sg["status_id"][0]
        ym_groups = sg.select(["year", "month", "cvegeo", "total"]).partition_by(
            ["year", "month"], maintain_order=True
        )
        for ymg in ym_groups:
            y  = int(ymg["year"][0])
            mo = int(ymg["month"][0])
            vals = ymg["total"].to_numpy().astype(np.float64)
            conc_rows.append({
                "status_id":    int(sid),
                "status_name":  STATUS_NAMES.get(int(sid), str(sid)),
                "year":         y,
                "month":        mo,
                "gini":         gini(vals),
                "hhi":          hhi(vals),
                "n_munis":      len(vals),
                "total_cases":  int(vals.sum()),
            })
        log.info(f"  status_id={sid}: done ({len(ym_groups)} year-months)")

    conc_df = pl.DataFrame(conc_rows)
    conc_df.write_csv(CONC_OUTPUT)
    log.info(f"concentration_monthly.csv: {conc_df.shape[0]} rows (expected 528)")
    log.info(f"  Gini range: {conc_df['gini'].min():.4f} – {conc_df['gini'].max():.4f}")
    log.info(f"  HHI range:  {conc_df['hhi'].min():.4f} – {conc_df['hhi'].max():.4f}")

    # -----------------------------------------------------------------------
    # 2. HH regional composition
    # -----------------------------------------------------------------------
    log.info("Computing HH regional composition...")

    # We need region and is_bajio joined into LISA HH rows
    # Panel already has those columns; join on cvegeo
    muni_meta = (
        panel.select(["cvegeo", "region", "is_bajio"])
        .unique("cvegeo")
    )

    # Filter LISA to total sex + HH only
    hh_lisa = (
        lisa.filter(
            (pl.col("sex") == "total") &
            (pl.col("cluster_label") == "HH")
        )
        .join(muni_meta, on="cvegeo", how="left")
    )

    # Optionally join pop_band
    if classif is not None:
        hh_lisa = hh_lisa.join(classif, on="cvegeo", how="left")

    # Regional composition: count HH municipalities per status × year × month × region
    region_comp = (
        hh_lisa
        .group_by(["status_id", "year", "month", "region", "is_bajio"])
        .agg(pl.len().alias("n_hh_munis"))
        .sort(["status_id", "year", "month", "region"])
    )

    if classif is not None:
        band_comp = (
            hh_lisa
            .group_by(["status_id", "year", "month", "pop_band"])
            .agg(pl.len().alias("n_hh_munis"))
            .sort(["status_id", "year", "month", "pop_band"])
        )
        # Combine region + band into one file (two separate frames, stack vertically with type tag)
        region_comp = region_comp.with_columns(pl.lit("region").alias("grouping_type"))
    else:
        region_comp = region_comp.with_columns(pl.lit("region").alias("grouping_type"))

    region_comp.write_csv(REGIONAL_OUT)
    log.info(f"hh_regional_composition.csv: {region_comp.shape[0]} rows")

    # -----------------------------------------------------------------------
    # 3. HH cross-tabulation — latest available month
    # -----------------------------------------------------------------------
    log.info("Computing HH cross-tabulation for latest month...")

    # Find latest month in LISA output
    latest = (
        lisa.select(["year", "month"])
        .max()
    )
    latest_year  = int(latest["year"][0])
    latest_month = int(latest["month"][0])
    log.info(f"  Latest month: {latest_year}-{latest_month:02d}")

    lisa_latest = lisa.filter(
        (pl.col("year")  == latest_year) &
        (pl.col("month") == latest_month) &
        (pl.col("sex")   == "total")
    )

    # Cross-tab: status × cluster_label counts
    crosstab = (
        lisa_latest
        .group_by(["status_id", "cluster_label"])
        .agg(pl.len().alias("n_munis"))
        .sort(["status_id", "cluster_label"])
        .with_columns(
            pl.col("status_id").cast(pl.Utf8)
            .replace({str(k): v for k, v in STATUS_NAMES.items()})
            .alias("status_name")
        )
        .with_columns(
            pl.lit(f"{latest_year}-{latest_month:02d}").alias("period")
        )
    )

    # Add total HH count per status + HH share
    total_munis = (
        lisa_latest
        .group_by("status_id")
        .agg(pl.len().alias("total_munis"))
    )
    crosstab = (
        crosstab
        .join(total_munis, on="status_id", how="left")
        .with_columns(
            (pl.col("n_munis") / pl.col("total_munis")).alias("pct")
        )
    )

    crosstab.write_csv(CROSSTAB_OUT)
    log.info(f"hh_cross_tabulation_latest.csv: {crosstab.shape[0]} rows")

    # --- Summary ---
    log.info("--- Script 13 complete ---")
    log.info(f"  concentration_monthly.csv:        {CONC_OUTPUT}")
    log.info(f"  hh_regional_composition.csv:      {REGIONAL_OUT}")
    log.info(f"  hh_cross_tabulation_latest.csv:   {CROSSTAB_OUT}")


if __name__ == "__main__":
    main()
