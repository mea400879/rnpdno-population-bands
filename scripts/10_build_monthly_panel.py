"""
Script 10: Build monthly municipality-level panel from 4 RNPDNO CSVs.

Outputs:
    data/processed/panel_monthly_counts.parquet

Schema: cvegeo, cve_estado, cve_mun, state, municipality,
        year, month, status_id, male, female, undefined, total,
        region, is_bajio
"""

import logging
import warnings
import polars as pl
import geopandas as gpd
from pathlib import Path

# ─── Configuration ────────────────────────────────────────────────────────────
ROOT = Path(__file__).parent.parent
RAW_DIR     = ROOT / "data" / "raw"
PROCESSED_DIR = ROOT / "data" / "processed"
EXTERNAL_DIR  = ROOT / "data" / "external"
LOGS_DIR    = ROOT / "logs"

RAW_FILES = {
    0: "rnpdno_total.csv",
    7: "rnpdno_disappeared_not_located.csv",
    2: "rnpdno_located_alive.csv",
    3: "rnpdno_located_dead.csv",
}

YEAR_START  = 2015
YEAR_END    = 2025
STATUS_IDS  = [0, 2, 3, 7]

# ─── Logging ──────────────────────────────────────────────────────────────────
LOGS_DIR.mkdir(exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOGS_DIR / "pipeline.log"),
        logging.StreamHandler(),
    ],
)
log = logging.getLogger(__name__)

# ─── Helpers ──────────────────────────────────────────────────────────────────

def sentinel_mask(cvegeo_col: pl.Expr) -> pl.Expr:
    """True for sentinel geocodes: ends in 998/999 or equals 99998."""
    return (cvegeo_col == 99998) | (cvegeo_col % 1000).is_in([998, 999])


def load_and_concat() -> pl.DataFrame:
    frames = []
    for status_id, fname in RAW_FILES.items():
        df = pl.read_csv(RAW_DIR / fname)
        log.info(f"  {fname}: {df.shape[0]:,} rows, status_id={df['status_id'].unique().to_list()}")
        frames.append(df)
    combined = pl.concat(frames)
    log.info(f"Combined raw: {combined.shape[0]:,} rows")
    return combined


def remove_sentinels(df: pl.DataFrame) -> pl.DataFrame:
    mask = sentinel_mask(pl.col("cvegeo"))
    n_before = len(df)
    df_clean = df.filter(~mask)
    n_removed = n_before - len(df_clean)
    log.info(f"Sentinels removed: {n_removed:,} rows  ({n_before:,} → {len(df_clean):,})")
    # Log total persons excluded
    persons_excluded = df.filter(mask)["total"].sum()
    log.info(f"  Persons in sentinel rows: {persons_excluded:,}")
    return df_clean


def build_name_lookup(df: pl.DataFrame) -> pl.DataFrame:
    """cvegeo (5-char str) → cve_estado, state, cve_mun, municipality."""
    return (
        df.select(["cvegeo", "cve_estado", "state", "cve_mun", "municipality"])
        .unique(subset=["cvegeo"])
        .with_columns([
            pl.col("cvegeo").cast(pl.Utf8).str.zfill(5),
            pl.col("cve_estado").cast(pl.Utf8).str.zfill(2),
            pl.col("cve_mun").cast(pl.Utf8).str.zfill(3),
        ])
    )


def build_state_lookup(df: pl.DataFrame) -> pl.DataFrame:
    """cve_estado (2-char str) → state name."""
    return (
        df.select(["cve_estado", "state"])
        .unique(subset=["cve_estado"])
        .with_columns(pl.col("cve_estado").cast(pl.Utf8).str.zfill(2))
    )


