"""RQ3 regional + Bajío chi-squared tests - Paper alpha.

Inputs
------
- data/interim/alpha/rq3_contingency_regional.parquet (staged by script 22)
- data/interim/alpha/rq3_band_counts_regional.parquet
- data/interim/alpha/alpha_cross_sections.parquet
- data/interim/alpha/band_denom.parquet
- data/processed/municipality_classification_v2.csv (JQC is_bajio flag)

Outputs
-------
- data/interim/alpha/rq3_chi2_regional.parquet
- data/interim/alpha/rq3_rate_ratios_regional.parquet
- data/interim/alpha/rq3_chi2_bajio.parquet
- data/interim/alpha/rq3_rate_ratios_bajio.parquet
- reports/alpha/22b_band_composition_regional.log
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
    BAJIO_29_CVEGEOS,
    BAND_ORDER,
    CESOP_REGIONS,
    CESOP_REGION_BY_CVE_ENT,
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

CONTINGENCY_IN = INTERIM_ALPHA / "rq3_contingency_regional.parquet"
REG_COUNTS_IN = INTERIM_ALPHA / "rq3_band_counts_regional.parquet"
XS_IN = INTERIM_ALPHA / "alpha_cross_sections.parquet"
DENOM_IN = INTERIM_ALPHA / "band_denom.parquet"
CLASS_V2_IN = REPO / "data" / "processed" / "municipality_classification_v2.csv"

CHI2_REG_OUT = INTERIM_ALPHA / "rq3_chi2_regional.parquet"
RR_REG_OUT = INTERIM_ALPHA / "rq3_rate_ratios_regional.parquet"
CHI2_BAJIO_OUT = INTERIM_ALPHA / "rq3_chi2_bajio.parquet"
RR_BAJIO_OUT = INTERIM_ALPHA / "rq3_rate_ratios_bajio.parquet"
LOG_OUT = REPORTS_ALPHA / "22b_band_composition_regional.log"

MC_SEED_REGIONAL = 20_260_424
MC_SEED_BAJIO = 20_260_425
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
    if math.isnan(p):
        return ""
    if p < 0.001:
        return "***"
    if p < 0.01:
        return "**"
    if p < 0.05:
        return "*"
    return ""


def run_chi2(tbl: np.ndarray, seed: int) -> dict:
    """Apply the bands-with-any-cases filter, run chi2 or MC, return a
    dict of {chi2, p_raw, dof, test_used, min_expected, cramer_v,
    cramer_v_interp, n_bands_dropped}."""
    row_sums = tbl.sum(axis=1)
    keep = row_sums > 0
    n_bands_dropped = int((~keep).sum())
    tbl_eff = tbl[keep]
    r_eff = tbl_eff.shape[0]
    grand = int(tbl_eff.sum())

    if r_eff < 2 or grand == 0:
        return {
            "chi2": float("nan"), "p_raw": float("nan"),
            "dof": float("nan"), "test_used": "n/a",
            "min_expected": float("nan"),
            "cramer_v": float("nan"),
            "cramer_v_interp": "n/a",
            "n_bands_dropped": n_bands_dropped,
        }

    col_totals = tbl_eff.sum(axis=0)
    row_totals = tbl_eff.sum(axis=1)
    expected = (
        row_totals[:, None].astype(float)
        * col_totals[None, :].astype(float) / grand
    )
    min_expected = float(expected.min())

    if min_expected >= FFH_MIN_EXPECTED:
        res = spstats.chi2_contingency(tbl_eff, correction=False)
        chi2 = float(res.statistic)
        p_raw = float(res.pvalue)
        dof = float(res.dof)
        test_used = "chi2"
    else:
        res = spstats.chi2_contingency(
            tbl_eff,
            correction=False,
            method=spstats.MonteCarloMethod(
                n_resamples=MC_N_RESAMPLES, rng=seed,
            ),
        )
        chi2 = float(res.statistic)
        p_raw = float(res.pvalue)
        dof = float("nan")
        test_used = "chi2_mc"

    v_den = grand * min(r_eff - 1, 1)
    V = math.sqrt(chi2 / v_den) if v_den > 0 else float("nan")

    return {
        "chi2": chi2, "p_raw": p_raw, "dof": dof,
        "test_used": test_used, "min_expected": min_expected,
        "cramer_v": V, "cramer_v_interp": interpret_cramer_v(V),
        "n_bands_dropped": n_bands_dropped,
    }


def rate_ratio(n_a: int, n_b: int, pop_a: int, pop_b: int) -> dict:
    rate_a = n_a / pop_a if pop_a > 0 else float("nan")
    rate_b = n_b / pop_b if pop_b > 0 else float("nan")
    if n_a == 0 or n_b == 0 or pop_a == 0 or pop_b == 0:
        return {"rate_a": rate_a, "rate_b": rate_b,
                "rate_ratio": float("nan"),
                "ci_lo": float("nan"), "ci_hi": float("nan"),
                "rate_ratio_defined": False}
    rr = rate_b / rate_a
    se = math.sqrt(1.0 / n_a + 1.0 / n_b)
    return {"rate_a": rate_a, "rate_b": rate_b,
            "rate_ratio": rr,
            "ci_lo": math.exp(math.log(rr) - 1.96 * se),
            "ci_hi": math.exp(math.log(rr) + 1.96 * se),
            "rate_ratio_defined": True}


def main() -> None:
    log_lines: list[str] = []

    def log(msg: str = "") -> None:
        log_lines.append(msg)

    # --- (1) load -------------------------------------------------------
    cont = pl.read_parquet(CONTINGENCY_IN)
    if cont.height != len(CESOP_REGIONS) * len(RQ3_YEAR_PAIRS) * len(STATUS_ORDER) * len(BAND_ORDER):
        raise ValueError(
            f"{CONTINGENCY_IN.name}: expected 315 rows, got {cont.height}"
        )
    reg_counts = pl.read_parquet(REG_COUNTS_IN)

    # --- (2) regional chi-squared tests ---------------------------------
    band_idx = {b: i for i, b in enumerate(BAND_ORDER)}
    reg_test_rows: list[dict] = []
    reg_extras: dict[tuple, dict] = {}

    for region in CESOP_REGIONS:
        for status in STATUS_ORDER:
            status_rows: list[dict] = []
            for (ya, yb) in RQ3_YEAR_PAIRS:
                sub = cont.filter(
                    (pl.col("region") == region)
                    & (pl.col("status") == status)
                    & (pl.col("year_a") == ya)
                    & (pl.col("year_b") == yb)
                )
                tbl = np.zeros((len(BAND_ORDER), 2), dtype=np.int64)
                for row in sub.iter_rows(named=True):
                    i = band_idx[row["band_2020"]]
                    tbl[i, 0] = row["n_a"]
                    tbl[i, 1] = row["n_b"]

                out = run_chi2(tbl, seed=MC_SEED_REGIONAL)
                col_tot = tbl.sum(axis=0)
                rec = {
                    "region": region,
                    "year_a": ya, "year_b": yb,
                    "status": status,
                    "n_a": int(col_tot[0]),
                    "n_b": int(col_tot[1]),
                    "grand_total": int(tbl.sum()),
                    **out,
                }
                status_rows.append(rec)
                reg_extras[(region, status, ya, yb)] = {"tbl": tbl}

            p_raws = [r["p_raw"] for r in status_rows]
            if any(math.isnan(p) for p in p_raws):
                holm = [float("nan")] * len(p_raws)
            else:
                holm = multipletests(p_raws, method="holm")[1]
            for r, ph in zip(status_rows, holm):
                r["p_holm"] = float(ph)
            reg_test_rows.extend(status_rows)

    reg_cols = [
        "region", "year_a", "year_b", "status",
        "n_a", "n_b", "grand_total",
        "dof", "chi2", "p_raw", "p_holm",
        "test_used", "min_expected",
        "cramer_v", "cramer_v_interp", "n_bands_dropped",
    ]
    reg_chi2 = pl.DataFrame(
        [{k: r[k] for k in reg_cols} for r in reg_test_rows],
        schema={
            "region": pl.Utf8,
            "year_a": pl.Int64, "year_b": pl.Int64, "status": pl.Utf8,
            "n_a": pl.Int64, "n_b": pl.Int64, "grand_total": pl.Int64,
            "dof": pl.Float64, "chi2": pl.Float64,
            "p_raw": pl.Float64, "p_holm": pl.Float64,
            "test_used": pl.Utf8, "min_expected": pl.Float64,
            "cramer_v": pl.Float64, "cramer_v_interp": pl.Utf8,
            "n_bands_dropped": pl.Int64,
        },
    )
    reg_chi2.write_parquet(CHI2_REG_OUT)

    # --- (3) regional rate-ratios ---------------------------------------
    rr_reg_rows: list[dict] = []
    for region in CESOP_REGIONS:
        for (ya, yb) in RQ3_YEAR_PAIRS:
            for status in STATUS_ORDER:
                for band in BAND_ORDER:
                    r_a = reg_counts.filter(
                        (pl.col("region") == region)
                        & (pl.col("status") == status)
                        & (pl.col("year") == ya)
                        & (pl.col("band_2020") == band)
                    ).row(0, named=True)
                    r_b = reg_counts.filter(
                        (pl.col("region") == region)
                        & (pl.col("status") == status)
                        & (pl.col("year") == yb)
                        & (pl.col("band_2020") == band)
                    ).row(0, named=True)
                    n_a = int(r_a["n_cases"])
                    n_b = int(r_b["n_cases"])
                    pop_a = int(r_a["band_population"])
                    pop_b = int(r_b["band_population"])
                    rr = rate_ratio(n_a, n_b, pop_a, pop_b)
                    rr_reg_rows.append({
                        "region": region,
                        "year_a": ya, "year_b": yb, "status": status,
                        "band_2020": band,
                        "n_a": n_a, "n_b": n_b,
                        "pop_a": pop_a, "pop_b": pop_b,
                        **rr,
                    })
    rr_reg_df = pl.DataFrame(rr_reg_rows).select([
        "region", "year_a", "year_b", "status", "band_2020",
        "n_a", "n_b", "pop_a", "pop_b",
        "rate_a", "rate_b", "rate_ratio", "ci_lo", "ci_hi",
        "rate_ratio_defined",
    ])
    rr_reg_df.write_parquet(RR_REG_OUT)

    # --- (4) Bajio sub-analyses: 29-muni SUN (primary) + 200-muni broad ---
    xs_full = pl.read_parquet(XS_IN).with_columns(
        pl.col("band_2020").cast(pl.Utf8)
    )
    denom_full = pl.read_parquet(DENOM_IN).with_columns(
        pl.col("band_2020").cast(pl.Utf8)
    )
    bajio_csv_v2 = pl.read_csv(
        CLASS_V2_IN, schema_overrides={"cvegeo": pl.Utf8}
    ).with_columns(pl.col("cvegeo").str.zfill(5))
    bajio_200_cvegeos = (
        bajio_csv_v2.filter(pl.col("is_bajio"))
        .get_column("cvegeo")
        .to_list()
    )

    def compute_bajio(muni_set: list[str]) -> dict:
        b_xs = xs_full.filter(pl.col("cve_geo").is_in(muni_set))
        b_denom = denom_full.filter(pl.col("cve_geo").is_in(muni_set))
        pop_wide = (
            b_denom.group_by("band_2020").agg(
                pl.col("pob_2015").sum(),
                pl.col("pob_2019").sum(),
                pl.col("pob_2025").sum(),
            )
        )
        pop_long = (
            pop_wide.unpivot(
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
        grid = (
            pl.DataFrame({"band_2020": BAND_ORDER})
            .join(pl.DataFrame({"year": CROSS_SECTION_YEARS},
                               schema={"year": pl.Int64}), how="cross")
            .join(pl.DataFrame({"status": STATUS_ORDER}), how="cross")
        )
        agg = (
            b_xs.group_by(["band_2020", "year", "status"])
            .agg(pl.col("total").sum().alias("n_cases"))
            .with_columns(pl.col("year").cast(pl.Int64))
        )
        counts = (
            grid.join(agg, on=["band_2020", "year", "status"], how="left")
            .with_columns(pl.col("n_cases").fill_null(0))
            .join(pop_long, on=["band_2020", "year"], how="left")
            .with_columns(pl.col("band_population").fill_null(0))
            .select(["band_2020", "year", "status", "n_cases", "band_population"])
            .sort(["status", "year", "band_2020"])
        )

        test_rows: list[dict] = []
        extras: dict = {}
        for status in STATUS_ORDER:
            status_rows: list[dict] = []
            for (ya, yb) in RQ3_YEAR_PAIRS:
                sub = counts.filter(
                    (pl.col("status") == status)
                    & pl.col("year").is_in([ya, yb])
                )
                tbl = np.zeros((len(BAND_ORDER), 2), dtype=np.int64)
                col_idx = {ya: 0, yb: 1}
                for row in sub.iter_rows(named=True):
                    tbl[band_idx[row["band_2020"]], col_idx[row["year"]]] = row["n_cases"]
                out = run_chi2(tbl, seed=MC_SEED_BAJIO)
                col_tot = tbl.sum(axis=0)
                rec = {
                    "scope": "bajio",
                    "year_a": ya, "year_b": yb,
                    "status": status,
                    "n_a": int(col_tot[0]),
                    "n_b": int(col_tot[1]),
                    "grand_total": int(tbl.sum()),
                    **out,
                }
                status_rows.append(rec)
                extras[(status, ya, yb)] = {"tbl": tbl}
            p_raws = [r["p_raw"] for r in status_rows]
            if any(math.isnan(p) for p in p_raws):
                holm = [float("nan")] * len(p_raws)
            else:
                holm = multipletests(p_raws, method="holm")[1]
            for r, ph in zip(status_rows, holm):
                r["p_holm"] = float(ph)
            test_rows.extend(status_rows)

        rr_rows: list[dict] = []
        for (ya, yb) in RQ3_YEAR_PAIRS:
            for status in STATUS_ORDER:
                for band in BAND_ORDER:
                    r_a = counts.filter(
                        (pl.col("status") == status)
                        & (pl.col("year") == ya)
                        & (pl.col("band_2020") == band)
                    ).row(0, named=True)
                    r_b = counts.filter(
                        (pl.col("status") == status)
                        & (pl.col("year") == yb)
                        & (pl.col("band_2020") == band)
                    ).row(0, named=True)
                    n_a = int(r_a["n_cases"])
                    n_b = int(r_b["n_cases"])
                    pop_a = int(r_a["band_population"])
                    pop_b = int(r_b["band_population"])
                    rr = rate_ratio(n_a, n_b, pop_a, pop_b)
                    rr_rows.append({
                        "year_a": ya, "year_b": yb, "status": status,
                        "band_2020": band,
                        "n_a": n_a, "n_b": n_b,
                        "pop_a": pop_a, "pop_b": pop_b,
                        **rr,
                    })

        return {
            "n_munis": len(muni_set),
            "counts": counts,
            "test_rows": test_rows,
            "extras": extras,
            "rr_rows": rr_rows,
        }

    bajio_29 = compute_bajio(list(BAJIO_29_CVEGEOS))
    bajio_200 = compute_bajio(bajio_200_cvegeos)

    # Primary = 29-muni SUN-based definition. Parquet overwrites reflect this.
    bajio_counts = bajio_29["counts"]
    bajio_test_rows = bajio_29["test_rows"]
    bajio_extras = bajio_29["extras"]
    rr_bajio_rows = bajio_29["rr_rows"]
    n_bajio = bajio_29["n_munis"]

    bajio_cols = [
        "scope", "year_a", "year_b", "status",
        "n_a", "n_b", "grand_total",
        "dof", "chi2", "p_raw", "p_holm",
        "test_used", "min_expected",
        "cramer_v", "cramer_v_interp", "n_bands_dropped",
    ]
    bajio_chi2 = pl.DataFrame(
        [{k: r[k] for k in bajio_cols} for r in bajio_test_rows],
        schema={
            "scope": pl.Utf8,
            "year_a": pl.Int64, "year_b": pl.Int64, "status": pl.Utf8,
            "n_a": pl.Int64, "n_b": pl.Int64, "grand_total": pl.Int64,
            "dof": pl.Float64, "chi2": pl.Float64,
            "p_raw": pl.Float64, "p_holm": pl.Float64,
            "test_used": pl.Utf8, "min_expected": pl.Float64,
            "cramer_v": pl.Float64, "cramer_v_interp": pl.Utf8,
            "n_bands_dropped": pl.Int64,
        },
    )
    bajio_chi2.write_parquet(CHI2_BAJIO_OUT)
    rr_bajio_df = pl.DataFrame(rr_bajio_rows).select([
        "year_a", "year_b", "status", "band_2020",
        "n_a", "n_b", "pop_a", "pop_b",
        "rate_a", "rate_b", "rate_ratio", "ci_lo", "ci_hi",
        "rate_ratio_defined",
    ])
    rr_bajio_df.write_parquet(RR_BAJIO_OUT)

    # =====================================================================
    # LOG
    # =====================================================================
    log("=" * 72)
    log("[22b] band_composition_regional - RQ3 regional + Bajio QA log")
    log("=" * 72)

    # --- (a) test counts ------------------------------------------------
    log("")
    log("(a) test counts")
    log(
        f"    45 regional (5 regions x 3 year-pairs x 3 statuses) + "
        f"9 Bajio (3 x 3) = 54 tests"
    )
    log(f"    Bajio primary subset: 29-muni SUN-based list (Medina-Fernandez et al. 2023) "
        f"— n={bajio_29['n_munis']} (expected 29)")
    log(f"    Bajio comparison subset: is_bajio==True in municipality_classification_v2.csv "
        f"— n={bajio_200['n_munis']}")
    log(f"    MC seeds: regional={MC_SEED_REGIONAL}, bajio={MC_SEED_BAJIO}")

    # --- (b) regional contingency tables (primary pair only) -----------
    log("")
    log(f"(b) regional contingency tables (primary pair "
        f"{RQ3_PRIMARY_YEAR_PAIR})")
    for region in CESOP_REGIONS:
        for status in STATUS_ORDER:
            tbl = reg_extras[(region, status,
                              RQ3_PRIMARY_YEAR_PAIR[0],
                              RQ3_PRIMARY_YEAR_PAIR[1])]["tbl"]
            log("")
            log(f"--- region = {region} | status = {status} ---")
            log(
                f"    {'band':<13} "
                f"{'obs_' + str(RQ3_PRIMARY_YEAR_PAIR[0]):>10}  "
                f"{'obs_' + str(RQ3_PRIMARY_YEAR_PAIR[1]):>10}"
            )
            for i, band in enumerate(BAND_ORDER):
                log(f"    {band:<13} {tbl[i, 0]:>10,} {tbl[i, 1]:>10,}")

    # --- (c) regional + Bajio results tables ---------------------------
    log("")
    log("(c) regional test results (45 rows)")
    with pl.Config(
        tbl_rows=60, tbl_cols=-1, float_precision=4,
        fmt_str_lengths=30, tbl_hide_dataframe_shape=True,
        tbl_width_chars=400,
    ):
        log(str(reg_chi2.sort(["region", "status", "year_a"])))

    log("")
    log("(c') Bajio test results (9 rows)")
    with pl.Config(
        tbl_rows=30, tbl_cols=-1, float_precision=4,
        fmt_str_lengths=30, tbl_hide_dataframe_shape=True,
        tbl_width_chars=400,
    ):
        log(str(bajio_chi2.sort(["status", "year_a"])))

    # --- (d) primary significance summary ------------------------------
    log("")
    log(f"(d) primary pair {RQ3_PRIMARY_YEAR_PAIR} significance summary "
        "(p_holm < 0.05)")
    header = f"    {'region':<18} | " + " | ".join(
        [f"{s:<13}" for s in STATUS_ORDER]
    )
    log(header)
    log("    " + "-" * (len(header) - 4))
    primary_reg_sig = 0
    for region in CESOP_REGIONS:
        cells = []
        for status in STATUS_ORDER:
            row = next(
                r for r in reg_test_rows
                if r["region"] == region and r["status"] == status
                and r["year_a"] == RQ3_PRIMARY_YEAR_PAIR[0]
                and r["year_b"] == RQ3_PRIMARY_YEAR_PAIR[1]
            )
            ph = row["p_holm"]
            sig = (not math.isnan(ph)) and ph < 0.05
            if sig:
                primary_reg_sig += 1
            cells.append(f"{'SIG' if sig else 'ns ':<13}")
        log(f"    {region:<18} | " + " | ".join(cells))

    # --- (e) Cramer's V heatmap ----------------------------------------
    log("")
    log("(e) Cramer's V heatmap, primary pair (rows=region, cols=status)")
    header = f"    {'region':<18} | " + " | ".join(
        [f"{s:<16}" for s in STATUS_ORDER]
    )
    log(header)
    log("    " + "-" * (len(header) - 4))
    for region in CESOP_REGIONS:
        cells = []
        for status in STATUS_ORDER:
            row = next(
                r for r in reg_test_rows
                if r["region"] == region and r["status"] == status
                and r["year_a"] == RQ3_PRIMARY_YEAR_PAIR[0]
                and r["year_b"] == RQ3_PRIMARY_YEAR_PAIR[1]
            )
            v = row["cramer_v"]
            cells.append(
                f"{v:.3f} ({row['cramer_v_interp']:<10})"
                if not math.isnan(v) else f"{'n/a':<16}"
            )
        log(f"    {region:<18} | " + " | ".join(cells))

    # --- (f) primary-pair regional rate-ratios -------------------------
    log("")
    log(f"(f) regional rate ratios, primary pair {RQ3_PRIMARY_YEAR_PAIR}")
    for region in CESOP_REGIONS:
        log(f"    --- region = {region} ---")
        for status in STATUS_ORDER:
            log(f"        --- status = {status} ---")
            log(
                f"            {'band':<13} "
                f"{'n_a':>7} {'n_b':>7} "
                f"{'pop_a (M)':>10} {'pop_b (M)':>10} "
                f"{'RR [95% CI]':>28}"
            )
            for band in BAND_ORDER:
                r = next(
                    x for x in rr_reg_rows
                    if (x["region"] == region
                        and x["year_a"] == RQ3_PRIMARY_YEAR_PAIR[0]
                        and x["year_b"] == RQ3_PRIMARY_YEAR_PAIR[1]
                        and x["status"] == status
                        and x["band_2020"] == band)
                )
                if r["rate_ratio_defined"]:
                    rr_s = (f"{r['rate_ratio']:>6.2f} "
                            f"[{r['ci_lo']:.2f}, {r['ci_hi']:.2f}]")
                else:
                    rr_s = "n/a"
                log(
                    f"            {band:<13} "
                    f"{r['n_a']:>7,} {r['n_b']:>7,} "
                    f"{r['pop_a']/1e6:>10.3f} {r['pop_b']/1e6:>10.3f} "
                    f"{rr_s:>28}"
                )

    # --- (g) Bajio section --------------------------------------------
    log("")
    log(f"(g) Bajio sub-analysis — PRIMARY (29-muni SUN, n={n_bajio})")
    log(f"    Bajio bands populated: "
        f"{sorted(bajio_counts.filter(pl.col('band_population') > 0)['band_2020'].unique().to_list())}")
    log("")
    log(f"    Bajio contingency, primary pair {RQ3_PRIMARY_YEAR_PAIR}")
    for status in STATUS_ORDER:
        tbl = bajio_extras[(status,
                            RQ3_PRIMARY_YEAR_PAIR[0],
                            RQ3_PRIMARY_YEAR_PAIR[1])]["tbl"]
        log(f"    --- status = {status} ---")
        log(
            f"        {'band':<13} "
            f"{'obs_' + str(RQ3_PRIMARY_YEAR_PAIR[0]):>10}  "
            f"{'obs_' + str(RQ3_PRIMARY_YEAR_PAIR[1]):>10}"
        )
        for i, band in enumerate(BAND_ORDER):
            log(f"        {band:<13} {tbl[i, 0]:>10,} {tbl[i, 1]:>10,}")

    log("")
    log(f"    Bajio rate ratios, primary pair {RQ3_PRIMARY_YEAR_PAIR}")
    for status in STATUS_ORDER:
        log(f"        --- status = {status} ---")
        log(
            f"            {'band':<13} "
            f"{'n_a':>7} {'n_b':>7} "
            f"{'pop_a (M)':>10} {'pop_b (M)':>10} "
            f"{'RR [95% CI]':>28}"
        )
        for band in BAND_ORDER:
            r = next(
                x for x in rr_bajio_rows
                if (x["year_a"] == RQ3_PRIMARY_YEAR_PAIR[0]
                    and x["year_b"] == RQ3_PRIMARY_YEAR_PAIR[1]
                    and x["status"] == status
                    and x["band_2020"] == band)
            )
            if r["rate_ratio_defined"]:
                rr_s = (f"{r['rate_ratio']:>6.2f} "
                        f"[{r['ci_lo']:.2f}, {r['ci_hi']:.2f}]")
            else:
                rr_s = "n/a"
            log(
                f"            {band:<13} "
                f"{r['n_a']:>7,} {r['n_b']:>7,} "
                f"{r['pop_a']/1e6:>10.3f} {r['pop_b']/1e6:>10.3f} "
                f"{rr_s:>28}"
            )

    # --- (h) pre-registered predictions -------------------------------
    log("")
    log("(h) pre-registered predictions vs observed")

    def primary_row(region: str, status: str) -> dict:
        return next(
            r for r in reg_test_rows
            if r["region"] == region and r["status"] == status
            and r["year_a"] == RQ3_PRIMARY_YEAR_PAIR[0]
            and r["year_b"] == RQ3_PRIMARY_YEAR_PAIR[1]
        )

    def band_share_deltas(tbl: np.ndarray) -> tuple[int, float, float, float]:
        col_tot = tbl.sum(axis=0)
        if col_tot[0] == 0 or col_tot[1] == 0:
            return -1, 0.0, 0.0, 0.0
        share_a = tbl[:, 0] / col_tot[0]
        share_b = tbl[:, 1] / col_tot[1]
        delta = share_b - share_a
        i = int(np.argmax(np.abs(delta)))
        return i, float(share_a[i]), float(share_b[i]), float(delta[i])

    predictions: list[tuple[str, bool]] = []

    # 1. Centro-NL V >= 0.15
    r = primary_row("Centro", "not_located")
    v = r["cramer_v"]
    ok = (not math.isnan(v)) and v >= 0.15
    predictions.append(("Centro-NL V>=0.15", ok))
    log(
        f"    1. Centro-NL (primary): expected HIGHLY SIG V>=0.15; "
        f"observed V={v:.3f} {'PASS' if ok else 'FAIL'}"
    )

    # 2. Centro-LA V >= 0.20
    r = primary_row("Centro", "located_alive")
    v = r["cramer_v"]
    ok = (not math.isnan(v)) and v >= 0.20
    predictions.append(("Centro-LA V>=0.20", ok))
    log(
        f"    2. Centro-LA (primary): expected HIGHLY SIG V>=0.20 "
        f"(de-urbanization); observed V={v:.3f} {'PASS' if ok else 'FAIL'}"
    )

    # 3. Centro-Norte-NL significant; report largest share change
    r = primary_row("Centro-Norte", "not_located")
    tbl = reg_extras[("Centro-Norte", "not_located",
                      RQ3_PRIMARY_YEAR_PAIR[0],
                      RQ3_PRIMARY_YEAR_PAIR[1])]["tbl"]
    i, sa, sb, d = band_share_deltas(tbl)
    band_name = BAND_ORDER[i] if i >= 0 else "n/a"
    v = r["cramer_v"]
    ph = r["p_holm"]
    ok = (not math.isnan(ph)) and ph < 0.05
    predictions.append(("CNorte-NL sig", ok))
    log(
        f"    3. Centro-Norte-NL (primary): expected SIG with peak-decline "
        f"signature; observed V={v:.3f}, p_holm={ph:.4g} "
        f"{'(SIG)' if ok else '(ns)'}, largest |share change| band="
        f"{band_name} ({sa:.1%} -> {sb:.1%}, {d*100:+.1f} pp)"
    )

    # 4. Sur-NL possibly NOT SIG
    r = primary_row("Sur", "not_located")
    v = r["cramer_v"]
    ph = r["p_holm"]
    not_sig = math.isnan(ph) or ph >= 0.05
    predictions.append(("Sur-NL not-sig", not_sig))
    log(
        f"    4. Sur-NL (primary): expected possibly NOT SIG; "
        f"observed V={v:.3f}, p_holm={ph:.4g} "
        f"{'PASS (ns)' if not_sig else 'FAIL (SIG)'}"
    )

    # 5. Bajio-NL medium_city RR — strong acceleration (use RR >= 2.0)
    rr_b = next(
        x for x in rr_bajio_rows
        if x["year_a"] == RQ3_PRIMARY_YEAR_PAIR[0]
        and x["year_b"] == RQ3_PRIMARY_YEAR_PAIR[1]
        and x["status"] == "not_located"
        and x["band_2020"] == "medium_city"
    )
    if rr_b["rate_ratio_defined"]:
        rr_val = rr_b["rate_ratio"]
        ok = rr_val >= 2.0
    else:
        rr_val = float("nan")
        ok = False
    predictions.append(("Bajio-NL med_city RR>=2.0", ok))
    log(
        f"    5. Bajio-NL (primary): expected strong acceleration in "
        f"medium_city band; observed medium_city RR={rr_val:.2f} "
        f"{'PASS' if ok else 'FAIL'} (threshold >= 2.0)"
    )

    pred_pass = sum(1 for _, ok in predictions if ok)

    # --- (i) Bajio 29-muni reconciliation -------------------------------
    log("")
    log("(i) Bajio 29-muni reconciliation vs 200-muni is_bajio flag")

    # (i.1) 29-muni roster
    roster = pl.read_csv(
        REPO / "data" / "external" / "bajio_corridor_municipalities.csv",
        schema_overrides={"cvegeo": pl.Utf8},
    ).with_columns(pl.col("cvegeo").str.zfill(5)).sort("cvegeo")
    log("")
    log(f"    (i.1) 29-muni SUN roster (Medina-Fernandez et al. 2023; n={roster.height})")
    log(
        f"        {'cvegeo':<8} {'state':<18} {'muni':<28} "
        f"{'zm_entity':<38} {'type':<14}"
    )
    for row in roster.iter_rows(named=True):
        log(
            f"        {row['cvegeo']:<8} {row['state']:<18} "
            f"{row['municipality']:<28} {row['zm_entity']:<38} {row['entity_type']:<14}"
        )

    # (i.2) band distribution within the 29 (from primary Bajio counts,
    # any status collapsed — the muni composition by band is status-independent)
    b29_bands = (
        bajio_29["counts"]
        .filter(pl.col("year") == 2025)
        .group_by("band_2020")
        .agg(pl.col("band_population").first())
        .sort("band_2020")
    )
    # Count munis per band directly from denom.
    denom_29 = denom_full.filter(pl.col("cve_geo").is_in(list(BAJIO_29_CVEGEOS)))
    muni_per_band = (
        denom_29.group_by("band_2020")
        .len()
        .rename({"len": "n_munis"})
    )
    b29_bands = b29_bands.join(muni_per_band, on="band_2020", how="left").with_columns(
        pl.col("n_munis").fill_null(0)
    ).with_columns(
        pl.col("band_2020").cast(pl.Enum(BAND_ORDER))
    ).sort("band_2020")
    log("")
    log("    (i.2) band distribution within the 29 munis (2025 population)")
    with pl.Config(
        tbl_rows=20, tbl_cols=-1,
        fmt_str_lengths=30, tbl_hide_dataframe_shape=True,
    ):
        log(str(b29_bands.select(["band_2020", "n_munis", "band_population"])))

    # (i.3) side-by-side chi2 (29 vs 200) per (year_pair, status)
    log("")
    log("    (i.3) chi2 side-by-side (29-muni vs 200-muni) and deltas")
    log(
        f"        {'year_pair':<14} {'status':<15} | "
        f"{'29: chi2':>10} {'p_holm':>10} {'V':>6} | "
        f"{'200: chi2':>10} {'p_holm':>10} {'V':>6} | "
        f"{'dV':>7}"
    )
    for (ya, yb) in RQ3_YEAR_PAIRS:
        for status in STATUS_ORDER:
            r29 = next(
                r for r in bajio_29["test_rows"]
                if r["year_a"] == ya and r["year_b"] == yb and r["status"] == status
            )
            r200 = next(
                r for r in bajio_200["test_rows"]
                if r["year_a"] == ya and r["year_b"] == yb and r["status"] == status
            )
            dV = (r29["cramer_v"] - r200["cramer_v"]
                  if not (math.isnan(r29["cramer_v"]) or math.isnan(r200["cramer_v"]))
                  else float("nan"))
            log(
                f"        {ya}-{yb:<9} {status:<15} | "
                f"{r29['chi2']:>10.2f} {r29['p_holm']:>10.4g} "
                f"{r29['cramer_v']:>6.3f} | "
                f"{r200['chi2']:>10.2f} {r200['p_holm']:>10.4g} "
                f"{r200['cramer_v']:>6.3f} | "
                f"{dV:>+7.3f}"
            )

    # (i.4) primary-pair rate-ratio delta on medium_city NL (the pre-reg target)
    rr_29_medcity_nl = next(
        x for x in bajio_29["rr_rows"]
        if x["year_a"] == RQ3_PRIMARY_YEAR_PAIR[0]
        and x["year_b"] == RQ3_PRIMARY_YEAR_PAIR[1]
        and x["status"] == "not_located"
        and x["band_2020"] == "medium_city"
    )
    rr_200_medcity_nl = next(
        x for x in bajio_200["rr_rows"]
        if x["year_a"] == RQ3_PRIMARY_YEAR_PAIR[0]
        and x["year_b"] == RQ3_PRIMARY_YEAR_PAIR[1]
        and x["status"] == "not_located"
        and x["band_2020"] == "medium_city"
    )
    log("")
    log(
        f"    (i.4) primary-pair medium_city NL rate-ratio delta: "
        f"29-muni RR={rr_29_medcity_nl['rate_ratio']:.2f}, "
        f"200-muni RR={rr_200_medcity_nl['rate_ratio']:.2f}, "
        f"delta={rr_29_medcity_nl['rate_ratio'] - rr_200_medcity_nl['rate_ratio']:+.2f}"
    )

    # --- write log + stdout --------------------------------------------
    REPORTS_ALPHA.mkdir(parents=True, exist_ok=True)
    LOG_OUT.write_text("\n".join(log_lines) + "\n", encoding="utf-8")
    print("\n".join(log_lines))

    # primary significance counts
    primary_bajio_sig = sum(
        1 for r in bajio_test_rows
        if r["year_a"] == RQ3_PRIMARY_YEAR_PAIR[0]
        and r["year_b"] == RQ3_PRIMARY_YEAR_PAIR[1]
        and (not math.isnan(r["p_holm"])) and r["p_holm"] < 0.05
    )

    print("")
    print(
        f"[22b-bajio-reconcile] done. 29-muni list: found. "
        f"Bajio re-tested: yes. "
        f"Primary significant (Holm): {primary_reg_sig}/15 regional, "
        f"{primary_bajio_sig}/3 Bajio (29-muni). "
        f"Predictions: {pred_pass}/5 matched. Awaiting review."
    )


if __name__ == "__main__":
    try:
        main()
    except Exception:
        traceback.print_exc()
        sys.exit(1)
