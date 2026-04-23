"""RQ1 sex-composition descriptives + hypothesis tests for Paper α.

Inputs
------
- data/interim/alpha/alpha_cross_sections.parquet
- data/interim/alpha/alpha_panel_long.parquet

Outputs
-------
- data/interim/alpha/rq1_sex_cross_sections.parquet
- data/interim/alpha/rq1_sex_monthly.parquet
- data/interim/alpha/rq1_sex_tests.parquet
- reports/alpha/20_sex_composition.log
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
    CROSS_SECTION_YEARS,
    STATUS_ORDER,
    wilson_ci,
)

from scipy.stats import binomtest  # noqa: E402
from statsmodels.stats.multitest import multipletests  # noqa: E402
from statsmodels.stats.proportion import proportions_ztest  # noqa: E402

REPO = Path(__file__).resolve().parents[1]
INTERIM_ALPHA = REPO / "data" / "interim" / "alpha"
REPORTS_ALPHA = REPO / "reports" / "alpha"

XS_IN = INTERIM_ALPHA / "alpha_cross_sections.parquet"
PANEL_IN = INTERIM_ALPHA / "alpha_panel_long.parquet"
XS_OUT = INTERIM_ALPHA / "rq1_sex_cross_sections.parquet"
MONTHLY_OUT = INTERIM_ALPHA / "rq1_sex_monthly.parquet"
TESTS_OUT = INTERIM_ALPHA / "rq1_sex_tests.parquet"
LOG_OUT = REPORTS_ALPHA / "20_sex_composition.log"

EXPECTED_XS_ROWS = 5_737


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
        print(msg)

    # --- (a) load + input-row check --------------------------------------
    xs_raw = pl.read_parquet(XS_IN)
    if xs_raw.height != EXPECTED_XS_ROWS:
        raise ValueError(
            f"{XS_IN.name}: expected {EXPECTED_XS_ROWS:,} rows, "
            f"got {xs_raw.height:,}"
        )
    panel = pl.read_parquet(PANEL_IN)

    log("=" * 72)
    log("[20] sex_composition — QA log")
    log("=" * 72)
    log(f"(a) cross-sections rows: {xs_raw.height:,} (expected {EXPECTED_XS_ROWS:,})")
    log(f"    panel rows:          {panel.height:,}")

    # --- (b) national cross-section aggregation --------------------------
    cs = (
        xs_raw.group_by(["year", "status"])
        .agg(
            pl.col("male").sum().alias("n_male"),
            pl.col("female").sum().alias("n_female"),
            pl.col("undefined").sum().alias("n_undefined"),
            pl.col("total").sum().alias("n_total"),
        )
        .sort(["status", "year"])
    )
    if cs.height != 9:
        raise ValueError(f"cross-section aggregation: expected 9 rows, got {cs.height}")

    # --- (c) sanity: male + female + undefined == total ------------------
    mismatch = cs.filter(
        pl.col("n_male") + pl.col("n_female") + pl.col("n_undefined")
        != pl.col("n_total")
    )
    if mismatch.height != 0:
        raise ValueError(
            "row-wise sanity failed (n_male+n_female+n_undefined != n_total):\n"
            f"{mismatch}"
        )

    cs = cs.with_columns(
        (pl.col("n_female") + pl.col("n_male")).alias("n_sexed"),
    ).with_columns(
        (pl.col("n_female") / pl.col("n_total")).alias("pct_female"),
        (pl.col("n_male") / pl.col("n_total")).alias("pct_male"),
        (pl.col("n_undefined") / pl.col("n_total")).alias("pct_undefined"),
        (pl.col("n_female") / pl.col("n_sexed")).alias("female_share_of_sexed"),
    )

    wilson = [
        wilson_ci(int(k), int(n))
        for k, n in zip(cs["n_female"].to_list(), cs["n_sexed"].to_list())
    ]
    cs = cs.with_columns(
        pl.Series("wilson_lo", [w[0] for w in wilson], dtype=pl.Float64),
        pl.Series("wilson_hi", [w[1] for w in wilson], dtype=pl.Float64),
    ).select([
        "year", "status",
        "n_male", "n_female", "n_undefined", "n_total",
        "n_sexed", "pct_female", "pct_male", "pct_undefined",
        "female_share_of_sexed", "wilson_lo", "wilson_hi",
    ])

    cs.write_parquet(XS_OUT)

    with pl.Config(
        tbl_rows=20, tbl_cols=-1, float_precision=4,
        fmt_str_lengths=60, tbl_hide_dataframe_shape=True,
    ):
        cs_display = cs.select([
            "year", "status",
            "n_female", "n_male", "n_undefined",
            "pct_undefined", "female_share_of_sexed",
            "wilson_lo", "wilson_hi",
        ])
        log("")
        log("(b) cross-section table (year × status), 4-dp proportions")
        log(str(cs_display))

    log("")
    log("(c) row-wise sanity: n_male + n_female + n_undefined == n_total  ->  PASS")

    # --- monthly panel ---------------------------------------------------
    monthly = (
        panel.group_by(["year", "month", "status"])
        .agg(
            pl.col("male").sum().alias("n_male"),
            pl.col("female").sum().alias("n_female"),
            pl.col("undefined").sum().alias("n_undefined"),
        )
        .with_columns(
            (pl.col("n_female") + pl.col("n_male")).alias("n_sexed"),
        )
        .with_columns(
            pl.when(pl.col("n_sexed") > 0)
            .then(pl.col("n_female") / pl.col("n_sexed"))
            .otherwise(None)
            .alias("female_share_of_sexed"),
        )
        .sort(["status", "year", "month"])
    )
    monthly.write_parquet(MONTHLY_OUT)

    log("")
    log(f"(d) monthly rows: {monthly.height} (cap 132 x 3 = 396)")
    log(
        f"    year range: {monthly['year'].min()}-{monthly['year'].max()}; "
        f"month range: {monthly['month'].min()}-{monthly['month'].max()}; "
        f"status set: {sorted(monthly['status'].unique().to_list())}"
    )
    empty_cells = 396 - monthly.height
    log(f"    empty (year, month, status) cells vs. 396 cap: {empty_cells}")

    # --- Block A — binomial vs parity ------------------------------------
    block_a_rows: list[dict] = []
    for row in cs.sort(["status", "year"]).iter_rows(named=True):
        k = int(row["n_female"])
        n = int(row["n_sexed"])
        p_raw = float(binomtest(k=k, n=n, p=0.5).pvalue)
        block_a_rows.append({
            "test": "binom_vs_parity",
            "status": row["status"],
            "year_a": int(row["year"]),
            "year_b": None,
            "stat": float(row["female_share_of_sexed"]),
            "p_raw": p_raw,
            "n_a": n,
            "n_b": None,
        })
    a_p_holm = multipletests(
        [r["p_raw"] for r in block_a_rows], method="holm"
    )[1]
    for r, ph in zip(block_a_rows, a_p_holm):
        r["p_holm"] = float(ph)

    # --- Block B — two-proportion z-tests, 2015 vs 2025 per status -------
    block_b_rows: list[dict] = []
    for status in STATUS_ORDER:
        r15 = cs.filter(
            (pl.col("status") == status) & (pl.col("year") == 2015)
        ).row(0, named=True)
        r25 = cs.filter(
            (pl.col("status") == status) & (pl.col("year") == 2025)
        ).row(0, named=True)
        z, p_raw = proportions_ztest(
            count=[int(r25["n_female"]), int(r15["n_female"])],
            nobs=[int(r25["n_sexed"]), int(r15["n_sexed"])],
        )
        block_b_rows.append({
            "test": "prop_2015_vs_2025",
            "status": status,
            "year_a": 2025,
            "year_b": 2015,
            "stat": float(z),
            "p_raw": float(p_raw),
            "n_a": int(r25["n_sexed"]),
            "n_b": int(r15["n_sexed"]),
        })
    b_p_holm = multipletests(
        [r["p_raw"] for r in block_b_rows], method="holm"
    )[1]
    for r, ph in zip(block_b_rows, b_p_holm):
        r["p_holm"] = float(ph)

    # --- assemble tests parquet ------------------------------------------
    COLS = ["test", "status", "year_a", "year_b",
            "stat", "p_raw", "p_holm", "n_a", "n_b"]
    tests_df = pl.DataFrame(
        block_a_rows + block_b_rows,
        schema={
            "test": pl.Utf8,
            "status": pl.Utf8,
            "year_a": pl.Int64,
            "year_b": pl.Int64,
            "stat": pl.Float64,
            "p_raw": pl.Float64,
            "n_a": pl.Int64,
            "n_b": pl.Int64,
            "p_holm": pl.Float64,
        },
    ).select(COLS)
    tests_df.write_parquet(TESTS_OUT)

    # --- (e) Block A log -------------------------------------------------
    log("")
    log("(e) Block A - binomial vs parity (H0: FSoS = 0.5)")
    a_view = (
        tests_df.filter(pl.col("test") == "binom_vs_parity")
        .select(["status", "year_a", "n_a", "stat", "p_raw", "p_holm"])
        .rename({"year_a": "year", "n_a": "n_sexed", "stat": "FSoS"})
        .sort(["status", "year"])
    )
    with pl.Config(
        tbl_rows=20, tbl_cols=-1, float_precision=6,
        tbl_hide_dataframe_shape=True,
    ):
        log(str(a_view))
    a_sig = 0
    for r in block_a_rows:
        s = stars(r["p_holm"])
        if s:
            a_sig += 1
        log(
            f"    {r['status']:13s} y={r['year_a']}  "
            f"FSoS={r['stat']:.4f}  p_raw={r['p_raw']:.4g}  "
            f"p_holm={r['p_holm']:.4g} {s}"
        )

    # --- (f) Block B log -------------------------------------------------
    log("")
    log("(f) Block B - two-proportion z-test, 2025 vs 2015")
    b_view = (
        tests_df.filter(pl.col("test") == "prop_2015_vs_2025")
        .select(["status", "year_a", "year_b", "n_a", "n_b",
                 "stat", "p_raw", "p_holm"])
        .rename({"n_a": "n_2025", "n_b": "n_2015", "stat": "z"})
    )
    with pl.Config(
        tbl_rows=20, tbl_cols=-1, float_precision=6,
        tbl_hide_dataframe_shape=True,
    ):
        log(str(b_view))
    b_sig = 0
    for r in block_b_rows:
        s = stars(r["p_holm"])
        if s:
            b_sig += 1
        log(
            f"    {r['status']:13s} 2025 vs 2015  "
            f"z={r['stat']:+.4f}  p_raw={r['p_raw']:.4g}  "
            f"p_holm={r['p_holm']:.4g} {s}"
        )

    # --- (g) narrative per status ---------------------------------------
    log("")
    log("(g) per-status narrative (FSoS 2015 -> 2025, Holm across Block B)")
    cs_by_key = {(r["status"], r["year"]): r for r in cs.iter_rows(named=True)}
    b_by_status = {r["status"]: r for r in block_b_rows}
    for status in STATUS_ORDER:
        r15 = cs_by_key[(status, 2015)]
        r25 = cs_by_key[(status, 2025)]
        b = b_by_status[status]
        log(
            f"    {status}: FSoS 2015={r15['female_share_of_sexed']:.3f} "
            f"[{r15['wilson_lo']:.3f}, {r15['wilson_hi']:.3f}], "
            f"2025={r25['female_share_of_sexed']:.3f} "
            f"[{r25['wilson_lo']:.3f}, {r25['wilson_hi']:.3f}], "
            f"delta={r25['female_share_of_sexed'] - r15['female_share_of_sexed']:+.3f}, "
            f"Holm p={b['p_holm']:.4g} {stars(b['p_holm'])}"
        )

    # --- write log -------------------------------------------------------
    REPORTS_ALPHA.mkdir(parents=True, exist_ok=True)
    LOG_OUT.write_text("\n".join(log_lines) + "\n", encoding="utf-8")

    print("")
    print(
        f"[20] done. cs_rows={cs.height}, monthly_rows={monthly.height}, "
        f"tests={tests_df.height}. "
        f"Block A significant (Holm): {a_sig}/9. "
        f"Block B significant (Holm): {b_sig}/3. "
        "Awaiting review."
    )


if __name__ == "__main__":
    try:
        main()
    except Exception:
        traceback.print_exc()
        sys.exit(1)
