"""RQ3 band composition chi-squared tests - Paper alpha.

Inputs
------
- data/interim/alpha/alpha_cross_sections.parquet
- data/interim/alpha/band_denom.parquet

Outputs
-------
- data/interim/alpha/rq3_band_counts_national.parquet
- data/interim/alpha/rq3_band_counts_regional.parquet
- data/interim/alpha/rq3_chi2_national.parquet
- data/interim/alpha/rq3_rate_ratios_national.parquet
- data/interim/alpha/rq3_contingency_regional.parquet
- reports/alpha/22_band_composition_chi2.log
"""
from __future__ import annotations

import math
import sys
import traceback
from pathlib import Path

import numpy as np
import polars as pl

# Allow `python scripts_alpha/00_build_alpha_panel.py` to resolve the
# sibling package import (filenames starting with a digit block `-m`).
_REPO = Path(__file__).resolve().parents[1]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from scripts_alpha._utils import (  # noqa: E402
    BAND_ORDER,
    CESOP_REGION_BY_CVE_ENT,
    CESOP_REGIONS,
    CROSS_SECTION_YEARS,
    FFH_MIN_EXPECTED,
    RQ3_PRIMARY_YEAR_PAIR,
    RQ3_YEAR_PAIRS,
    STATUS_ORDER,
)

from scipy import stats as spstats  # noqa: E402
from statsmodels.stats.multitest import multipletests  # noqa: E402

REPO = Path(__file__).resolve().parents[1]
INTERIM_ALPHA = REPO / "data" / "interim" / "alpha"
REPORTS_ALPHA = REPO / "reports" / "alpha"

XS_IN = INTERIM_ALPHA / "alpha_cross_sections.parquet"
DENOM_IN = INTERIM_ALPHA / "band_denom.parquet"
NATIONAL_COUNTS_OUT = INTERIM_ALPHA / "rq3_band_counts_national.parquet"
REGIONAL_COUNTS_OUT = INTERIM_ALPHA / "rq3_band_counts_regional.parquet"
CHI2_OUT = INTERIM_ALPHA / "rq3_chi2_national.parquet"
RATE_RATIO_OUT = INTERIM_ALPHA / "rq3_rate_ratios_national.parquet"
CONTINGENCY_REGIONAL_OUT = INTERIM_ALPHA / "rq3_contingency_regional.parquet"
LOG_OUT = REPORTS_ALPHA / "22_band_composition_chi2.log"

EXPECTED_XS_ROWS = 5_737
MC_SEED = 20_260_423
MC_N_RESAMPLES = 9_999


def interpret_cramer_v(v: float) -> str:
    if math.isnan(v):
        return "n/a"
    if v < 0.10:
        return "negligible"
    if v < 0.30:
        return "small"
    if v < 0.50:
        return "medium"
    return "large"


def stars(p: float) -> str:
    if p < 0.001:
        return "***"
    if p < 0.01:
        return "**"
    if p < 0.05:
        return "*"
    return ""


