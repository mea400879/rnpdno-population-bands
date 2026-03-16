"""Phase 4 — LaTeX table generation (8 tables).

Each output is a standalone tabular environment (.tex) compilable via
\\input{} inside a document that loads the booktabs package.

Outputs in manuscript/tables/:
  table1_dataset_summary.tex       — rows, persons, temporal coverage by status
  table2_summary_statistics.tex    — distribution of monthly case counts per status
  table3_concentration_metrics.tex — Gini + HHI ranges and trends by status
  table4_lisa_classification.tex   — LISA cluster label counts, Dec 2024
  table5_hh_cross_tabulation.tex   — pairwise HH overlap across statuses, Dec 2024
  table6_regional_composition.tex  — HH municipalities by region, Dec 2015 vs Dec 2024
  table7_trend_slopes.tex          — OLS trend slopes by region × status
  table8_sex_hh_counts.tex         — HH counts by sex × status, Dec 2024
"""

import sys
import logging
from pathlib import Path

import numpy as np
import polars as pl
from scipy import stats as ss

# ---------------------------------------------------------------------------
# CONFIG
# ---------------------------------------------------------------------------
ROOT      = Path(__file__).resolve().parent.parent
DATA_RAW  = ROOT / "data" / "raw"
DATA_PROC = ROOT / "data" / "processed"
OUT_DIR   = ROOT / "manuscript" / "tables"
LOGS_DIR  = ROOT / "logs"

OUT_DIR.mkdir(parents=True, exist_ok=True)

RAW_FILES = {
    0: DATA_RAW / "rnpdno_total.csv",
    7: DATA_RAW / "rnpdno_disappeared_not_located.csv",
    2: DATA_RAW / "rnpdno_located_alive.csv",
    3: DATA_RAW / "rnpdno_located_dead.csv",
}

STATUS_IDS    = [0, 7, 2, 3]
STATUS_LABELS = {0: "Total", 7: "Not Located", 2: "Located Alive", 3: "Located Dead"}

REGIONS = ["Norte", "Norte-Occidente", "Centro-Norte", "Centro", "Sur", "Bajío"]

XSEC_LATEST = (2024, 12)   # Dec 2024 for all cross-sectional tables (T4, T5, T8)
XSEC_EARLY  = (2015, 12)   # Dec 2015 for temporal comparison (T6, T7)

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
# LaTeX helpers
# ---------------------------------------------------------------------------
def stars(p: float) -> str:
    if p < 0.001: return "***"
    if p < 0.01:  return "**"
    if p < 0.05:  return "*"
    return ""


def fi(x) -> str:
    """Format integer with comma."""
    return f"{int(round(x)):,}"


def ff(x, d=4) -> str:
    """Format float."""
    return f"{x:.{d}f}"


def fp(p: float) -> str:
    """Format p-value."""
    if p < 0.001: return "$<$0.001"
    return ff(p, 3)


def tex_row(*cells) -> str:
    return "  " + " & ".join(str(c) for c in cells) + r" \\"


def write_tex(path: Path, body: str, note: str = ""):
    with open(path, "w") as f:
        f.write(body)
        if note:
            f.write(f"\n% NOTE: {note}\n")
    log.info(f"  Saved {path.name}")


# ---------------------------------------------------------------------------
# Sentinel mask (applied to raw CSVs)
# ---------------------------------------------------------------------------
def sentinel_mask_expr():
    return (pl.col("cvegeo") == 99998) | (pl.col("cvegeo") % 1000).is_in([998, 999])


