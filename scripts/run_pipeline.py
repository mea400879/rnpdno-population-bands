"""Monthly RNPDNO pipeline orchestrator.

Runs scripts 10–15 in sequence. Skips phases whose outputs already exist
unless --force is passed.

Usage:
    conda run -n rnpdno_eda python scripts/run_pipeline.py            # skip done phases
    conda run -n rnpdno_eda python scripts/run_pipeline.py --force    # rerun everything
    conda run -n rnpdno_eda python scripts/run_pipeline.py --from 3   # start from phase N
"""

import sys
import subprocess
import logging
import argparse
from pathlib import Path
from datetime import datetime

ROOT      = Path(__file__).resolve().parent.parent
DATA_PROC = ROOT / "data" / "processed"
LOGS_DIR  = ROOT / "logs"
LOGS_DIR.mkdir(exist_ok=True)

# ---------------------------------------------------------------------------
# Phases: (name, script, output_sentinel_files)
# ---------------------------------------------------------------------------
PHASES = [
    (
        1, "Panel construction",
        "scripts/10_build_monthly_panel.py",
        [DATA_PROC / "panel_monthly_counts.parquet"],
    ),
    (
        1, "Spatial weights",
        "scripts/11_build_spatial_weights.py",
        [DATA_PROC / "spatial_weights_queen.gal"],
    ),
    (
        2, "Monthly LISA",
        "scripts/12_compute_lisa_monthly.py",
        [
            DATA_PROC / "lisa_monthly_results.parquet",
            DATA_PROC / "morans_i_monthly.csv",
            DATA_PROC / "hh_clusters_monthly.parquet",
        ],
    ),
    (
        2, "Concentration metrics",
        "scripts/13_compute_concentration.py",
        [
            DATA_PROC / "concentration_monthly.csv",
            DATA_PROC / "hh_regional_composition.csv",
            DATA_PROC / "hh_cross_tabulation_latest.csv",
        ],
    ),
    (
        3, "Figures",
        "scripts/14_generate_figures.py",
        [ROOT / "manuscript" / "figures" / "fig8_sex_disaggregation_maps.pdf"],
    ),
    (
        4, "Tables",
        "scripts/15_generate_tables.py",
        [ROOT / "manuscript" / "tables" / "table8_sex_hh_counts.tex"],
    ),
]

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
log_file = LOGS_DIR / f"pipeline_run_{datetime.now():%Y%m%d_%H%M%S}.log"
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler(sys.stdout),
    ],
)
log = logging.getLogger(__name__)


def outputs_exist(sentinels: list) -> bool:
    return all(p.exists() for p in sentinels)


def run_script(script: str) -> bool:
    """Run a script via conda and return True on success."""
    cmd = ["conda", "run", "-n", "rnpdno_eda", "python", str(ROOT / script)]
    log.info(f"  Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=str(ROOT))
    return result.returncode == 0


def main():
    parser = argparse.ArgumentParser(description="RNPDNO monthly pipeline")
    parser.add_argument("--force",   action="store_true", help="Rerun all phases")
    parser.add_argument("--from",    dest="from_phase", type=int, default=1,
                        help="Start from phase N (1-4)")
    parser.add_argument("--only",    dest="only_phase", type=int, default=None,
                        help="Run only phase N")
    args = parser.parse_args()

    log.info("=" * 60)
    log.info("RNPDNO Monthly Pipeline")
    log.info(f"Log: {log_file}")
    log.info("=" * 60)

    n_run = 0
    n_skip = 0
    failed = []

    for phase_num, phase_name, script, sentinels in PHASES:
        label = f"Phase {phase_num} — {phase_name}"

        if args.only_phase and phase_num != args.only_phase:
            continue
        if phase_num < args.from_phase:
            log.info(f"[SKIP] {label} (before --from {args.from_phase})")
            n_skip += 1
            continue

        if not args.force and outputs_exist(sentinels):
            log.info(f"[SKIP] {label} — outputs already exist")
            n_skip += 1
            continue

        log.info(f"[RUN]  {label}")
        ok = run_script(script)
        if ok:
            log.info(f"[OK]   {label}")
            n_run += 1
        else:
            log.error(f"[FAIL] {label} — aborting pipeline")
            failed.append(label)
            sys.exit(1)

    log.info("=" * 60)
    log.info(f"Done. Ran {n_run} steps, skipped {n_skip}.")
    if failed:
        log.error(f"Failed: {failed}")
    else:
        log.info("All outputs up to date.")
    log.info("=" * 60)


if __name__ == "__main__":
    main()