def build_full_grid(canonical_cvegeos: list[str]) -> pl.DataFrame:
    """
    Cross-product: canonical municipalities × 132 year-months × 4 status_ids.
    Returns DataFrame with columns: cvegeo, year, month, status_id.
    """
    n_months = (YEAR_END - YEAR_START + 1) * 12
    years  = [y for y in range(YEAR_START, YEAR_END + 1) for _ in range(12)]
    months = [m for _ in range(YEAR_START, YEAR_END + 1) for m in range(1, 13)]

    munis_df   = pl.DataFrame({"cvegeo": canonical_cvegeos})
    ym_df      = pl.DataFrame({"year": years, "month": months})
    status_df  = pl.DataFrame({"status_id": STATUS_IDS})

    grid = munis_df.join(ym_df, how="cross").join(status_df, how="cross")
    log.info(
        f"Full grid: {len(grid):,} rows  "
        f"({len(munis_df):,} munis × {n_months} months × {len(STATUS_IDS)} statuses)"
    )
    return grid


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    log.info("=" * 60)
    log.info("Script 10: Build Monthly Panel")
    log.info("=" * 60)
    PROCESSED_DIR.mkdir(exist_ok=True)

    # 1. Load raw CSVs
    log.info("Step 1 — Loading raw CSVs...")
    raw = load_and_concat()

    # 2. Remove sentinels
    log.info("Step 2 — Removing sentinel geocodes...")
    raw_clean = remove_sentinels(raw)

    # 3. Build name/state lookups (before zero-padding raw cvegeo)
    log.info("Step 3 — Building name and state lookups...")
    name_lookup  = build_name_lookup(raw_clean)
    state_lookup = build_state_lookup(raw_clean)
    log.info(f"  Unique municipalities in raw data: {len(name_lookup):,}")
    log.info(f"  Unique states in raw data: {len(state_lookup):,}")

    # 4. Zero-pad cvegeo; aggregate duplicates by summing counts
    counts_raw = (
        raw_clean
        .with_columns(pl.col("cvegeo").cast(pl.Utf8).str.zfill(5))
        .select(["cvegeo", "year", "month", "status_id", "male", "female", "undefined", "total"])
    )
    # Deduplicate: for keys with multiple rows, keep the row with the highest total.
    # Verified against CNB website: the single-person ghost rows are artifacts of
    # late amendments in the RNPDNO export system; the larger row is the correct value.
    n_before_dedup = len(counts_raw)
    counts = (
        counts_raw
        .sort("total", descending=True)
        .unique(subset=["cvegeo", "year", "month", "status_id"], keep="first")
    )
    n_after_dedup = len(counts)
    n_dropped = n_before_dedup - n_after_dedup
    if n_dropped > 0:
        log.warning(
            f"Dropped {n_dropped} ghost duplicate rows (kept max-total row per key)  "
            f"({n_before_dedup:,} → {n_after_dedup:,})"
        )

    # 5. Canonical municipality list from geoparquet
    log.info("Step 5 — Loading canonical municipality list from geoparquet...")
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        gdf = gpd.read_parquet(str(EXTERNAL_DIR / "municipios_2024.geoparquet"))
    geo_df = pl.from_pandas(
        gdf[["cve_geo", "nomgeo"]].rename(columns={"cve_geo": "cvegeo", "nomgeo": "geo_mun_name"})
    )
    canonical_cvegeos = geo_df["cvegeo"].to_list()
    log.info(f"  Canonical municipalities: {len(canonical_cvegeos):,}")

    # 6. Load regional classification
    log.info("Step 6 — Loading regional classification...")
    class_df = (
        pl.read_csv(PROCESSED_DIR / "municipality_classification_v2.csv")
        .with_columns(pl.col("cvegeo").cast(pl.Utf8).str.zfill(5))
        .select(["cvegeo", "region", "is_bajio"])
    )

    # 7. Build full grid (canonical × months × statuses)
    log.info("Step 7 — Building full grid...")
    grid = build_full_grid(canonical_cvegeos)

    # 8. Left join counts → zero-fill nulls
    log.info("Step 8 — Zero-infilling (joining counts onto grid)...")
    panel = (
        grid
        .join(counts, on=["cvegeo", "year", "month", "status_id"], how="left")
        .with_columns([
            pl.col("male").fill_null(0).cast(pl.Int32),
            pl.col("female").fill_null(0).cast(pl.Int32),
            pl.col("undefined").fill_null(0).cast(pl.Int32),
            pl.col("total").fill_null(0).cast(pl.Int32),
        ])
    )
    n_zeroed = panel.filter(pl.col("total") == 0).shape[0]
    log.info(f"  Zero-filled rows: {n_zeroed:,} of {len(panel):,}")

    # 9. Join municipality names (raw lookup preferred; fall back to geoparquet)
    log.info("Step 9 — Joining municipality names...")
    panel = (
        panel
        .join(name_lookup, on="cvegeo", how="left")
        .join(geo_df, on="cvegeo", how="left")
        .with_columns([
            # municipality name
            pl.when(pl.col("municipality").is_null())
              .then(pl.col("geo_mun_name"))
              .otherwise(pl.col("municipality"))
              .alias("municipality"),
            # cve_estado: derive from cvegeo prefix if missing
            pl.when(pl.col("cve_estado").is_null())
              .then(pl.col("cvegeo").str.slice(0, 2))
              .otherwise(pl.col("cve_estado"))
              .alias("cve_estado"),
            # cve_mun: derive from cvegeo suffix if missing
            pl.when(pl.col("cve_mun").is_null())
              .then(pl.col("cvegeo").str.slice(2, 3))
              .otherwise(pl.col("cve_mun"))
              .alias("cve_mun"),
        ])
        .drop("geo_mun_name")
    )

    # Fill state names for municipalities not in raw data
    panel = (
        panel
        .join(state_lookup.rename({"state": "_state_fill"}), on="cve_estado", how="left")
        .with_columns(
            pl.when(pl.col("state").is_null())
              .then(pl.col("_state_fill"))
              .otherwise(pl.col("state"))
              .alias("state")
        )
        .drop("_state_fill")
    )

    # 10. Join region and is_bajio
    log.info("Step 10 — Joining regional classification...")
    panel = panel.join(class_df, on="cvegeo", how="left")

    # 11. Final column selection and type casting
    panel = panel.select([
        pl.col("cvegeo").cast(pl.Utf8),
        pl.col("cve_estado").cast(pl.Utf8),
        pl.col("cve_mun").cast(pl.Utf8),
        pl.col("state").cast(pl.Utf8),
        pl.col("municipality").cast(pl.Utf8),
        pl.col("year").cast(pl.Int32),
        pl.col("month").cast(pl.Int32),
        pl.col("status_id").cast(pl.Int32),
        pl.col("male").cast(pl.Int32),
        pl.col("female").cast(pl.Int32),
        pl.col("undefined").cast(pl.Int32),
        pl.col("total").cast(pl.Int32),
        pl.col("region").cast(pl.Utf8),
        pl.col("is_bajio").cast(pl.Boolean),
    ])

    # 12. Validation
    log.info("Step 12 — Validating panel...")
    n_total = len(panel)
    n_mismatch = panel.filter(
        pl.col("total") != pl.col("male") + pl.col("female") + pl.col("undefined")
    ).shape[0]
    null_counts = {c: panel[c].null_count() for c in panel.columns}
    log.info(f"  Total rows:  {n_total:,}")
    log.info(f"  total != m+f+u mismatches: {n_mismatch}")
    log.info(f"  Statuses:    {sorted(panel['status_id'].unique().to_list())}")
    log.info(f"  Year range:  {panel['year'].min()}–{panel['year'].max()}")
    log.info(f"  Month range: {panel['month'].min()}–{panel['month'].max()}")
    log.info(f"  Unique cvegeo: {panel['cvegeo'].n_unique():,}")
    for col, n_null in null_counts.items():
        if n_null > 0:
            log.warning(f"  NULL in '{col}': {n_null:,} rows")

    # Quick sum check for total status
    total_persons = panel.filter(pl.col("status_id") == 0)["total"].sum()
    log.info(f"  Sum of total (status_id=0): {total_persons:,} person-months")

    # 13. Save
    out_path = PROCESSED_DIR / "panel_monthly_counts.parquet"
    panel.write_parquet(str(out_path))
    log.info(f"Saved → {out_path}")
    log.info("Script 10 complete.")


if __name__ == "__main__":
    main()
