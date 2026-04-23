"""RQ2 state trajectories — Paper α.

Two-halt execution. This run reaches HALT 1: metrics computed, no
classification yet (thresholds TBD after user review).

Inputs
------
- data/interim/alpha/alpha_panel_long.parquet

Outputs written in this run
---------------------------
- data/interim/alpha/rq2_state_monthly_8ced.parquet
- data/interim/alpha/rq2_state_metrics.parquet
- data/interim/alpha/rq2_state_fsos_la_annual.parquet

Not written until Step 3
------------------------
- data/interim/alpha/rq2_state_classification.parquet
- reports/alpha/21_state_trajectories.log
"""
from __future__ import annotations

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
    CED_STATES,
    STATUS_ORDER,
    TRAJECTORY_CLASSES,  # noqa: F401 - part of public contract for Step 3
)

import pymannkendall as mk  # noqa: E402

REPO = Path(__file__).resolve().parents[1]
INTERIM_ALPHA = REPO / "data" / "interim" / "alpha"

PANEL_IN = INTERIM_ALPHA / "alpha_panel_long.parquet"
MONTHLY_OUT = INTERIM_ALPHA / "rq2_state_monthly_8ced.parquet"
METRICS_OUT = INTERIM_ALPHA / "rq2_state_metrics.parquet"
FSOS_OUT = INTERIM_ALPHA / "rq2_state_fsos_la_annual.parquet"

YEARS = list(range(2015, 2026))       # 2015..2025 inclusive, 11 years
MONTHS = list(range(1, 13))           # 1..12
N_MONTHS = len(YEARS) * len(MONTHS)   # 132
EXPECTED_MONTHLY_ROWS = len(CED_STATES) * N_MONTHS * len(STATUS_ORDER)  # 3168

BOOT_B = 2000
BOOT_SEED = 20_260_422


def rolling_trailing_sum(arr: np.ndarray, window: int) -> np.ndarray:
    """Trailing rolling sum: result[i] = sum(arr[max(0, i-window+1):i+1])."""
    out = np.empty_like(arr, dtype=np.float64)
    cum = np.concatenate(([0.0], np.cumsum(arr, dtype=np.float64)))
    for i in range(arr.size):
        lo = max(0, i - window + 1)
        out[i] = cum[i + 1] - cum[lo]
    return out


