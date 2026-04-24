"""RQ3 monthly and annual band rates - Paper alpha.

Year-to-CONAPO-reference stepwise mapping (no interpolation, per locks):
    year  in {2015, 2016, 2017, 2018}                      -> CONAPO pob_2015
    year  in {2019, 2020, 2021, 2022, 2023, 2024}          -> CONAPO pob_2020
    year  == 2025                                          -> CONAPO pob_2025

Source CONAPO columns used: pob_total, pob_hombres, pob_mujeres per
(cve_geo, year). Band membership comes from band_denom.parquet, which
uses pob_2020 as the canonical CONAPO classification year.

Inputs
------
- data/interim/alpha/alpha_panel_long.parquet (post-sentinel monthly muni)
- data/interim/alpha/band_denom.parquet       (muni -> band_2020)
- data/external/conapo_poblacion_1990_2070.parquet (pob_total + sex)

Outputs
-------
- data/interim/alpha/rq3_band_rates_monthly_national.parquet
- data/interim/alpha/rq3_band_rates_monthly_regional.parquet
- data/interim/alpha/rq3_band_rates_annual_national.parquet
- data/interim/alpha/rq3_band_rates_annual_regional.parquet
- reports/alpha/23_band_rates.log
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

from scripts_alpha._utils import (  # noqa: E402
    BAND_ORDER,
    CESOP_REGION_BY_CVE_ENT,
    CESOP_REGIONS,  # noqa: F401 - public contract
    RATE_SCALE,
    SMALL_DENOM_N_MUNIS,
    STATUS_ORDER,
)

REPO = Path(__file__).resolve().parents[1]
INTERIM_ALPHA = REPO / "data" / "interim" / "alpha"
REPORTS_ALPHA = REPO / "reports" / "alpha"

PANEL_IN = INTERIM_ALPHA / "alpha_panel_long.parquet"
DENOM_IN = INTERIM_ALPHA / "band_denom.parquet"
CONAPO_IN = REPO / "data" / "external" / "conapo_poblacion_1990_2070.parquet"

MONTHLY_NAT_OUT = INTERIM_ALPHA / "rq3_band_rates_monthly_national.parquet"
MONTHLY_REG_OUT = INTERIM_ALPHA / "rq3_band_rates_monthly_regional.parquet"
ANNUAL_NAT_OUT = INTERIM_ALPHA / "rq3_band_rates_annual_national.parquet"
ANNUAL_REG_OUT = INTERIM_ALPHA / "rq3_band_rates_annual_regional.parquet"
LOG_OUT = REPORTS_ALPHA / "23_band_rates.log"

YEARS = list(range(2015, 2026))       # 2015..2025 inclusive, 11 years
MONTHS = list(range(1, 13))
N_MONTHS = len(YEARS) * len(MONTHS)   # 132

EXPECTED_MONTHLY_NAT_ROWS = N_MONTHS * len(BAND_ORDER) * len(STATUS_ORDER)  # 2772
EXPECTED_ANNUAL_NAT_ROWS = len(YEARS) * len(BAND_ORDER) * len(STATUS_ORDER)  # 231


def step_year_expr() -> pl.Expr:
    """Return a polars expression mapping `year` to CONAPO ref year."""
    return (
        pl.when(pl.col("year") <= 2018).then(2015)
          .when(pl.col("year") <= 2024).then(2020)
          .otherwise(2025)
          .cast(pl.Int64)
          .alias("conapo_ref_year")
    )


def main() -> None:
    log_lines: list[str] = []

    def log(msg: str = "") -> None:
        log_lines.append(msg)

    # --- load + enrich --------------------------------------------------
    panel = pl.read_parquet(PANEL_IN)
    muni_band = (
        pl.read_parquet(DENOM_IN)
        .select(["cve_geo", "band_2020"])
        .with_columns(pl.col("band_2020").cast(pl.Utf8))
    )
    conapo = (
        pl.read_parquet(CONAPO_IN)
        .filter(pl.col("year").is_in([2015, 2020, 2025]))
        .select(["cve_geo", "year", "pob_total", "pob_hombres", "pob_mujeres"])
        .rename({"year": "conapo_ref_year"})
    )

    region_lookup = pl.DataFrame(
        {"cve_ent": list(CESOP_REGION_BY_CVE_ENT.keys()),
         "region": list(CESOP_REGION_BY_CVE_ENT.values())},
        schema={"cve_ent": pl.Int64, "region": pl.Utf8},
    )

    # Muni-level CONAPO x band joined once.
    muni_ref = (
        conapo.join(muni_band, on="cve_geo", how="inner")
        .with_columns(
            pl.col("cve_geo").str.slice(0, 2).cast(pl.Int64).alias("cve_ent")
        )
        .join(region_lookup, on="cve_ent", how="left")
    )
    if muni_ref.filter(pl.col("region").is_null()).height:
        raise ValueError("region lookup failed for some munis in CONAPO x band_denom")

    # Band x ref-year population (national).
    band_ref_pob = (
        muni_ref.group_by(["conapo_ref_year", "band_2020"])
        .agg(
            pl.col("pob_total").sum().alias("pob_total_used"),
            pl.col("pob_hombres").sum().alias("pob_male_used"),
            pl.col("pob_mujeres").sum().alias("pob_female_used"),
        )
    )

    # Region x band x ref-year population.
    reg_band_ref_pob = (
        muni_ref.group_by(["region", "conapo_ref_year", "band_2020"])
        .agg(
            pl.col("pob_total").sum().alias("pob_total_used"),
            pl.col("pob_hombres").sum().alias("pob_male_used"),
            pl.col("pob_mujeres").sum().alias("pob_female_used"),
        )
    )

    # Muni count per (region, band) - year-invariant (band_2020 is fixed).
    n_munis_rb = (
        muni_ref.select(["region", "band_2020", "cve_geo"])
        .unique()
        .group_by(["region", "band_2020"])
        .agg(pl.len().alias("n_munis_in_region_band"))
    )

    # Enrich panel with band and region (inner-join drops the 3 excluded munis).
    panel = (
        panel.join(muni_band, on="cve_geo", how="inner")
        .with_columns(
            pl.col("cve_geo").str.slice(0, 2).cast(pl.Int64).alias("cve_ent")
        )
        .join(region_lookup, on="cve_ent", how="left")
    )
    if panel.filter(pl.col("region").is_null()).height:
        raise ValueError("region lookup failed for some munis in panel")

    # --- Aggregation 1: national monthly --------------------------------
    nat_counts = (
        panel.group_by(["year", "month", "band_2020", "status"])
        .agg(
            pl.col("total").sum().alias("n_total"),
            pl.col("male").sum().alias("n_male"),
            pl.col("female").sum().alias("n_female"),
            pl.col("undefined").sum().alias("n_undefined"),
        )
    )

    grid_nat = (
        pl.DataFrame({"year": YEARS}, schema={"year": pl.Int64})
        .join(pl.DataFrame({"month": MONTHS}, schema={"month": pl.Int64}), how="cross")
        .join(pl.DataFrame({"band_2020": BAND_ORDER}), how="cross")
        .join(pl.DataFrame({"status": STATUS_ORDER}), how="cross")
    )

    monthly_nat = (
        grid_nat.join(
            nat_counts, on=["year", "month", "band_2020", "status"], how="left"
        )
        .with_columns(
            pl.col("n_total").fill_null(0),
            pl.col("n_male").fill_null(0),
            pl.col("n_female").fill_null(0),
            pl.col("n_undefined").fill_null(0),
        )
        .with_columns(step_year_expr())
        .join(band_ref_pob, on=["conapo_ref_year", "band_2020"], how="left")
        .with_columns(
            (pl.col("n_total") / pl.col("pob_total_used") * RATE_SCALE).alias("rate_total"),
            (pl.col("n_male") / pl.col("pob_male_used") * RATE_SCALE).alias("rate_male"),
            (pl.col("n_female") / pl.col("pob_female_used") * RATE_SCALE).alias("rate_female"),
            pl.when((pl.col("n_female") + pl.col("n_male")) > 0)
              .then(pl.col("n_female") / (pl.col("n_female") + pl.col("n_male")))
              .otherwise(None)
              .alias("fsos"),
        )
        .select([
            "year", "month", "band_2020", "status",
            "n_total", "n_male", "n_female", "n_undefined",
            "pob_total_used", "pob_male_used", "pob_female_used",
            "rate_total", "rate_male", "rate_female", "fsos",
        ])
        .sort(["status", "band_2020", "year", "month"])
    )
    if monthly_nat.height != EXPECTED_MONTHLY_NAT_ROWS:
        raise ValueError(
            f"monthly_national: expected {EXPECTED_MONTHLY_NAT_ROWS} rows, "
            f"got {monthly_nat.height}"
        )
    monthly_nat.write_parquet(MONTHLY_NAT_OUT)

    # --- Aggregation 2: regional monthly --------------------------------
    reg_counts = (
        panel.group_by(["region", "year", "month", "band_2020", "status"])
        .agg(
            pl.col("total").sum().alias("n_total"),
            pl.col("male").sum().alias("n_male"),
            pl.col("female").sum().alias("n_female"),
            pl.col("undefined").sum().alias("n_undefined"),
        )
    )

    # Grid restricted to (region, band) pairs that actually have munis.
    nonempty_rb = muni_ref.select(["region", "band_2020"]).unique()
    grid_reg = (
        nonempty_rb
        .join(pl.DataFrame({"year": YEARS}, schema={"year": pl.Int64}), how="cross")
        .join(pl.DataFrame({"month": MONTHS}, schema={"month": pl.Int64}), how="cross")
        .join(pl.DataFrame({"status": STATUS_ORDER}), how="cross")
    )

    monthly_reg = (
        grid_reg.join(
            reg_counts,
            on=["region", "year", "month", "band_2020", "status"],
            how="left",
        )
        .with_columns(
            pl.col("n_total").fill_null(0),
            pl.col("n_male").fill_null(0),
            pl.col("n_female").fill_null(0),
            pl.col("n_undefined").fill_null(0),
        )
        .with_columns(step_year_expr())
        .join(
            reg_band_ref_pob,
            on=["region", "conapo_ref_year", "band_2020"],
            how="left",
        )
        .join(n_munis_rb, on=["region", "band_2020"], how="left")
        .with_columns(
            (pl.col("n_total") / pl.col("pob_total_used") * RATE_SCALE).alias("rate_total"),
            (pl.col("n_male") / pl.col("pob_male_used") * RATE_SCALE).alias("rate_male"),
            (pl.col("n_female") / pl.col("pob_female_used") * RATE_SCALE).alias("rate_female"),
            pl.when((pl.col("n_female") + pl.col("n_male")) > 0)
              .then(pl.col("n_female") / (pl.col("n_female") + pl.col("n_male")))
              .otherwise(None)
              .alias("fsos"),
            (pl.col("n_munis_in_region_band") < SMALL_DENOM_N_MUNIS)
              .alias("small_denom_flag"),
        )
        .select([
            "region", "year", "month", "band_2020", "status",
            "n_total", "n_male", "n_female", "n_undefined",
            "pob_total_used", "pob_male_used", "pob_female_used",
            "rate_total", "rate_male", "rate_female", "fsos",
            "n_munis_in_region_band", "small_denom_flag",
        ])
        .sort(["region", "status", "band_2020", "year", "month"])
    )
    monthly_reg.write_parquet(MONTHLY_REG_OUT)

    # --- Aggregation 3: annual roll-ups ---------------------------------
    annual_nat = (
        monthly_nat.group_by(["year", "band_2020", "status"])
        .agg(
            pl.col("n_total").sum(),
            pl.col("n_male").sum(),
            pl.col("n_female").sum(),
            pl.col("n_undefined").sum(),
            pl.col("pob_total_used").first().alias("pob_total_used"),
            pl.col("pob_male_used").first().alias("pob_male_used"),
            pl.col("pob_female_used").first().alias("pob_female_used"),
        )
        .with_columns(
            (pl.col("n_total") / pl.col("pob_total_used") * RATE_SCALE).alias("rate_total"),
            (pl.col("n_male") / pl.col("pob_male_used") * RATE_SCALE).alias("rate_male"),
            (pl.col("n_female") / pl.col("pob_female_used") * RATE_SCALE).alias("rate_female"),
            pl.when((pl.col("n_female") + pl.col("n_male")) > 0)
              .then(pl.col("n_female") / (pl.col("n_female") + pl.col("n_male")))
              .otherwise(None)
              .alias("fsos"),
        )
        .select([
            "year", "band_2020", "status",
            "n_total", "n_male", "n_female", "n_undefined",
            "pob_total_used", "pob_male_used", "pob_female_used",
            "rate_total", "rate_male", "rate_female", "fsos",
        ])
        .sort(["status", "band_2020", "year"])
    )
    if annual_nat.height != EXPECTED_ANNUAL_NAT_ROWS:
        raise ValueError(
            f"annual_national: expected {EXPECTED_ANNUAL_NAT_ROWS} rows, "
            f"got {annual_nat.height}"
        )
    annual_nat.write_parquet(ANNUAL_NAT_OUT)

    annual_reg = (
        monthly_reg.group_by(["region", "year", "band_2020", "status"])
        .agg(
            pl.col("n_total").sum(),
            pl.col("n_male").sum(),
            pl.col("n_female").sum(),
            pl.col("n_undefined").sum(),
            pl.col("pob_total_used").first().alias("pob_total_used"),
            pl.col("pob_male_used").first().alias("pob_male_used"),
            pl.col("pob_female_used").first().alias("pob_female_used"),
            pl.col("n_munis_in_region_band").first(),
            pl.col("small_denom_flag").first(),
        )
        .with_columns(
            (pl.col("n_total") / pl.col("pob_total_used") * RATE_SCALE).alias("rate_total"),
            (pl.col("n_male") / pl.col("pob_male_used") * RATE_SCALE).alias("rate_male"),
            (pl.col("n_female") / pl.col("pob_female_used") * RATE_SCALE).alias("rate_female"),
            pl.when((pl.col("n_female") + pl.col("n_male")) > 0)
              .then(pl.col("n_female") / (pl.col("n_female") + pl.col("n_male")))
              .otherwise(None)
              .alias("fsos"),
        )
        .select([
            "region", "year", "band_2020", "status",
            "n_total", "n_male", "n_female", "n_undefined",
            "pob_total_used", "pob_male_used", "pob_female_used",
            "rate_total", "rate_male", "rate_female", "fsos",
            "n_munis_in_region_band", "small_denom_flag",
        ])
        .sort(["region", "status", "band_2020", "year"])
    )
    annual_reg.write_parquet(ANNUAL_REG_OUT)

    # =====================================================================
    # LOG
    # =====================================================================
    log("=" * 72)
    log("[23] band_rates - monthly and annual band rates, QA log")
    log("=" * 72)

    log("")
    log("(a) row-count assertions")
    log(f"    monthly_national: {monthly_nat.height:,} "
        f"(expected {EXPECTED_MONTHLY_NAT_ROWS:,})")
    log(f"    monthly_regional: {monthly_reg.height:,}")
    log(f"    annual_national:  {annual_nat.height:,} "
        f"(expected {EXPECTED_ANNUAL_NAT_ROWS:,})")
    log(f"    annual_regional:  {annual_reg.height:,}")
    log(f"    CONAPO ref-year step: year<=2018->2015; "
        "2019<=year<=2024->2020; year==2025->2025.")
    log(f"    RATE_SCALE = {RATE_SCALE:,} (rates per 100k population)")

    # (b) large_city + medium_city + city annual rates per status x year
    log("")
    log("(b) national annual rates for medium_city / city / large_city "
        "(rate per 100k), per status, 2015 / 2020 / 2025")
    qa_years = [2015, 2020, 2025]
    qa_bands = ["medium_city", "city", "large_city"]
    qa = (
        annual_nat.filter(
            pl.col("band_2020").is_in(qa_bands)
            & pl.col("year").is_in(qa_years)
        )
        .select([
            "status", "year", "band_2020",
            "n_total", "pob_total_used", "rate_total", "fsos",
        ])
        .sort(["status", "band_2020", "year"])
    )
    with pl.Config(
        tbl_rows=40, tbl_cols=-1, float_precision=4,
        fmt_str_lengths=30, tbl_hide_dataframe_shape=True,
        tbl_width_chars=400,
    ):
        log(str(qa))

    # (c) sex-count sanity check
    bad = monthly_nat.filter(
        (pl.col("n_male") + pl.col("n_female") + pl.col("n_undefined"))
        != pl.col("n_total")
    )
    log("")
    log("(c) sex-count sanity: n_male + n_female + n_undefined == n_total")
    if bad.height == 0:
        log(f"    PASS (0 mismatched rows out of {monthly_nat.height:,})")
    else:
        log(f"    FAIL ({bad.height:,} mismatched rows)")
        log(str(bad.head(10)))

    # (d) small-denominator cells
    small = (
        n_munis_rb.filter(pl.col("n_munis_in_region_band") < SMALL_DENOM_N_MUNIS)
        .sort(["region", "band_2020"])
    )
    log("")
    log(f"(d) (region, band) cells with n_munis < {SMALL_DENOM_N_MUNIS} "
        "— reviewer-proofing list")
    if small.height == 0:
        log("    none")
    else:
        with pl.Config(
            tbl_rows=40, tbl_cols=-1,
            fmt_str_lengths=30, tbl_hide_dataframe_shape=True,
        ):
            log(str(small))

    # (e) top-10 monthly (band, status) rate_total
    top10 = (
        monthly_nat.filter(pl.col("rate_total").is_not_null())
        .sort("rate_total", descending=True)
        .head(10)
        .select([
            "year", "month", "band_2020", "status",
            "n_total", "pob_total_used", "rate_total",
        ])
    )
    log("")
    log("(e) top-10 monthly national (band, status) cells by rate_total")
    with pl.Config(
        tbl_rows=20, tbl_cols=-1, float_precision=4,
        fmt_str_lengths=30, tbl_hide_dataframe_shape=True,
        tbl_width_chars=400,
    ):
        log(str(top10))

    REPORTS_ALPHA.mkdir(parents=True, exist_ok=True)
    LOG_OUT.write_text("\n".join(log_lines) + "\n", encoding="utf-8")
    print("\n".join(log_lines))

    small_n = small.height
    print("")
    print(
        f"[23] done. monthly_national={monthly_nat.height}, "
        f"monthly_regional={monthly_reg.height}, "
        f"annual_national={annual_nat.height}, "
        f"annual_regional={annual_reg.height}. "
        f"small_denom_cells={small_n}. Awaiting review."
    )


if __name__ == "__main__":
    try:
        main()
    except Exception:
        traceback.print_exc()
        sys.exit(1)