# ---------------------------------------------------------------------------
# TABLE 1: Dataset summary by status
# ---------------------------------------------------------------------------
def make_table1():
    log.info("Table 1: dataset summary...")
    rows_data = []
    for sid in STATUS_IDS:
        raw = pl.read_csv(RAW_FILES[sid])
        n_raw_rows   = len(raw)
        n_sent_rows  = raw.filter(sentinel_mask_expr()).shape[0]
        n_valid_rows = n_raw_rows - n_sent_rows

        total_persons  = int(raw["total"].sum())
        sent_persons   = int(raw.filter(sentinel_mask_expr())["total"].sum())
        valid_persons  = total_persons - sent_persons

        rows_data.append((sid, n_raw_rows, n_valid_rows, n_sent_rows,
                          total_persons, valid_persons, sent_persons))

    lines = [
        r"\begin{tabular}{lrrrrrr}",
        r"  \toprule",
        tex_row(
            r"\textbf{Status}",
            r"\textbf{CSV rows}",
            r"\textbf{Valid rows}",
            r"\textbf{Sentinel rows}",
            r"\textbf{Total persons}",
            r"\textbf{Valid persons}",
            r"\textbf{Sentinel persons}",
        ),
        r"  \midrule",
    ]
    for sid, n_raw, n_val, n_sent, tp, vp, sp in rows_data:
        lines.append(tex_row(
            STATUS_LABELS[sid],
            fi(n_raw), fi(n_val), fi(n_sent),
            fi(tp), fi(vp), fi(sp),
        ))
    lines += [
        r"  \bottomrule",
        r"  \multicolumn{7}{l}{\footnotesize Temporal coverage: January 2015 -- December 2025.} \\",
        r"  \multicolumn{7}{l}{\footnotesize Sentinel geocodes (cvegeo ending 998/999 or equal to 99998) excluded from all spatial analyses.} \\",
        r"\end{tabular}",
    ]
    write_tex(OUT_DIR / "table1_dataset_summary.tex", "\n".join(lines))


# ---------------------------------------------------------------------------
# TABLE 2: Summary statistics by status
# ---------------------------------------------------------------------------
def make_table2(panel: pl.DataFrame):
    log.info("Table 2: summary statistics...")

    lines = [
        r"\begin{tabular}{lrrrrrrrrr}",
        r"  \toprule",
        tex_row(
            r"\textbf{Status}",
            r"\textbf{N}$^a$",
            r"\textbf{Total}",
            r"\textbf{Mean}",
            r"\textbf{SD}",
            r"\textbf{Median}",
            r"\textbf{P75}",
            r"\textbf{P95}",
            r"\textbf{Max}",
            r"\textbf{Skew}",
        ),
        r"  \midrule",
    ]

    for sid in STATUS_IDS:
        sub = panel.filter(pl.col("status_id") == sid)["total"].to_numpy().astype(float)
        non_zero = sub[sub > 0]
        skew = float(ss.skew(sub))
        lines.append(tex_row(
            STATUS_LABELS[sid],
            fi(len(non_zero)),
            fi(sub.sum()),
            ff(non_zero.mean() if len(non_zero) > 0 else 0, 2),
            ff(non_zero.std()  if len(non_zero) > 0 else 0, 2),
            ff(np.median(non_zero) if len(non_zero) > 0 else 0, 1),
            ff(np.percentile(sub, 75), 1),
            ff(np.percentile(sub, 95), 1),
            fi(sub.max()),
            ff(skew, 2),
        ))

    lines += [
        r"  \bottomrule",
        r"  \multicolumn{10}{l}{\footnotesize $^a$Non-zero municipality-months only. Unit of observation: municipality $\times$ month.} \\",
        r"  \multicolumn{10}{l}{\footnotesize N = 2{,}478 municipalities $\times$ 132 months. P75/P95 computed over all municipality-months including zeros.} \\",
        r"\end{tabular}",
    ]
    write_tex(OUT_DIR / "table2_summary_statistics.tex", "\n".join(lines))