def main() -> None:
    log_lines: list[str] = []

    def log(msg: str = "") -> None:
        log_lines.append(msg)

    # --- load + enrich cross-sections -----------------------------------
    xs = pl.read_parquet(XS_IN)
    if xs.height != EXPECTED_XS_ROWS:
        raise ValueError(
            f"{XS_IN.name}: expected {EXPECTED_XS_ROWS:,} rows, got {xs.height:,}"
        )

    region_lookup = pl.DataFrame(
        {"cve_ent": list(CESOP_REGION_BY_CVE_ENT.keys()),
         "region": list(CESOP_REGION_BY_CVE_ENT.values())},
        schema={"cve_ent": pl.Int64, "region": pl.Utf8},
    )

    xs = (
        xs.with_columns(
            pl.col("cve_geo").str.slice(0, 2).cast(pl.Int64).alias("cve_ent")
        )
        .join(region_lookup, on="cve_ent", how="left")
    )
    if xs.filter(pl.col("region").is_null()).height:
        raise ValueError("unmapped cve_ent encountered after region join")

    # band_2020 is an Enum - cast to Utf8 for portable grouping / joining.
    xs = xs.with_columns(pl.col("band_2020").cast(pl.Utf8))

    # --- band_denom: per-band population per year -----------------------
    denom = pl.read_parquet(DENOM_IN).with_columns(
        pl.col("band_2020").cast(pl.Utf8)
    )

    band_pop_wide = (
        denom.group_by("band_2020")
        .agg(
            pl.col("pob_2015").sum(),
            pl.col("pob_2019").sum(),
            pl.col("pob_2025").sum(),
        )
    )
    band_pop_long = (
        band_pop_wide.unpivot(
            index="band_2020",
            on=["pob_2015", "pob_2019", "pob_2025"],
            variable_name="year_col",
            value_name="band_population",
        )
        .with_columns(
            pl.col("year_col").str.replace("pob_", "").cast(pl.Int64).alias("year")
        )
        .select(["band_2020", "year", "band_population"])
    )

    # --- (2) national band x year x status counts -----------------------
    grid_nat = (
        pl.DataFrame({"band_2020": BAND_ORDER})
        .join(pl.DataFrame({"year": CROSS_SECTION_YEARS},
                           schema={"year": pl.Int64}),
              how="cross")
        .join(pl.DataFrame({"status": STATUS_ORDER}), how="cross")
    )
    nat_agg = (
        xs.group_by(["band_2020", "year", "status"])
        .agg(pl.col("total").sum().alias("n_cases"))
        .with_columns(pl.col("year").cast(pl.Int64))
    )
    national = (
        grid_nat.join(
            nat_agg, on=["band_2020", "year", "status"], how="left"
        )
        .with_columns(pl.col("n_cases").fill_null(0))
        .join(band_pop_long, on=["band_2020", "year"], how="left")
        .select(["band_2020", "year", "status", "n_cases", "band_population"])
        .sort(["status", "year", "band_2020"])
    )
    expected_national_rows = (
        len(BAND_ORDER) * len(CROSS_SECTION_YEARS) * len(STATUS_ORDER)
    )
    if national.height != expected_national_rows:
        raise ValueError(
            f"national counts: expected {expected_national_rows} rows, "
            f"got {national.height}"
        )
    national.write_parquet(NATIONAL_COUNTS_OUT)

    # --- (3) regional band x year x status counts -----------------------
    denom_reg = (
        denom.with_columns(
            pl.col("cve_geo").str.slice(0, 2).cast(pl.Int64).alias("cve_ent")
        )
        .join(region_lookup, on="cve_ent", how="left")
    )
    if denom_reg.filter(pl.col("region").is_null()).height:
        raise ValueError("unmapped cve_ent in band_denom")

    reg_pop_wide = (
        denom_reg.group_by(["region", "band_2020"])
        .agg(
            pl.col("pob_2015").sum(),
            pl.col("pob_2019").sum(),
            pl.col("pob_2025").sum(),
        )
    )
    reg_pop_long = (
        reg_pop_wide.unpivot(
            index=["region", "band_2020"],
            on=["pob_2015", "pob_2019", "pob_2025"],
            variable_name="year_col",
            value_name="band_population",
        )
        .with_columns(
            pl.col("year_col").str.replace("pob_", "").cast(pl.Int64).alias("year")
        )
        .select(["region", "band_2020", "year", "band_population"])
    )

    grid_reg = (
        pl.DataFrame({"region": CESOP_REGIONS})
        .join(pl.DataFrame({"band_2020": BAND_ORDER}), how="cross")
        .join(pl.DataFrame({"year": CROSS_SECTION_YEARS},
                           schema={"year": pl.Int64}), how="cross")
        .join(pl.DataFrame({"status": STATUS_ORDER}), how="cross")
    )
    reg_agg = (
        xs.group_by(["region", "band_2020", "year", "status"])
        .agg(pl.col("total").sum().alias("n_cases"))
        .with_columns(pl.col("year").cast(pl.Int64))
    )
    regional = (
        grid_reg.join(
            reg_agg, on=["region", "band_2020", "year", "status"], how="left"
        )
        .with_columns(pl.col("n_cases").fill_null(0))
        .join(reg_pop_long,
              on=["region", "band_2020", "year"], how="left")
        .with_columns(pl.col("band_population").fill_null(0))
        .select(["region", "band_2020", "year", "status",
                 "n_cases", "band_population"])
        .sort(["region", "status", "year", "band_2020"])
    )
    regional.write_parquet(REGIONAL_COUNTS_OUT)

    # --- (4) national chi-squared tests ---------------------------------
    nat_test_rows: list[dict] = []
    for status in STATUS_ORDER:
        status_rows: list[dict] = []
        for (ya, yb) in RQ3_YEAR_PAIRS:
            sub = (
                national.filter(
                    (pl.col("status") == status)
                    & pl.col("year").is_in([ya, yb])
                )
                .sort(["band_2020", "year"])
            )
            tbl = np.zeros((len(BAND_ORDER), 2), dtype=np.int64)
            col_idx = {ya: 0, yb: 1}
            band_idx = {b: i for i, b in enumerate(BAND_ORDER)}
            for row in sub.iter_rows(named=True):
                tbl[band_idx[row["band_2020"]], col_idx[row["year"]]] = row["n_cases"]

            col_totals = tbl.sum(axis=0)
            row_totals = tbl.sum(axis=1)
            grand = int(tbl.sum())
            if grand > 0:
                expected = (
                    row_totals[:, None].astype(float)
                    * col_totals[None, :].astype(float) / grand
                )
            else:
                expected = np.zeros_like(tbl, dtype=float)
            min_expected = float(expected.min())

            if min_expected >= FFH_MIN_EXPECTED:
                res = spstats.chi2_contingency(tbl, correction=False)
                chi2 = float(res.statistic)
                p_raw = float(res.pvalue)
                dof = float(res.dof)
                test_used = "chi2"
            else:
                res = spstats.chi2_contingency(
                    tbl,
                    correction=False,
                    method=spstats.MonteCarloMethod(
                        n_resamples=MC_N_RESAMPLES, rng=MC_SEED,
                    ),
                )
                chi2 = float(res.statistic)
                p_raw = float(res.pvalue)
                dof = float("nan")
                test_used = "chi2_mc"

            V = math.sqrt(chi2 / grand) if grand > 0 else float("nan")
            status_rows.append({
                "scope": "national",
                "region": None,
                "year_a": ya, "year_b": yb,
                "status": status,
                "n_a": int(col_totals[0]),
                "n_b": int(col_totals[1]),
                "grand_total": grand,
                "dof": dof,
                "chi2": chi2,
                "p_raw": p_raw,
                "test_used": test_used,
                "min_expected": min_expected,
                "cramer_v": V,
                "cramer_v_interp": interpret_cramer_v(V),
                "_tbl": tbl,
                "_expected": expected,
            })

        holm = multipletests([r["p_raw"] for r in status_rows],
                             method="holm")[1]
        for r, ph in zip(status_rows, holm):
            r["p_holm"] = float(ph)
        nat_test_rows.extend(status_rows)

    chi2_cols = [
        "scope", "region", "year_a", "year_b", "status",
        "n_a", "n_b", "grand_total",
        "dof", "chi2", "p_raw", "p_holm",
        "test_used", "min_expected",
        "cramer_v", "cramer_v_interp",
    ]
    chi2_df = pl.DataFrame(
        [{k: r[k] for k in chi2_cols} for r in nat_test_rows],
        schema={
            "scope": pl.Utf8, "region": pl.Utf8,
            "year_a": pl.Int64, "year_b": pl.Int64, "status": pl.Utf8,
            "n_a": pl.Int64, "n_b": pl.Int64, "grand_total": pl.Int64,
            "dof": pl.Float64, "chi2": pl.Float64,
            "p_raw": pl.Float64, "p_holm": pl.Float64,
            "test_used": pl.Utf8, "min_expected": pl.Float64,
            "cramer_v": pl.Float64, "cramer_v_interp": pl.Utf8,
        },
    )
    chi2_df.write_parquet(CHI2_OUT)

    # --- (5) rate-ratio computations ------------------------------------
    rr_rows: list[dict] = []
    for (ya, yb) in RQ3_YEAR_PAIRS:
        for status in STATUS_ORDER:
            for band in BAND_ORDER:
                r_a = national.filter(
                    (pl.col("status") == status)
                    & (pl.col("year") == ya)
                    & (pl.col("band_2020") == band)
                ).row(0, named=True)
                r_b = national.filter(
                    (pl.col("status") == status)
                    & (pl.col("year") == yb)
                    & (pl.col("band_2020") == band)
                ).row(0, named=True)
                n_a = int(r_a["n_cases"])
                n_b = int(r_b["n_cases"])
                pop_a = int(r_a["band_population"])
                pop_b = int(r_b["band_population"])
                rate_a = n_a / pop_a if pop_a > 0 else float("nan")
                rate_b = n_b / pop_b if pop_b > 0 else float("nan")
                if n_a == 0 or n_b == 0 or pop_a == 0 or pop_b == 0:
                    rr = ci_lo = ci_hi = float("nan")
                    defined = False
                else:
                    rr = rate_b / rate_a
                    se = math.sqrt(1.0 / n_a + 1.0 / n_b)
                    ci_lo = math.exp(math.log(rr) - 1.96 * se)
                    ci_hi = math.exp(math.log(rr) + 1.96 * se)
                    defined = True
                rr_rows.append({
                    "year_a": ya, "year_b": yb, "status": status,
                    "band_2020": band,
                    "n_a": n_a, "n_b": n_b,
                    "pop_a": pop_a, "pop_b": pop_b,
                    "rate_a": rate_a, "rate_b": rate_b,
                    "rate_ratio": rr, "ci_lo": ci_lo, "ci_hi": ci_hi,
                    "rate_ratio_defined": defined,
                })
    rr_df = pl.DataFrame(rr_rows).select([
        "year_a", "year_b", "status", "band_2020",
        "n_a", "n_b", "pop_a", "pop_b",
        "rate_a", "rate_b", "rate_ratio", "ci_lo", "ci_hi",
        "rate_ratio_defined",
    ])
    rr_df.write_parquet(RATE_RATIO_OUT)

    # --- (6) regional contingency tables (staged, not tested) -----------
    cont_rows: list[dict] = []
    for region in CESOP_REGIONS:
        for (ya, yb) in RQ3_YEAR_PAIRS:
            for status in STATUS_ORDER:
                for band in BAND_ORDER:
                    r_a = regional.filter(
                        (pl.col("region") == region)
                        & (pl.col("status") == status)
                        & (pl.col("year") == ya)
                        & (pl.col("band_2020") == band)
                    ).row(0, named=True)
                    r_b = regional.filter(
                        (pl.col("region") == region)
                        & (pl.col("status") == status)
                        & (pl.col("year") == yb)
                        & (pl.col("band_2020") == band)
                    ).row(0, named=True)
                    cont_rows.append({
                        "region": region,
                        "year_a": ya, "year_b": yb, "status": status,
                        "band_2020": band,
                        "n_a": int(r_a["n_cases"]),
                        "n_b": int(r_b["n_cases"]),
                    })
    cont_df = pl.DataFrame(cont_rows).select([
        "region", "year_a", "year_b", "status", "band_2020", "n_a", "n_b",
    ])
    cont_df.write_parquet(CONTINGENCY_REGIONAL_OUT)

    # =====================================================================
    # LOG
    # =====================================================================
    log("=" * 72)
    log("[22] band_composition_chi2 - RQ3 QA log")
    log("=" * 72)

    log("")
    log("(a) thresholds")
    log(f"    FFH_MIN_EXPECTED           = {FFH_MIN_EXPECTED}")
    log(f"    RQ3_YEAR_PAIRS             = {RQ3_YEAR_PAIRS}")
    log(f"    RQ3_PRIMARY_YEAR_PAIR      = {RQ3_PRIMARY_YEAR_PAIR}")
    log(f"    MC_N_RESAMPLES / MC_SEED   = {MC_N_RESAMPLES} / {MC_SEED}")

    log("")
    log("(b) national band x year x status counts (63 rows)")
    with pl.Config(
        tbl_rows=80, tbl_cols=-1, float_precision=4,
        fmt_str_lengths=30, tbl_hide_dataframe_shape=True,
        tbl_width_chars=400,
    ):
        log(str(
            national.with_columns(
                pl.col("band_2020").cast(pl.Enum(BAND_ORDER))
            ).sort(["status", "year", "band_2020"])
        ))

    log("")
    log("(c) band population totals per year (7 bands x 3 years)")
    pop_table = band_pop_long.pivot(
        index="band_2020", on="year", values="band_population",
        aggregate_function="first",
    ).with_columns(
        pl.col("band_2020").cast(pl.Enum(BAND_ORDER))
    ).sort("band_2020")
    with pl.Config(
        tbl_rows=20, tbl_cols=-1,
        fmt_str_lengths=30, tbl_hide_dataframe_shape=True,
    ):
        log(str(pop_table))

    log("")
    log(f"(d) PRIMARY year pair {RQ3_PRIMARY_YEAR_PAIR} - "
        "per-status 7x2 contingency (observed / expected)")
    for r in nat_test_rows:
        if (r["year_a"], r["year_b"]) != RQ3_PRIMARY_YEAR_PAIR:
            continue
        tbl = r["_tbl"]
        exp = r["_expected"]
        log("")
        log(f"--- status = {r['status']} ---")
        log(
            f"    {'band':<13} "
            f"{'obs_' + str(r['year_a']):>12}  "
            f"{'obs_' + str(r['year_b']):>12}  "
            f"{'exp_' + str(r['year_a']):>12}  "
            f"{'exp_' + str(r['year_b']):>12}"
        )
        for i, band in enumerate(BAND_ORDER):
            log(
                f"    {band:<13} "
                f"{tbl[i, 0]:>12,} "
                f"{tbl[i, 1]:>12,} "
                f"{exp[i, 0]:>12.2f} "
                f"{exp[i, 1]:>12.2f}"
            )
        log(
            f"    min_expected = {r['min_expected']:.3f}; "
            f"test_used = {r['test_used']}"
        )
        dof_str = (f"{int(r['dof'])}"
                   if not math.isnan(r["dof"])
                   else "n/a (MC)")
        log(
            f"    chi2({dof_str}) = {r['chi2']:.3f}, "
            f"p_raw = {r['p_raw']:.4g}, "
            f"p_holm = {r['p_holm']:.4g} {stars(r['p_holm'])}"
        )
        log(
            f"    Cramer's V = {r['cramer_v']:.3f} ({r['cramer_v_interp']}; "
            "Cohen's heuristic, descriptive only)"
        )

    log("")
    log("(e) supplementary year pairs - one-line summaries")
    for r in nat_test_rows:
        if (r["year_a"], r["year_b"]) == RQ3_PRIMARY_YEAR_PAIR:
            continue
        dof_str = (f"{int(r['dof'])}"
                   if not math.isnan(r["dof"])
                   else "mc")
        log(
            f"    {r['status']:13s} {r['year_a']} vs {r['year_b']}: "
            f"n={r['n_a']:>6,}->{r['n_b']:>6,}, "
            f"chi2({dof_str})={r['chi2']:.2f}, "
            f"p_raw={r['p_raw']:.4g}, p_holm={r['p_holm']:.4g} {stars(r['p_holm'])}, "
            f"V={r['cramer_v']:.3f} ({r['cramer_v_interp']}), "
            f"test={r['test_used']}"
        )

    log("")
    log(f"(f) rate ratios for primary pair {RQ3_PRIMARY_YEAR_PAIR} "
        "(21 rows: 7 bands x 3 statuses)")
    for status in STATUS_ORDER:
        log(f"    --- status = {status} ---")
        log(
            f"        {'band':<13} {'rate_a (per 1e6)':>18} "
            f"{'rate_b (per 1e6)':>18} {'RR [95% CI]':>28}"
        )
        for band in BAND_ORDER:
            r = next(
                x for x in rr_rows
                if (x["year_a"] == RQ3_PRIMARY_YEAR_PAIR[0]
                    and x["year_b"] == RQ3_PRIMARY_YEAR_PAIR[1]
                    and x["status"] == status
                    and x["band_2020"] == band)
            )
            ra_1e6 = r["rate_a"] * 1e6 if not math.isnan(r["rate_a"]) else float("nan")
            rb_1e6 = r["rate_b"] * 1e6 if not math.isnan(r["rate_b"]) else float("nan")
            if r["rate_ratio_defined"]:
                rr_str = (
                    f"{r['rate_ratio']:>6.2f} "
                    f"[{r['ci_lo']:.2f}, {r['ci_hi']:.2f}]"
                )
            else:
                rr_str = "undefined"
            log(
                f"        {band:<13} "
                f"{ra_1e6:>18.3f} {rb_1e6:>18.3f} {rr_str:>28}"
            )

    log("")
    log("(g) narrative per status (primary test, 2015 -> 2025)")
    for r in nat_test_rows:
        if (r["year_a"], r["year_b"]) != RQ3_PRIMARY_YEAR_PAIR:
            continue
        tbl = r["_tbl"]
        col_tot = tbl.sum(axis=0)
        share_a = (tbl[:, 0] / col_tot[0]
                   if col_tot[0] > 0 else np.zeros(len(BAND_ORDER)))
        share_b = (tbl[:, 1] / col_tot[1]
                   if col_tot[1] > 0 else np.zeros(len(BAND_ORDER)))
        delta = share_b - share_a
        i_up = int(np.argmax(delta))
        i_dn = int(np.argmin(delta))
        shift = (
            f"share of {BAND_ORDER[i_up]} "
            f"{share_a[i_up]:.1%}->{share_b[i_up]:.1%} "
            f"({delta[i_up]*100:+.1f} pp), "
            f"share of {BAND_ORDER[i_dn]} "
            f"{share_a[i_dn]:.1%}->{share_b[i_dn]:.1%} "
            f"({delta[i_dn]*100:+.1f} pp)"
        )
        dof_str = (f"{int(r['dof'])}"
                   if not math.isnan(r["dof"])
                   else "mc")
        log(
            f"    {r['status']} 2015->2025: "
            f"n={r['n_a']:,}->{r['n_b']:,}, "
            f"chi2({dof_str})={r['chi2']:.2f}, "
            f"p_holm={r['p_holm']:.4g} {stars(r['p_holm'])}, "
            f"V={r['cramer_v']:.3f} ({r['cramer_v_interp']}). "
            f"Band shift: {shift}."
        )

    log("")
    log("(h) regional contingency tables staged (not tested in primary)")
    for region in CESOP_REGIONS:
        n_rows = cont_df.filter(pl.col("region") == region).height
        log(
            f"    regional contingency tables for {region} written to "
            f"parquet - {n_rows} rows, not tested in primary."
        )

    REPORTS_ALPHA.mkdir(parents=True, exist_ok=True)
    LOG_OUT.write_text("\n".join(log_lines) + "\n", encoding="utf-8")

    print("\n".join(log_lines))

    primary_sig = sum(
        1 for r in nat_test_rows
        if (r["year_a"], r["year_b"]) == RQ3_PRIMARY_YEAR_PAIR
        and r["p_holm"] < 0.05
    )
    print("")
    print(
        f"[22] done. 9 national tests (3 year-pairs x 3 statuses). "
        f"Primary significant (Holm, per status): {primary_sig}/3. "
        "Regional contingency tables staged but not tested. Awaiting review."
    )


if __name__ == "__main__":
    try:
        main()
    except Exception:
        traceback.print_exc()
        sys.exit(1)
