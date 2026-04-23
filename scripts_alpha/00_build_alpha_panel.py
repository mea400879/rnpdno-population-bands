"""Build the alpha panel (monthly long) and the 3 cross-sections from
the three RNPDNO stratum CSVs plus the band denominator table.

Inputs
------
- data/raw/rnpdno_disappeared_not_located.csv  (status_id == 7)
- data/raw/rnpdno_located_alive.csv            (status_id == 2)
- data/raw/rnpdno_located_dead.csv             (status_id == 3)
- data/interim/alpha/band_denom.parquet

Outputs
-------
- data/interim/alpha/alpha_panel_long.parquet
- data/interim/alpha/alpha_cross_sections.parquet
- reports/alpha/00_alpha_panel.log
"""
from __future__ import annotations

import sys
import traceback
from pathlib import Path

import polars as pl

# Allow `python scripts_alpha/00_build_alpha_panel.py` to resolve the
# sibling package import (filenames starting with a digit block `-m`).
_REPO = Path(__file__).resolve().parents[1]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from scripts_alpha._utils import (
    CROSS_SECTION_YEARS,
    SENTINEL_SUFFIXES,
    STATUS_ID_MAP,
)

REPO = Path(__file__).resolve().parents[1]
RAW = REPO / "data" / "raw"
INTERIM_ALPHA = REPO / "data" / "interim" / "alpha"
REPORTS_ALPHA = REPO / "reports" / "alpha"

STRATA = [
    ("not_located",   7, RAW / "rnpdno_disappeared_not_located.csv", 34_617),
    ("located_alive", 2, RAW / "rnpdno_located_alive.csv",           37_379),
    ("located_dead",  3, RAW / "rnpdno_located_dead.csv",             9_936),
]

EXPECTED_TOTAL_ROWS = sum(r for _, _, _, r in STRATA)  # 81_932

METRIC_COLS = ["male", "female", "undefined", "total"]


def load_stratum(path: Path, expected_status_id: int,
                 expected_label: str) -> pl.DataFrame:
    df = pl.read_csv(path)
    uniq = df["status_id"].unique().to_list()
    if uniq != [expected_status_id]:
        raise ValueError(
            f"{path.name}: expected status_id=[{expected_status_id}] "
            f"(→ {expected_label}), got {uniq}"
        )
    df = (
        df.with_columns(
            pl.col("cvegeo").cast(pl.Utf8).str.zfill(5),
        )
        .drop(["cve_estado", "cve_mun", "state", "municipality"])
        .with_columns(
            pl.col("status_id").replace_strict(STATUS_ID_MAP).alias("status"),
        )
    )
    return df


def person_totals_by_status(df: pl.DataFrame) -> pl.DataFrame:
    return (
        df.group_by("status")
        .agg(
            pl.len().alias("rows"),
            pl.col("total").sum().alias("person_sum"),
        )
        .sort("status")
    )