def main() -> None:
    # --- load + derive cve_ent ------------------------------------------
    panel = pl.read_parquet(PANEL_IN)
    panel = panel.with_columns(
        pl.col("cve_geo").str.slice(0, 2).cast(pl.Int64).alias("cve_ent")
    )

    ced_lookup = pl.DataFrame(
        CED_STATES,
        schema=["cve_ent", "nom_ent", "region"],
        orient="row",
    ).with_columns(pl.col("cve_ent").cast(pl.Int64))

    state_ids = [s[0] for s in CED_STATES]

    # --- filter + aggregate ---------------------------------------------
    agg = (
        panel.filter(pl.col("cve_ent").is_in(state_ids))
        .group_by(["cve_ent", "year", "month", "status"])
        .agg(
            pl.col("male").sum(),
            pl.col("female").sum(),
            pl.col("undefined").sum(),
            pl.col("total").sum(),
        )
    )

    # --- zero-fill full grid --------------------------------------------
    grid = (
        pl.DataFrame({"cve_ent": state_ids}, schema={"cve_ent": pl.Int64})
        .join(pl.DataFrame({"year": YEARS},
                           schema={"year": pl.Int64}), how="cross")
        .join(pl.DataFrame({"month": MONTHS},
                           schema={"month": pl.Int64}), how="cross")
        .join(pl.DataFrame({"status": STATUS_ORDER}), how="cross")
    )
    monthly = (
        grid.join(agg, on=["cve_ent", "year", "month", "status"], how="left")
        .with_columns(
            pl.col("male").fill_null(0),
            pl.col("female").fill_null(0),
            pl.col("undefined").fill_null(0),
            pl.col("total").fill_null(0),
        )
        .join(ced_lookup.select(["cve_ent", "nom_ent"]),
              on="cve_ent", how="left")
        .select([
            "cve_ent", "nom_ent", "year", "month", "status",
            "male", "female", "undefined", "total",
        ])
        .sort(["cve_ent", "status", "year", "month"])
    )
    if monthly.height != EXPECTED_MONTHLY_ROWS:
        raise ValueError(
            f"zero-filled monthly panel: expected {EXPECTED_MONTHLY_ROWS} rows, "
            f"got {monthly.height}"
        )
    monthly.write_parquet(MONTHLY_OUT)

    # --- per-(state, status) metrics ------------------------------------
    rng = np.random.default_rng(BOOT_SEED)

    metric_rows: list[dict] = []
    for (cve_ent, nom_ent, region) in CED_STATES:
        for status in STATUS_ORDER:
            sub = (
                monthly.filter(
                    (pl.col("cve_ent") == cve_ent)
                    & (pl.col("status") == status)
                )
                .sort(["year", "month"])
            )
            if sub.height != N_MONTHS:
                raise ValueError(
                    f"({cve_ent}, {status}): expected {N_MONTHS} monthly rows, "
                    f"got {sub.height}"
                )
            series = sub["total"].to_numpy().astype(np.float64)

            mk_res = mk.original_test(series)
            sen_res = mk.sens_slope(series)
            sen_m = float(sen_res.slope)
            sen_y = sen_m * 12.0

            boot = np.empty(BOOT_B, dtype=np.float64)
            for b in range(BOOT_B):
                idx = rng.integers(0, N_MONTHS, size=N_MONTHS)
                boot[b] = mk.sens_slope(series[idx]).slope
            ci_lo_m, ci_hi_m = np.percentile(boot, [2.5, 97.5])
            ci_lo_yr = float(ci_lo_m) * 12.0
            ci_hi_yr = float(ci_hi_m) * 12.0

            roll12 = rolling_trailing_sum(series, 12)
            peak_idx = int(np.argmax(roll12))
            peak_level = float(roll12[peak_idx])
            peak_year = YEARS[peak_idx // 12]
            peak_month = (peak_idx % 12) + 1

            baseline_mask = sub["year"].to_numpy() == 2015
            current_mask = np.isin(sub["year"].to_numpy(), [2024, 2025])
            baseline = float(series[baseline_mask].mean())
            current = float(series[current_mask].mean())
            mean_monthly = float(series.mean())
            n_nonzero_months = int((series > 0).sum())

            metric_rows.append({
                "cve_ent": int(cve_ent),
                "nom_ent": nom_ent,
                "region": region,
                "status": status,
                "mk_tau": float(mk_res.Tau),
                "mk_p": float(mk_res.p),
                "sen_slope_per_month": sen_m,
                "sen_slope_per_year": sen_y,
                "sen_ci_lo_yr": ci_lo_yr,
                "sen_ci_hi_yr": ci_hi_yr,
                "baseline": baseline,
                "current": current,
                "peak_level": peak_level,
                "peak_month": peak_month,
                "peak_year": peak_year,
                "mean_monthly": mean_monthly,
                "n_nonzero_months": n_nonzero_months,
            })

    metric_cols = [
        "cve_ent", "nom_ent", "region", "status",
        "mk_tau", "mk_p",
        "sen_slope_per_month", "sen_slope_per_year",
        "sen_ci_lo_yr", "sen_ci_hi_yr",
        "baseline", "current",
        "peak_level", "peak_month", "peak_year",
        "mean_monthly", "n_nonzero_months",
    ]
    metrics = pl.DataFrame(metric_rows).select(metric_cols)
    if metrics.height != 24:
        raise ValueError(f"metrics row count: expected 24, got {metrics.height}")
    metrics.write_parquet(METRICS_OUT)

    # --- FSoS-in-LA annual ----------------------------------------------
    fsos = (
        monthly.filter(pl.col("status") == "located_alive")
        .group_by(["cve_ent", "nom_ent", "year"])
        .agg(
            pl.col("female").sum().alias("f"),
            pl.col("male").sum().alias("m"),
        )
        .with_columns(
            (pl.col("f") + pl.col("m")).alias("n_sexed_la"),
        )
        .with_columns(
            pl.when(pl.col("n_sexed_la") > 0)
              .then(pl.col("f") / pl.col("n_sexed_la"))
              .otherwise(None)
              .alias("fsos_la_annual"),
        )
        .select(["cve_ent", "nom_ent", "year", "fsos_la_annual", "n_sexed_la"])
        .sort(["cve_ent", "year"])
    )
    if fsos.height != len(CED_STATES) * len(YEARS):
        raise ValueError(
            f"FSoS-LA annual: expected {len(CED_STATES) * len(YEARS)} rows, "
            f"got {fsos.height}"
        )
    fsos.write_parquet(FSOS_OUT)

    years_above = (
        fsos.with_columns(
            (pl.col("fsos_la_annual") >= 0.50).fill_null(False).alias("above"),
        )
        .group_by(["cve_ent", "nom_ent"])
        .agg(pl.col("above").sum().alias("fsos_la_years_above_parity"))
        .sort("cve_ent")
    )

    # --- HALT POINT 1 print ---------------------------------------------
    print("=" * 72)
    print("[21] HALT 1 - metrics computed, classification NOT applied")
    print("=" * 72)

    print("")
    print("rq2_state_metrics.parquet (24 rows, 4-dp floats):")
    with pl.Config(
        tbl_rows=30, tbl_cols=-1, float_precision=4,
        fmt_str_lengths=30, tbl_hide_dataframe_shape=True,
        tbl_width_chars=400,
    ):
        print(str(metrics))

    print("")
    print("Per-state NL summary (status='not_located'):")
    nl = (
        metrics.filter(pl.col("status") == "not_located")
        .with_columns(
            (pl.col("current") / pl.col("baseline")).alias("curr_over_base"),
        )
        .select([
            "cve_ent", "nom_ent", "region",
            "mk_tau", "sen_slope_per_year",
            "peak_year", "peak_month",
            "baseline", "current", "curr_over_base",
        ])
        .sort("cve_ent")
    )
    with pl.Config(
        tbl_rows=30, tbl_cols=-1, float_precision=4,
        fmt_str_lengths=30, tbl_hide_dataframe_shape=True,
        tbl_width_chars=400,
    ):
        print(str(nl))

    print("")
    print("Per-state FSoS-LA years >= 0.50 (of 11 years):")
    with pl.Config(
        tbl_rows=30, tbl_cols=-1,
        fmt_str_lengths=30, tbl_hide_dataframe_shape=True,
        tbl_width_chars=200,
    ):
        print(str(years_above))

    print("")
    print(
        f"[21] HALT 1: metrics computed. {metrics.height} metric rows, "
        f"{fsos.height} FSoS-annual rows. Threshold calibration pending "
        "user review. Classification NOT yet applied."
    )


if __name__ == "__main__":
    try:
        main()
    except Exception:
        traceback.print_exc()
        sys.exit(1)
