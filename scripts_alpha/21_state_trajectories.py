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
BOOT_BLOCK_L = 12
BOOT_N_BLOCKS = int(np.ceil(N_MONTHS / BOOT_BLOCK_L))  # 11

CLASSIFICATION_OUT = INTERIM_ALPHA / "rq2_state_classification.parquet"
LOG_OUT = REPO / "reports" / "alpha" / "21_state_trajectories.log"

# --- classification thresholds (Step 3, calibrated) ---
THRESHOLD_LOWBASE_BASELINE_2015 = 2.0
THRESHOLD_ACC_TAU = 0.35
THRESHOLD_ACC_PEAK_YEAR = 2023
THRESHOLD_ACC_RATIO = 2.0
THRESHOLD_PEAKDECLINE_PEAK_YEARS = {2019, 2020, 2021, 2022}
THRESHOLD_PEAKDECLINE_TAU_MAX = 0.0
THRESHOLD_FEMALE_ANOM_YEARS = 8
THRESHOLD_FEMALE_ANOM_MEAN = 0.55

EXPECTED_CLASS = {
    19: "Accelerating",      # Nuevo Leon
    15: "Accelerating",      # Edo. de Mexico
    11: "Accelerating",      # Guanajuato
    14: "Peak-decline",      # Jalisco
    30: "Moderate",          # Veracruz
    5:  "Moderate",          # Coahuila
    18: "Low-baseline",      # Nayarit
    27: "Low-baseline",      # Tabasco
}
EXPECTED_FEMALE_ANOM = {
    19: False, 15: True,  11: False,
    14: False, 30: False, 5:  False,
    18: False, 27: True,
}


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

            # Moving-block bootstrap (L=12 months, preserves 12-month
            # temporal structure — avoids collapsing to ~0 that an IID
            # value-resample produces).
            boot = np.empty(BOOT_B, dtype=np.float64)
            for b in range(BOOT_B):
                starts = rng.integers(0, N_MONTHS - BOOT_BLOCK_L,
                                      size=BOOT_N_BLOCKS)
                blocks = np.concatenate(
                    [series[s:s + BOOT_BLOCK_L] for s in starts]
                )
                trimmed = blocks[:N_MONTHS]
                boot[b] = mk.sens_slope(trimmed).slope
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

    # --- classification (NL series, first-match-wins) -------------------
    nl_by_state = {
        r["cve_ent"]: r
        for r in metrics.filter(pl.col("status") == "not_located")
                       .iter_rows(named=True)
    }

    fsos_stats = (
        fsos.group_by(["cve_ent", "nom_ent"])
        .agg(
            (pl.col("fsos_la_annual") >= 0.50)
                .fill_null(False).sum()
                .alias("fsos_la_years_above_parity"),
            pl.col("fsos_la_annual").mean().alias("mean_fsos_la_11yr"),
        )
    )
    fsos_by_state = {
        r["cve_ent"]: r for r in fsos_stats.iter_rows(named=True)
    }

    def classify_nl(m: dict) -> tuple[str, float]:
        mean_monthly = m["mean_monthly"]
        tau = m["mk_tau"]
        peak_year = m["peak_year"]
        baseline = m["baseline"]
        current = m["current"]
        if baseline == 0:
            ratio = float("inf") if current > 0 else 0.0
        else:
            ratio = current / baseline
        if baseline < THRESHOLD_LOWBASE_BASELINE_2015:
            return "Low-baseline", ratio
        if (tau > THRESHOLD_ACC_TAU
                and peak_year >= THRESHOLD_ACC_PEAK_YEAR
                and ratio > THRESHOLD_ACC_RATIO):
            return "Accelerating", ratio
        if (peak_year in THRESHOLD_PEAKDECLINE_PEAK_YEARS
                and tau <= THRESHOLD_PEAKDECLINE_TAU_MAX):
            return "Peak-decline", ratio
        return "Moderate", ratio

    class_rows: list[dict] = []
    for (cve_ent, nom_ent, region) in CED_STATES:
        m = nl_by_state[cve_ent]
        f = fsos_by_state[cve_ent]
        traj, ratio = classify_nl(m)
        n_above = int(f["fsos_la_years_above_parity"])
        mean_fsos = float(f["mean_fsos_la_11yr"])
        female_anom = (
            n_above >= THRESHOLD_FEMALE_ANOM_YEARS
            and mean_fsos >= THRESHOLD_FEMALE_ANOM_MEAN
        )
        class_rows.append({
            "cve_ent": int(cve_ent),
            "nom_ent": nom_ent,
            "region": region,
            "trajectory_class": traj,
            "female_anomalous": bool(female_anom),
            "mean_monthly_nl": float(m["mean_monthly"]),
            "mk_tau_nl": float(m["mk_tau"]),
            "peak_year_nl": int(m["peak_year"]),
            "curr_over_base_nl": float(ratio),
            "fsos_la_years_above_parity": n_above,
            "mean_fsos_la_11yr": mean_fsos,
        })

    classification = pl.DataFrame(class_rows).select([
        "cve_ent", "nom_ent", "region",
        "trajectory_class", "female_anomalous",
        "mean_monthly_nl", "mk_tau_nl", "peak_year_nl",
        "curr_over_base_nl",
        "fsos_la_years_above_parity", "mean_fsos_la_11yr",
    ])
    if classification.height != 8:
        raise ValueError(
            f"classification: expected 8 rows, got {classification.height}"
        )
    classification.write_parquet(CLASSIFICATION_OUT)

    # --- build log --------------------------------------------------------
    log_lines: list[str] = []

    def log(msg: str = "") -> None:
        log_lines.append(msg)

    log("=" * 72)
    log("[21] state_trajectories - Step 3 (classification applied)")
    log("=" * 72)

    log("")
    log("(a) thresholds (calibrated)")
    log(f"    THRESHOLD_LOWBASE_BASELINE_2015      = {THRESHOLD_LOWBASE_BASELINE_2015}")
    log(f"    THRESHOLD_ACC_TAU                    = {THRESHOLD_ACC_TAU}")
    log(f"    THRESHOLD_ACC_PEAK_YEAR              = {THRESHOLD_ACC_PEAK_YEAR}")
    log(f"    THRESHOLD_ACC_RATIO                  = {THRESHOLD_ACC_RATIO}")
    log(f"    THRESHOLD_PEAKDECLINE_PEAK_YEARS     = {sorted(THRESHOLD_PEAKDECLINE_PEAK_YEARS)}")
    log(f"    THRESHOLD_PEAKDECLINE_TAU_MAX        = {THRESHOLD_PEAKDECLINE_TAU_MAX}")
    log(f"    THRESHOLD_FEMALE_ANOM_YEARS          = {THRESHOLD_FEMALE_ANOM_YEARS}")
    log(f"    THRESHOLD_FEMALE_ANOM_MEAN           = {THRESHOLD_FEMALE_ANOM_MEAN}")

    log("")
    log("(b) rq2_state_metrics.parquet (24 rows, moving-block-bootstrap CIs, per-year units):")
    with pl.Config(
        tbl_rows=30, tbl_cols=-1, float_precision=4,
        fmt_str_lengths=30, tbl_hide_dataframe_shape=True,
        tbl_width_chars=400,
    ):
        log(str(metrics))

    log("")
    log("(c) rq2_state_classification.parquet (8 rows):")
    with pl.Config(
        tbl_rows=30, tbl_cols=-1, float_precision=4,
        fmt_str_lengths=30, tbl_hide_dataframe_shape=True,
        tbl_width_chars=400,
    ):
        log(str(classification))

    log("")
    log("(d) per-state narrative")
    for r in class_rows:
        log(
            f"    {r['nom_ent']} ({r['region']}): "
            f"NL t={r['mk_tau_nl']:+.2f}, peak={r['peak_year_nl']}, "
            f"curr/base={r['curr_over_base_nl']:.1f}x -> {r['trajectory_class']}; "
            f"FSoS-LA {r['fsos_la_years_above_parity']}/11 yrs >= parity, "
            f"mean={r['mean_fsos_la_11yr']:.3f} -> "
            f"female_anomalous={r['female_anomalous']}"
        )

    log("")
    log("(e) summary counts")
    class_counts = (
        classification.group_by("trajectory_class")
        .len().rename({"len": "n"}).sort("trajectory_class")
    )
    anom_counts = (
        classification.group_by("female_anomalous")
        .len().rename({"len": "n"}).sort("female_anomalous")
    )
    with pl.Config(
        tbl_rows=30, tbl_cols=-1,
        fmt_str_lengths=30, tbl_hide_dataframe_shape=True,
    ):
        log("    by trajectory_class:")
        log(str(class_counts))
        log("    by female_anomalous:")
        log(str(anom_counts))

    # --- deviation report vs expected ------------------------------------
    deviations: list[str] = []
    for r in class_rows:
        exp_class = EXPECTED_CLASS.get(r["cve_ent"])
        if exp_class is not None and r["trajectory_class"] != exp_class:
            deviations.append(
                f"    {r['nom_ent']}: expected {exp_class}, "
                f"got {r['trajectory_class']}"
            )
        exp_anom = EXPECTED_FEMALE_ANOM.get(r["cve_ent"])
        if exp_anom is True and not r["female_anomalous"]:
            deviations.append(
                f"    {r['nom_ent']}: expected female_anomalous=True, "
                f"got {r['female_anomalous']}"
            )
        elif exp_anom is False and r["female_anomalous"]:
            deviations.append(
                f"    {r['nom_ent']}: expected female_anomalous=False, "
                f"got {r['female_anomalous']}"
            )

    matches = 0
    for r in class_rows:
        exp_class = EXPECTED_CLASS.get(r["cve_ent"])
        exp_anom = EXPECTED_FEMALE_ANOM.get(r["cve_ent"])
        class_ok = exp_class is None or r["trajectory_class"] == exp_class
        anom_ok = exp_anom is None or r["female_anomalous"] == exp_anom
        if class_ok and anom_ok:
            matches += 1

    log("")
    log("(f) deviations from expected sanity reference")
    if deviations:
        for d in deviations:
            log(d)
    else:
        log("    none")

    LOG_OUT.parent.mkdir(parents=True, exist_ok=True)
    LOG_OUT.write_text("\n".join(log_lines) + "\n", encoding="utf-8")

    print("\n".join(log_lines))
    print("")
    print(
        f"[21] rerun done. Low-baseline threshold keyed on baseline_nl < 2.0. "
        f"Expected matches: {matches}/8. Awaiting review."
    )


if __name__ == "__main__":
    try:
        main()
    except Exception:
        traceback.print_exc()
        sys.exit(1)