def main() -> None:
    log_lines: list[str] = []

    def log(msg: str = "") -> None:
        log_lines.append(msg)
        print(msg)

    # --- load + concat ----------------------------------------------------
    frames: list[pl.DataFrame] = []
    for label, sid, path, expected_rows in STRATA:
        df = load_stratum(path, sid, label)
        if df.height != expected_rows:
            raise ValueError(
                f"{path.name}: expected {expected_rows:,} rows, got {df.height:,}"
            )
        frames.append(df)

    panel = pl.concat(frames, how="vertical_relaxed")
    if panel.height != EXPECTED_TOTAL_ROWS:
        raise ValueError(
            f"concat row count mismatch: expected {EXPECTED_TOTAL_ROWS:,}, "
            f"got {panel.height:,}"
        )

    log("=" * 72)
    log("[00] build_alpha_panel — QA log")
    log("=" * 72)
    log(f"strata rows: {[(l, f.height) for (l, _, _, _), f in zip(STRATA, frames)]}")
    log(f"concatenated rows: {panel.height:,}  (expected {EXPECTED_TOTAL_ROWS:,})")

    # --- (a) pre-sentinel totals -----------------------------------------
    pre = person_totals_by_status(panel)
    log("")
    log("(a) pre-sentinel totals per status")
    log(pre.to_pandas().to_string(index=False))

    # --- (b) sentinel drops ----------------------------------------------
    is_sentinel = (
        pl.col("cvegeo").str.ends_with(SENTINEL_SUFFIXES[0])
        | pl.col("cvegeo").str.ends_with(SENTINEL_SUFFIXES[1])
    )
    sentinel_df = panel.filter(is_sentinel).with_columns(
        (pl.col("cvegeo").str.slice(0, 2)
         + pl.col("cvegeo").str.slice(-3, 3)).alias("sentinel_cat"),
    )
    drops = (
        sentinel_df.group_by(["sentinel_cat", "status"])
        .agg(
            pl.len().alias("rows"),
            pl.col("total").sum().alias("person_sum"),
        )
        .sort(["sentinel_cat", "status"])
    )
    log("")
    log(f"(b) sentinel drops — total rows dropped: {sentinel_df.height:,}")
    log(drops.to_pandas().to_string(index=False))

    panel = panel.filter(~is_sentinel)

    # --- (c) post-sentinel totals ----------------------------------------
    post = person_totals_by_status(panel)
    log("")
    log("(c) post-sentinel totals per status")
    log(post.to_pandas().to_string(index=False))

    # --- write panel_long -------------------------------------------------
    panel_long = panel.rename({"cvegeo": "cve_geo"}).select(
        ["cve_geo", "year", "month", "status", *METRIC_COLS]
    )
    INTERIM_ALPHA.mkdir(parents=True, exist_ok=True)
    panel_long.write_parquet(INTERIM_ALPHA / "alpha_panel_long.parquet")

    # --- cross-section extraction ----------------------------------------
    xs_parts: list[pl.DataFrame] = []
    for y in CROSS_SECTION_YEARS:
        part = (
            panel.filter(pl.col("year") == y)
            .group_by(["cvegeo", "status"])
            .agg([pl.col(c).sum() for c in METRIC_COLS])
            .with_columns(pl.lit(y).alias("year"))
        )
        xs_parts.append(part)
    xs = pl.concat(xs_parts, how="vertical_relaxed")

    log("")
    log("(d) cross-section person-totals per (year, status) — pre-join")
    pre_join = (
        xs.group_by(["year", "status"])
        .agg(pl.col("total").sum().alias("person_sum"),
             pl.len().alias("rows"))
        .sort(["year", "status"])
    )
    log(pre_join.to_pandas().to_string(index=False))

    # --- inner-join to band_denom ----------------------------------------
    denom = pl.read_parquet(INTERIM_ALPHA / "band_denom.parquet")

    rnpdno_keys = set(xs["cvegeo"].unique().to_list())
    denom_keys = set(denom["cve_geo"].unique().to_list())
    missing_keys = sorted(rnpdno_keys - denom_keys)

    xs_joined = xs.join(
        denom,
        left_on="cvegeo",
        right_on="cve_geo",
        how="inner",
    ).rename({"cvegeo": "cve_geo"})

    # after the rename, pob column is selected per-year
    xs_joined = xs_joined.with_columns(
        pl.when(pl.col("year") == 2015).then(pl.col("pob_2015"))
          .when(pl.col("year") == 2019).then(pl.col("pob_2019"))
          .when(pl.col("year") == 2025).then(pl.col("pob_2025"))
          .otherwise(None)
          .alias("pob")
    ).select([
        "cve_geo", "nom_ent", "nom_mun", "year", "status",
        *METRIC_COLS, "band_2020", "pob",
    ])

    join_loss_rows = xs.height - xs_joined.height
    lost_person_sum = (
        xs.filter(pl.col("cvegeo").is_in(missing_keys))["total"].sum()
        if missing_keys else 0
    )

    log("")
    log("(e) join-loss report")
    log(f"  cross-section rows pre-join:  {xs.height:,}")
    log(f"  cross-section rows post-join: {xs_joined.height:,}")
    log(f"  rows lost:                    {join_loss_rows:,}")
    log(f"  unique cve_geo lost: {len(missing_keys)}  → {missing_keys}")
    log(f"  person-sum lost:              {lost_person_sum:,}")

    xs_joined.write_parquet(INTERIM_ALPHA / "alpha_cross_sections.parquet")

    # --- write log --------------------------------------------------------
    REPORTS_ALPHA.mkdir(parents=True, exist_ok=True)
    log_path = REPORTS_ALPHA / "00_alpha_panel.log"
    log_path.write_text("\n".join(log_lines) + "\n", encoding="utf-8")

    # --- final summary ---------------------------------------------------
    print("")
    print(
        f"[00] done. panel_rows={panel_long.height}, "
        f"cross_rows={xs_joined.height}, "
        f"sentinels_dropped={sentinel_df.height}, "
        f"join_loss={join_loss_rows}. Awaiting review."
    )


if __name__ == "__main__":
    try:
        main()
    except Exception:
        traceback.print_exc()
        sys.exit(1)