# ---------------------------------------------------------------------------
# TABLE 3: Concentration metrics by status
# ---------------------------------------------------------------------------
def make_table3(conc: pl.DataFrame):
    log.info("Table 3: concentration metrics...")

    lines = [
        r"\begin{tabular}{lrrrrrrrr}",
        r"  \toprule",
        r"  & \multicolumn{4}{c}{\textbf{Gini}} & \multicolumn{4}{c}{\textbf{HHI}} \\",
        r"  \cmidrule(lr){2-5}\cmidrule(lr){6-9}",
        tex_row(
            r"\textbf{Status}",
            r"\textbf{Mean}", r"\textbf{Min}", r"\textbf{Max}", r"\textbf{Trend}$^a$",
            r"\textbf{Mean}", r"\textbf{Min}", r"\textbf{Max}", r"\textbf{Trend}$^a$",
        ),
        r"  \midrule",
    ]

    for sid in STATUS_IDS:
        sub = conc.filter(pl.col("status_id") == sid).sort(["year", "month"])
        g = sub["gini"].to_numpy()
        h = sub["hhi"].to_numpy()
        n = len(g)
        x = np.arange(n)

        g_sl = ss.linregress(x, g)
        h_sl = ss.linregress(x, h)

        # Trend per year = slope × 12
        g_trend = f"{g_sl.slope*12:.4f}{stars(g_sl.pvalue)}"
        h_trend = f"{h_sl.slope*12:.4f}{stars(h_sl.pvalue)}"

        lines.append(tex_row(
            STATUS_LABELS[sid],
            ff(g.mean(), 4), ff(g.min(), 4), ff(g.max(), 4), g_trend,
            ff(h.mean(), 4), ff(h.min(), 4), ff(h.max(), 4), h_trend,
        ))

    lines += [
        r"  \bottomrule",
        r"  \multicolumn{9}{l}{\footnotesize $^a$OLS trend slope per year ($\times$12), 132 monthly observations. $^{***}p<0.001$, $^{**}p<0.01$, $^{*}p<0.05$.} \\",
        r"\end{tabular}",
    ]
    write_tex(OUT_DIR / "table3_concentration_metrics.tex", "\n".join(lines))


# ---------------------------------------------------------------------------
# TABLE 4: LISA classification counts by status (Dec 2024)
# ---------------------------------------------------------------------------
def make_table4(lisa: pl.DataFrame):
    log.info("Table 4: LISA classification counts (Dec 2024)...")

    y, mo = XSEC_LATEST
    sub = lisa.filter(
        (pl.col("year")  == y) &
        (pl.col("month") == mo) &
        (pl.col("sex")   == "total")
    )

    LABELS = ["HH", "LL", "HL", "LH", "NS"]

    lines = [
        r"\begin{tabular}{lrrrrrr}",
        r"  \toprule",
        tex_row(
            r"\textbf{Status}",
            r"\textbf{HH}", r"\textbf{LL}", r"\textbf{HL}", r"\textbf{LH}",
            r"\textbf{NS}", r"\textbf{Total}",
        ),
        r"  \midrule",
    ]

    for sid in STATUS_IDS:
        s = sub.filter(pl.col("status_id") == sid)
        counts = {lbl: int(s.filter(pl.col("cluster_label") == lbl).shape[0]) for lbl in LABELS}
        total  = sum(counts.values())
        lines.append(tex_row(
            STATUS_LABELS[sid],
            fi(counts["HH"]), fi(counts["LL"]), fi(counts["HL"]), fi(counts["LH"]),
            fi(counts["NS"]), fi(total),
        ))

    lines += [
        r"  \bottomrule",
        r"  \multicolumn{7}{l}{\footnotesize LISA classification: Queen contiguity, 999 permutations, $\alpha=0.05$. Reference period: December 2024.} \\",
        r"  \multicolumn{7}{l}{\footnotesize HH = High-High, LL = Low-Low, HL = High-Low, LH = Low-High, NS = Not Significant.} \\",
        r"\end{tabular}",
    ]
    write_tex(OUT_DIR / "table4_lisa_classification.tex", "\n".join(lines))


