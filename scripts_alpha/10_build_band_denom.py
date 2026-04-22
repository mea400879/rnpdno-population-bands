"""10_build_band_denom.py — Paper α band denominator build.

Inputs:
    data/external/conapo_poblacion_1990_2070.parquet
    data/external/ageeml_catalog.csv  (AGEEML 2025-12 vintage, latin-1)

Outputs:
    data/interim/alpha/band_denom.parquet
    data/interim/alpha/band_drift_2015_2025.parquet
    reports/alpha/10_band_denom.log
"""
from __future__ import annotations

import io
import sys
import traceback
from datetime import datetime, timezone
from pathlib import Path

import polars as pl

REPO_ROOT = Path(__file__).resolve().parents[1]

CONAPO_PATH = REPO_ROOT / "data" / "external" / "conapo_poblacion_1990_2070.parquet"
AGEEML_PATH = REPO_ROOT / "data" / "external" / "ageeml_catalog.csv"

OUT_DIR = REPO_ROOT / "data" / "interim" / "alpha"
BAND_DENOM_PATH = OUT_DIR / "band_denom.parquet"
DRIFT_PATH = OUT_DIR / "band_drift_2015_2025.parquet"
LOG_PATH = REPO_ROOT / "reports" / "alpha" / "10_band_denom.log"

CROSS_YEARS = [2015, 2019, 2020, 2025]

# Half-open intervals [lower, upper)
BAND_BREAKS = [2500, 15000, 50000, 150000, 500000, 1000000]
BAND_LABELS = [
    "community",
    "rural",
    "semi_urban",
    "small_city",
    "medium_city",
    "city",
    "large_city",
]
BAND_ENUM = pl.Enum(BAND_LABELS)


def assign_band(col: str) -> pl.Expr:
    return (
        pl.col(col)
        .cut(BAND_BREAKS, labels=BAND_LABELS, left_closed=True)
        .cast(BAND_ENUM)
    )


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)

    conapo = (
        pl.scan_parquet(CONAPO_PATH)
        .filter(pl.col("year").is_in(CROSS_YEARS))
        .select(["cve_geo", "year", "pob_total"])
        .collect()
    )

    ageeml = (
        pl.read_csv(AGEEML_PATH, encoding="latin-1", infer_schema_length=0)
        .rename({"CVEGEO": "cve_geo", "NOM_ENT": "nom_ent", "NOM_MUN": "nom_mun"})
        .select(["cve_geo", "nom_ent", "nom_mun"])
        .unique(subset=["cve_geo"])
    )

    conapo_2020 = conapo.filter(pl.col("year") == 2020).select("cve_geo")
    excluded = ageeml.join(conapo_2020, on="cve_geo", how="anti").sort("cve_geo")

    wide = conapo.pivot(on="year", index="cve_geo", values="pob_total").rename(
        {str(y): f"pob_{y}" for y in CROSS_YEARS}
    )

    denom = (
        wide.join(ageeml, on="cve_geo", how="left")
        .with_columns(band_2020=assign_band("pob_2020"))
        .select(
            [
                "cve_geo",
                "nom_ent",
                "nom_mun",
                "pob_2015",
                "pob_2019",
                "pob_2020",
                "pob_2025",
                "band_2020",
            ]
        )
        .sort("cve_geo")
    )

    drift = (
        denom.select(
            [
                "cve_geo",
                assign_band("pob_2015").alias("band_2015"),
                pl.col("band_2020"),
                assign_band("pob_2025").alias("band_2025"),
            ]
        )
        .with_columns(
            drift_count=(
                (pl.col("band_2015") != pl.col("band_2020")).cast(pl.Int32)
                + (pl.col("band_2020") != pl.col("band_2025")).cast(pl.Int32)
            )
        )
        .sort("cve_geo")
    )

    denom.write_parquet(BAND_DENOM_PATH)
    drift.write_parquet(DRIFT_PATH)

    buf = io.StringIO()
    ts = datetime.now(timezone.utc).isoformat(timespec="seconds")
    buf.write(f"[10] band_denom build — {ts}\n")
    buf.write(f"     repo_root: {REPO_ROOT}\n")
    buf.write(f"     conapo:    {CONAPO_PATH.name}\n")
    buf.write(f"     ageeml:    {AGEEML_PATH.name}\n")
    buf.write(f"     n_denom rows:  {denom.height}\n")
    buf.write(f"     n_ageeml rows: {ageeml.height}\n\n")

    buf.write("(a) Excluded munis (in AGEEML canonical but not in CONAPO 2020):\n")
    if excluded.height == 0:
        buf.write("    (none)\n")
    else:
        with pl.Config(
            tbl_rows=excluded.height, tbl_width_chars=200, fmt_str_lengths=80
        ):
            buf.write(str(excluded))
            buf.write("\n")
    buf.write("\n")

    band_counts = (
        denom.group_by("band_2020")
        .len()
        .rename({"len": "n"})
        .sort("band_2020")
    )
    buf.write("(b) Per-band muni counts for 2020:\n")
    with pl.Config(tbl_rows=band_counts.height, tbl_width_chars=200):
        buf.write(str(band_counts))
        buf.write("\n")
    buf.write("\n")

    totals = (
        conapo.join(denom.select("cve_geo"), on="cve_geo", how="semi")
        .group_by("year")
        .agg(pl.col("pob_total").sum())
        .sort("year")
    )
    buf.write("(c) National population totals by year (sum over matched munis):\n")
    with pl.Config(tbl_rows=totals.height, tbl_width_chars=200):
        buf.write(str(totals))
        buf.write("\n")
    buf.write("\n")

    n_drifters = drift.filter(pl.col("drift_count") > 0).height
    dist = (
        drift.group_by("drift_count")
        .len()
        .rename({"len": "n"})
        .sort("drift_count")
    )
    crosstab = (
        drift.group_by(["band_2015", "band_2025"])
        .len()
        .rename({"len": "n"})
        .pivot(on="band_2025", index="band_2015", values="n")
        .sort("band_2015")
    )
    buf.write("(d) Drift summary:\n")
    buf.write(f"    n_drifters (drift_count > 0) = {n_drifters}\n")
    buf.write("    drift_count distribution:\n")
    with pl.Config(tbl_rows=dist.height, tbl_width_chars=200):
        buf.write(str(dist))
        buf.write("\n")
    buf.write("    Cross-tab band_2015 (rows) x band_2025 (cols):\n")
    with pl.Config(
        tbl_rows=crosstab.height, tbl_cols=crosstab.width, tbl_width_chars=300
    ):
        buf.write(str(crosstab))
        buf.write("\n")
    buf.write("\n")

    buf.write(
        "(e) Bands assigned using half-open intervals [lower, upper). "
        "Static 2020 assignment used for all analyses; "
        "2015/2025 bands computed for robustness only.\n"
    )

    log_text = buf.getvalue()
    LOG_PATH.write_text(log_text, encoding="utf-8")

    print(log_text)
    print(
        f"[10] done. n_munis={denom.height}, "
        f"n_excluded={excluded.height}, n_drifters={n_drifters}. "
        f"Awaiting review."
    )


if __name__ == "__main__":
    try:
        main()
    except Exception:
        traceback.print_exc()
        sys.exit(1)
