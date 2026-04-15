"""Phase 2 — VAWRI external validation.

Compares HH municipalities from LISA (June 2023 cross-section) against
VAWRI Mexico 2023 composite scores.  Temporal alignment: both datasets
reference 2023, eliminating the 2-year mismatch in the prior analysis.

Tests:
  - Mann-Whitney U (HH vs non-HH) per status_id, total sex
  - Mann-Whitney U per status_id × sex for status 7 (Not Located) and 3 (Located Dead)
  - Rank-biserial correlation as effect size  (r = 1 - 2U/(n1*n2))

Outputs:
  reports/paper1_verification/11_vawri_comparison_jun2023.md
"""

from __future__ import annotations

import sys
import logging
from pathlib import Path

import numpy as np
import pandas as pd
import polars as pl
from scipy.stats import mannwhitneyu

# ---------------------------------------------------------------------------
# CONFIG
# ---------------------------------------------------------------------------
ROOT = Path(__file__).resolve().parent.parent
DATA_PROC = ROOT / "data" / "processed"
DATA_EXT = ROOT / "data" / "external"
REPORTS = ROOT / "reports" / "paper1_verification"
LOGS_DIR = ROOT / "logs"

LISA_FILE = DATA_PROC / "lisa_monthly_results.parquet"
VAWRI_FILE = DATA_EXT / "vawri" / "vawri_mexico_2023_data.csv"
OUTPUT_MD = REPORTS / "11_vawri_comparison_jun2023.md"

# LISA cross-section: June 2023 to match VAWRI 2023
LISA_YEAR = 2023
LISA_MONTH = 6

STATUS_LABELS = {0: "Total", 7: "Not Located", 2: "Located Alive", 3: "Located Dead"}

# ---------------------------------------------------------------------------
# LOGGING
# ---------------------------------------------------------------------------
LOGS_DIR.mkdir(exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    handlers=[
        logging.FileHandler(LOGS_DIR / "pipeline.log", mode="a"),
        logging.StreamHandler(sys.stdout),
    ],
)
log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# HELPERS
# ---------------------------------------------------------------------------
def rank_biserial(u_stat: float, n1: int, n2: int) -> float:
    """Rank-biserial correlation: r = 2U/(n1·n2) − 1.

    scipy.stats.mannwhitneyu returns U₁ for the first sample.
    When alternative='greater' and x truly > y, U₁ ≈ n1·n2 and r → +1.
    """
    return 2.0 * u_stat / (n1 * n2) - 1.0


def iqr_str(series: pd.Series) -> str:
    """Format IQR as 'Q1–Q3'."""
    q1, q3 = series.quantile(0.25), series.quantile(0.75)
    return f"{q1:.3f}–{q3:.3f}"


def run_test(merged: pd.DataFrame, status_id: int, sex: str) -> dict | None:
    """Run Mann-Whitney U comparing VAWRI in HH vs non-HH for one slice."""
    if sex == "total":
        sub = merged[merged["status_id"] == status_id]
    else:
        sub = merged[(merged["status_id"] == status_id) & (merged["sex"] == sex)]

    hh = sub[sub["cluster_label"] == "HH"]["VAWRI"]
    non_hh = sub[sub["cluster_label"] != "HH"]["VAWRI"]

    if len(hh) < 2:
        log.warning(f"  status={status_id} sex={sex}: only {len(hh)} HH — skipping")
        return None

    u_stat, p_val = mannwhitneyu(hh, non_hh, alternative="greater")
    r_rb = rank_biserial(u_stat, len(hh), len(non_hh))

    return {
        "status_id": status_id,
        "status_label": STATUS_LABELS[status_id],
        "sex": sex,
        "n_hh": len(hh),
        "n_non_hh": len(non_hh),
        "mean_hh": hh.mean(),
        "mean_non_hh": non_hh.mean(),
        "median_hh": hh.median(),
        "median_non_hh": non_hh.median(),
        "iqr_hh": iqr_str(hh),
        "iqr_non_hh": iqr_str(non_hh),
        "U": u_stat,
        "p": p_val,
        "r_rb": r_rb,
    }


# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------
def main():
    log.info("=== Script 16: VAWRI external validation (June 2023) ===")

    # --- Load VAWRI --------------------------------------------------------
    log.info("Loading VAWRI Mexico 2023...")
    vawri = pd.read_csv(VAWRI_FILE)
    # Zero-pad CVE_INEGI to 5 digits → matches LISA cvegeo
    vawri["cvegeo"] = vawri["CVE_INEGI"].astype(str).str.zfill(5)
    vawri = vawri[["cvegeo", "VAWRI"]].copy()
    log.info(f"  VAWRI: {len(vawri)} municipalities, range {vawri['VAWRI'].min():.3f}–{vawri['VAWRI'].max():.3f}")

    # --- Load LISA June 2023 -----------------------------------------------
    log.info(f"Loading LISA cross-section: {LISA_YEAR}-{LISA_MONTH:02d}...")
    lisa = pl.read_parquet(LISA_FILE)
    lisa_jun23 = (
        lisa.filter(
            (pl.col("year") == LISA_YEAR) & (pl.col("month") == LISA_MONTH)
        )
        .to_pandas()
    )
    log.info(f"  LISA June 2023: {len(lisa_jun23)} rows")

    n_lisa_munis = lisa_jun23["cvegeo"].nunique()
    log.info(f"  Unique LISA municipalities: {n_lisa_munis}")

    # --- Join --------------------------------------------------------------
    merged = lisa_jun23.merge(vawri, on="cvegeo", how="inner")
    n_joined = merged["cvegeo"].nunique()
    n_vawri = vawri["cvegeo"].nunique()
    n_miss_vawri = n_lisa_munis - n_joined
    log.info(f"  Joined: {n_joined} municipalities ({n_miss_vawri} LISA munis missing from VAWRI)")

    # --- Tests: total sex, all 4 statuses ----------------------------------
    results = []
    log.info("Running Mann-Whitney U tests (total sex, all statuses)...")
    total_merged = merged[merged["sex"] == "total"]
    for sid in [0, 7, 2, 3]:
        r = run_test(total_merged, sid, "total")
        if r:
            results.append(r)
            log.info(
                f"  {r['status_label']:>16s}: n_HH={r['n_hh']:3d}  "
                f"median HH={r['median_hh']:.3f} vs {r['median_non_hh']:.3f}  "
                f"U={r['U']:.0f}  p={r['p']:.2e}  r_rb={r['r_rb']:.3f}"
            )

    # --- Tests: sex-disaggregated for status 7 and 3 ----------------------
    log.info("Running Mann-Whitney U tests (sex-disaggregated, status 7 & 3)...")
    for sid in [7, 3]:
        for sex in ["male", "female"]:
            r = run_test(merged, sid, sex)
            if r:
                results.append(r)
                log.info(
                    f"  {r['status_label']:>16s} ({sex:6s}): n_HH={r['n_hh']:3d}  "
                    f"median HH={r['median_hh']:.3f} vs {r['median_non_hh']:.3f}  "
                    f"U={r['U']:.0f}  p={r['p']:.2e}  r_rb={r['r_rb']:.3f}"
                )

    # --- Build report ------------------------------------------------------
    log.info("Writing report...")
    lines = [
        "# 11 — VAWRI External Validation (June 2023 LISA Cross-Section)",
        "",
        "## Dataset",
        "",
        f"- **VAWRI source:** VAWRI Mexico 2023 (Violence Against Women Risk Index)",
        f"- **VAWRI municipalities:** {n_vawri}",
        f"- **VAWRI range:** {vawri['VAWRI'].min():.3f}–{vawri['VAWRI'].max():.3f}",
        f"- **VAWRI mean:** {vawri['VAWRI'].mean():.3f}, median: {vawri['VAWRI'].median():.3f}",
        f"- **LISA cross-section:** {LISA_YEAR}-{LISA_MONTH:02d} (temporally matched to VAWRI 2023)",
        f"- **LISA municipalities:** {n_lisa_munis}",
        f"- **Successfully joined:** {n_joined} municipalities",
        f"- **Join key:** CVE_INEGI (zero-padded to 5 digits) → cvegeo",
        "",
        "## Mann-Whitney U Tests: Total Sex, All Statuses",
        "",
        "| Status | N HH | N non-HH | Median HH | IQR HH | Median non-HH | IQR non-HH | U | p-value | r_rb |",
        "|--------|------|----------|-----------|--------|---------------|------------|---|---------|------|",
    ]

    for r in results:
        if r["sex"] != "total":
            continue
        p_str = f"{r['p']:.2e}" if r["p"] > 0 else "<1e-300"
        sig = "*" if r["p"] < 0.001 else ""
        lines.append(
            f"| {r['status_label']} | {r['n_hh']} | {r['n_non_hh']} | "
            f"{r['median_hh']:.3f} | {r['iqr_hh']} | "
            f"{r['median_non_hh']:.3f} | {r['iqr_non_hh']} | "
            f"{r['U']:.0f} | {p_str}{sig} | {r['r_rb']:.3f} |"
        )

    lines += [
        "",
        "## Mann-Whitney U Tests: Sex-Disaggregated (Not Located & Located Dead)",
        "",
        "| Status | Sex | N HH | N non-HH | Median HH | IQR HH | Median non-HH | IQR non-HH | U | p-value | r_rb |",
        "|--------|-----|------|----------|-----------|--------|---------------|------------|---|---------|------|",
    ]

    for r in results:
        if r["sex"] == "total":
            continue
        p_str = f"{r['p']:.2e}" if r["p"] > 0 else "<1e-300"
        sig = "*" if r["p"] < 0.001 else ""
        lines.append(
            f"| {r['status_label']} | {r['sex']} | {r['n_hh']} | {r['n_non_hh']} | "
            f"{r['median_hh']:.3f} | {r['iqr_hh']} | "
            f"{r['median_non_hh']:.3f} | {r['iqr_non_hh']} | "
            f"{r['U']:.0f} | {p_str}{sig} | {r['r_rb']:.3f} |"
        )

    # Effect size interpretation guide
    lines += [
        "",
        "## Effect Size Interpretation",
        "",
        "The rank-biserial correlation (r_rb) is computed as r = 2U₁/(n₁·n₂) − 1, where U₁ is the Mann-Whitney U for the HH group.",
        "Interpretation (following Kerby 2014): |r| < 0.3 small, 0.3–0.5 medium, > 0.5 large.",
        "",
        "## Notes",
        "",
        "- **Temporal alignment:** Both VAWRI composite scores and LISA HH classification reference 2023,",
        "  eliminating the 2-year mismatch in the prior analysis (which used June 2025 LISA).",
        "- **Test directionality:** One-sided (greater), testing whether HH municipalities have higher VAWRI.",
        f"- **LISA parameters:** Queen contiguity, 999 permutations, α = 0.05.",
    ]

    OUTPUT_MD.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_MD.write_text("\n".join(lines) + "\n")
    log.info(f"Report written to {OUTPUT_MD}")
    log.info("Script 16 complete.")


if __name__ == "__main__":
    main()