# ---------------------------------------------------------------------------
# TABLE 5: Pairwise HH overlap across statuses (Dec 2024)
# ---------------------------------------------------------------------------
def make_table5(lisa: pl.DataFrame):
    log.info("Table 5: HH cross-tabulation (Dec 2024)...")

    y, mo = XSEC_LATEST
    sub = lisa.filter(
        (pl.col("year")  == y) &
        (pl.col("month") == mo) &
        (pl.col("sex")   == "total")
    )

    # Build HH sets per status
    hh_sets = {}
    for sid in STATUS_IDS:
        hh_sets[sid] = set(
            sub.filter(
                (pl.col("status_id") == sid) &
                (pl.col("cluster_label") == "HH")
            )["cvegeo"].to_list()
        )

    short = {0: "Total", 7: "Not Loc.", 2: "Located\\,Alive", 3: "Located\\,Dead"}

    header = r"\textbf{}" + "".join(f" & \\textbf{{{short[sid]}}}" for sid in STATUS_IDS) + r" \\"

    lines = [
        r"\begin{tabular}{lrrrr}",
        r"  \toprule",
        "  " + header,
        r"  \midrule",
    ]

    for sid_row in STATUS_IDS:
        cells = [short[sid_row]]
        for sid_col in STATUS_IDS:
            overlap = len(hh_sets[sid_row] & hh_sets[sid_col])
            if sid_row == sid_col:
                cells.append(f"\\textbf{{{fi(overlap)}}}")
            else:
                cells.append(fi(overlap))
        lines.append(tex_row(*cells))

    lines += [
        r"  \bottomrule",
        r"  \multicolumn{5}{l}{\footnotesize Diagonal = total HH municipalities per status. Off-diagonal = pairwise intersection count.} \\",
        r"  \multicolumn{5}{l}{\footnotesize Reference period: December 2024. All counts use total sex LISA ($\alpha=0.05$).} \\",
        r"\end{tabular}",
    ]
    write_tex(OUT_DIR / "table5_hh_cross_tabulation.tex", "\n".join(lines))


# ---------------------------------------------------------------------------
# TABLE 6: Regional composition of HH clusters, Dec 2015 vs Dec 2024
# ---------------------------------------------------------------------------
def make_table6(lisa: pl.DataFrame, muni_meta: pl.DataFrame):
    log.info("Table 6: regional composition (Dec 2015 vs Dec 2024)...")

    def get_hh_regional(y, mo):
        sub = lisa.filter(
            (pl.col("year")  == y) &
            (pl.col("month") == mo) &
            (pl.col("sex")   == "total") &
            (pl.col("cluster_label") == "HH")
        ).join(muni_meta, on="cvegeo", how="left")

        counts = {}
        for reg in ["Norte", "Norte-Occidente", "Centro-Norte", "Centro", "Sur"]:
            counts[reg] = sub.filter(pl.col("region") == reg).group_by("status_id").agg(
                pl.len().alias("n")
            )
        counts["Bajío"] = sub.filter(pl.col("is_bajio") == True).group_by("status_id").agg(
            pl.len().alias("n")
        )
        return counts

    c2015 = get_hh_regional(*XSEC_EARLY)
    c2024 = get_hh_regional(*XSEC_LATEST)

    def lookup(counts_dict, region, sid):
        df = counts_dict.get(region, pl.DataFrame({"status_id": [], "n": []}))
        row = df.filter(pl.col("status_id") == sid)
        return int(row["n"][0]) if len(row) > 0 else 0

    # χ² test: compare distribution across regions for each status (2015 vs 2024)
    def chi2_test(sid):
        regs = ["Norte", "Norte-Occidente", "Centro-Norte", "Centro", "Sur"]
        obs_2015 = [lookup(c2015, r, sid) for r in regs]
        obs_2024 = [lookup(c2024, r, sid) for r in regs]
        contingency = np.array([obs_2015, obs_2024])
        # Only run if enough counts
        if contingency.sum() < 10 or (contingency > 0).sum() < 4:
            return None, None
        try:
            chi2, p, dof, _ = ss.chi2_contingency(contingency)
            return chi2, p
        except Exception:
            return None, None

    short_sid = {0: "Total", 7: "Not Loc.", 2: "Loc. Alive", 3: "Loc. Dead"}

    lines = [
        r"\begin{tabular}{llrrrr}",
        r"  \toprule",
        r"  & & \multicolumn{4}{c}{\textbf{HH Municipalities}} \\",
        r"  \cmidrule(lr){3-6}",
        tex_row(
            r"\textbf{Region}", r"\textbf{Period}",
            *[f"\\textbf{{{short_sid[s]}}}" for s in STATUS_IDS]
        ),
        r"  \midrule",
    ]

    for reg in REGIONS:
        lines.append(tex_row(
            reg, "Dec 2015",
            *[fi(lookup(c2015, reg, sid)) for sid in STATUS_IDS]
        ))
        lines.append(tex_row(
            "", "Dec 2024",
            *[fi(lookup(c2024, reg, sid)) for sid in STATUS_IDS]
        ))
        lines.append(r"  \addlinespace[2pt]")

    # Add χ² row per status
    lines.append(r"  \midrule")
    chi2_row = [r"$\chi^2$ $p$-value", ""]
    for sid in STATUS_IDS:
        chi2_val, pval = chi2_test(sid)
        chi2_row.append(fp(pval) + stars(pval) if pval is not None else "---")
    lines.append(tex_row(*chi2_row))

    lines += [
        r"  \bottomrule",
        r"  \multicolumn{6}{l}{\footnotesize $\chi^2$ tests compare regional distribution of HH municipalities (5 standard regions) between Dec 2015 and Dec 2024.} \\",
        r"  \multicolumn{6}{l}{\footnotesize Baj\'{i}o municipalities (sub-flag) shown separately; not included in $\chi^2$ test.} \\",
        r"  \multicolumn{6}{l}{\footnotesize $^{***}p<0.001$, $^{**}p<0.01$, $^{*}p<0.05$.} \\",
        r"\end{tabular}",
    ]
    write_tex(OUT_DIR / "table6_regional_composition.tex", "\n".join(lines))


