"""
Script 11: Build Queen contiguity spatial weights matrix.

Requires: data/processed/panel_monthly_counts.parquet (from script 10)

Outputs:
    data/processed/spatial_weights_queen.gal
    data/processed/island_municipalities.csv
"""

import logging
import warnings
import polars as pl
import geopandas as gpd
import pandas as pd
from libpysal.weights import Queen
from pathlib import Path

# ─── Configuration ────────────────────────────────────────────────────────────
ROOT          = Path(__file__).parent.parent
PROCESSED_DIR = ROOT / "data" / "processed"
EXTERNAL_DIR  = ROOT / "data" / "external"
LOGS_DIR      = ROOT / "logs"

# ─── Logging ──────────────────────────────────────────────────────────────────
LOGS_DIR.mkdir(exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOGS_DIR / "pipeline.log", mode="a"),
        logging.StreamHandler(),
    ],
)
log = logging.getLogger(__name__)


def main():
    log.info("=" * 60)
    log.info("Script 11: Build Spatial Weights")
    log.info("=" * 60)

    # 1. Load valid municipality list from panel
    log.info("Step 1 — Loading valid municipality list from panel...")
    panel = pl.read_parquet(str(PROCESSED_DIR / "panel_monthly_counts.parquet"))
    valid_cvegeos = set(panel["cvegeo"].unique().to_list())
    log.info(f"  Valid municipalities: {len(valid_cvegeos):,}")

    # 2. Load geometries
    log.info("Step 2 — Loading municipios geoparquet...")
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        gdf = gpd.read_parquet(str(EXTERNAL_DIR / "municipios_2024.geoparquet"))
    log.info(f"  Loaded: {len(gdf):,} municipalities, CRS EPSG:{gdf.crs.to_epsg()}")

    # 3. Ensure EPSG:6372
    if gdf.crs.to_epsg() != 6372:
        gdf = gdf.to_crs(epsg=6372)
        log.info("  Reprojected to EPSG:6372")

    # 4. Standardize cvegeo index, filter to valid municipalities
    gdf["cvegeo"] = gdf["cve_geo"].str.zfill(5)
    gdf = gdf.set_index("cvegeo")
    gdf_valid = gdf.loc[gdf.index.isin(valid_cvegeos)].copy()
    log.info(f"  After filtering to valid munis: {len(gdf_valid):,}")

    n_missing = len(valid_cvegeos) - len(gdf_valid)
    if n_missing > 0:
        log.warning(f"  {n_missing} valid municipalities not found in geometry file")

    # 5. Build Queen contiguity weights (row-standardized)
    log.info("Step 5 — Building Queen contiguity weights (row-standardized)...")
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        w = Queen.from_dataframe(gdf_valid, use_index=True)
    w.transform = "R"

    log.info(f"  Observations:    {w.n:,}")
    log.info(f"  Islands:         {len(w.islands):,}")
    log.info(f"  Min neighbors:   {w.min_neighbors}")
    log.info(f"  Max neighbors:   {w.max_neighbors}")
    log.info(f"  Mean neighbors:  {w.mean_neighbors:.2f}")

    # 6. Save weights (.gal format)
    out_path = PROCESSED_DIR / "spatial_weights_queen.gal"
    w.to_file(str(out_path))
    log.info(f"Saved → {out_path}")

    # 7. Save island list
    island_path = PROCESSED_DIR / "island_municipalities.csv"
    pd.DataFrame({"cvegeo": w.islands}).to_csv(str(island_path), index=False)
    log.info(f"Saved → {island_path}  ({len(w.islands)} islands)")

    log.info("Script 11 complete.")


if __name__ == "__main__":
    main()