# ---------------------------------------------------------------------------
# TABLE 7: OLS trend slopes by region × status
# ---------------------------------------------------------------------------
def make_table7(lisa: pl.DataFrame, muni_meta: pl.DataFrame):
    log.info("Table 7: OLS trend slopes by region × status...")

    hh_all = (
        lisa.filter(
            (pl.col("sex") == "total") &
            (pl.col("cluster_label") == "HH")
        )
        .select(["status_id", "year", "month", "cvegeo"])
        .join(muni_meta, on="cvegeo", how="left")
    )

    year_months = [(y, m) for y in range(2015, 2026) for m in range(1, 13)]
    n_periods = len(year_months)
    ym_index  = {(y, m): i for i, (y, m) in enumerate(year_months)}

    def time_series(sub_df):
        """Count HH munis per period, return aligned array length n_periods."""
        counts = (
            sub_df.group_by(["year", "month"])
            .agg(pl.len().alias("n"))
            .to_pandas()
        )
        arr = np.zeros(n_periods)
        for _, row in counts.iterrows():
            idx = ym_index.get((int(row["year"]), int(row["month"])))
            if idx is not None:
                arr[idx] = row["n"]
        return arr

    def fmt_cell(slope, pval):
        """Format slope (per year) with SE and stars."""
        slope_yr = slope * 12
        return f"{slope_yr:+.2f}{stars(pval)}"

    short_sid = {0: "Total", 7: "Not Located", 2: "Located Alive", 3: "Located Dead"}

    lines = [
        r"\begin{tabular}{lrrrr}",
        r"  \toprule",
        tex_row(
            r"\textbf{Region}",
            *[f"\\textbf{{{short_sid[s]}}}" for s in STATUS_IDS]
        ),
        r"  \midrule",
    ]

    for reg in REGIONS:
        row_cells = [reg]
        for sid in STATUS_IDS:
            if reg == "Bajío":
                sub = hh_all.filter(
                    (pl.col("status_id") == sid) &
                    (pl.col("is_bajio") == True)
                )
            else:
                sub = hh_all.filter(
                    (pl.col("status_id") == sid) &
                    (pl.col("region") == reg)
                )
            arr = time_series(sub)
            if arr.sum() < 3:
                row_cells.append("---")
            else:
                x = np.arange(n_periods, dtype=float)
                sl = ss.linregress(x, arr)
                row_cells.append(fmt_cell(sl.slope, sl.pvalue))
        lines.append(tex_row(*row_cells))

    lines += [
        r"  \bottomrule",
        r"  \multicolumn{5}{l}{\footnotesize OLS slope (municipalities per year $= $ slope $\times 12$), 132 monthly observations.} \\",
        r"  \multicolumn{5}{l}{\footnotesize $^{***}p<0.001$, $^{**}p<0.01$, $^{*}p<0.05$. Sign: positive $=$ growing hotspot region.} \\",
        r"\end{tabular}",
    ]
    write_tex(OUT_DIR / "table7_trend_slopes.tex", "\n".join(lines))


# ---------------------------------------------------------------------------
# TABLE 8: HH counts by sex × status (Dec 2024)
# ---------------------------------------------------------------------------
def make_table8(lisa: pl.DataFrame):
    log.info("Table 8: HH counts by sex × status (Dec 2024)...")

    y, mo = XSEC_LATEST
    sub = lisa.filter(
        (pl.col("year")  == y) &
        (pl.col("month") == mo)
    )

    def hh_set(sid, sx):
        return set(
            sub.filter(
                (pl.col("status_id") == sid) &
                (pl.col("sex")       == sx) &
                (pl.col("cluster_label") == "HH")
            )["cvegeo"].to_list()
        )

    lines = [
        r"\begin{tabular}{lrrrrrr}",
        r"  \toprule",
        tex_row(
            r"\textbf{Status}",
            r"\textbf{Total HH}",
            r"\textbf{Male HH}",
            r"\textbf{Female HH}",
            r"\textbf{M $\cap$ F}",
            r"\textbf{M only}",
            r"\textbf{F only}",
        ),
        r"  \midrule",
    ]

    for sid in STATUS_IDS:
        t_set = hh_set(sid, "total")
        m_set = hh_set(sid, "male")
        f_set = hh_set(sid, "female")
        mf    = m_set & f_set
        m_only = m_set - f_set
        f_only = f_set - m_set
        lines.append(tex_row(
            STATUS_LABELS[sid],
            fi(len(t_set)),
            fi(len(m_set)),
            fi(len(f_set)),
            fi(len(mf)),
            fi(len(m_only)),
            fi(len(f_only)),
        ))

    lines += [
        r"  \bottomrule",
        r"  \multicolumn{7}{l}{\footnotesize Reference period: December 2024. $\alpha=0.05$, Queen contiguity, 999 permutations.} \\",
        r"  \multicolumn{7}{l}{\footnotesize M $\cap$ F = municipalities HH under both male and female LISA. M/F only = sex-exclusive hotspots.} \\",
        r"\end{tabular}",
    ]
    write_tex(OUT_DIR / "table8_sex_hh_counts.tex", "\n".join(lines))


# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------
def main():
    log.info("=== Phase 4: Table generation ===")

    # Load shared inputs
    log.info("Loading data...")
    panel = pl.read_parquet(DATA_PROC / "panel_monthly_counts.parquet")
    conc  = pl.read_csv(DATA_PROC / "concentration_monthly.csv")
    lisa  = pl.read_parquet(DATA_PROC / "lisa_monthly_results.parquet")

    muni_meta = panel.select(["cvegeo", "region", "is_bajio"]).unique("cvegeo")

    # Generate tables
    make_table1()
    make_table2(panel)
    make_table3(conc)
    make_table4(lisa)
    make_table5(lisa)
    make_table6(lisa, muni_meta)
    make_table7(lisa, muni_meta)
    make_table8(lisa)

    log.info("=== Phase 4 complete. Tables written to manuscript/tables/ ===")
    for f in sorted(OUT_DIR.glob("table*.tex")):
        log.info(f"  {f.name}: {f.stat().st_size} bytes")


if __name__ == "__main__":
    main()
