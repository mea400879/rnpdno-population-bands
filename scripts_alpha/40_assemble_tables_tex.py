"""Paper alpha — assemble booktabs tabular .tex fragments, one per table.

Each output is a plain `\\begin{tabular}{...}` fragment with booktabs rules.
No `\\begin{table}` wrapper, no `\\caption`, no `\\label` — the manuscript is
drafted in Word and the captions are authored there. Fragments are dropped
in via pandoc/manual paste.

Floats are formatted per paper-alpha house rules:
    proportions / V / tau : 3dp
    rate ratios + CI      : 2dp as  2.18 [1.91, 2.48]
    chi-squared statistic : 2dp
    p-values              : 0.045 if p >= 0.001; 2.7e-13 if 1e-99 < p < 0.001;
                            <1e-99 if p < 1e-99
    Holm stars            : ***  p<0.001, ** p<0.01, * p<0.05
    counts / populations  : thousands separator

Inputs
------
- data/interim/alpha/alpha_panel_long.parquet
- data/interim/alpha/alpha_cross_sections.parquet
- data/interim/alpha/band_denom.parquet
- data/interim/alpha/band_drift_2015_2025.parquet
- data/interim/alpha/rq1_sex_cross_sections.parquet
- data/interim/alpha/rq1_sex_tests.parquet
- data/interim/alpha/rq2_state_classification.parquet
- data/interim/alpha/rq2_state_metrics.parquet
- data/interim/alpha/rq3_chi2_national.parquet
- data/interim/alpha/rq3_chi2_regional.parquet
- data/interim/alpha/rq3_chi2_bajio.parquet
- data/interim/alpha/rq3_rate_ratios_national.parquet
- data/interim/alpha/rq3_rate_ratios_bajio.parquet
- data/raw/rnpdno_*.csv   (raw scrape; used for T1 row/person counts)

Outputs
-------
- manuscript_alpha/tables/TABLE1_dataset_summary.tex
- manuscript_alpha/tables/TABLE2_rq1_sex_composition.tex
- manuscript_alpha/tables/TABLE3_rq2_state_typology.tex
- manuscript_alpha/tables/TABLE4_rq3_national.tex
- manuscript_alpha/tables/TABLE5_rq3_regional_heatmap.tex
- manuscript_alpha/tables/TABLE6_rq3_bajio29.tex
- manuscript_alpha/tables/TABLE_A1_sentinel_drops.tex
- manuscript_alpha/tables/TABLE_A2_bajio_robustness.tex   (skipped if parquet absent)
- manuscript_alpha/tables/TABLE_A3_band_drift.tex
- reports/alpha/40_assemble_tables_tex.log
"""
from __future__ import annotations

import math
import os
import sys
import traceback
from pathlib import Path

import polars as pl

_REPO = Path(__file__).resolve().parents[1]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from scripts_alpha._utils import (  # noqa: E402
    BAND_ORDER,
    CED_STATES,
    CESOP_REGIONS,
    RQ3_PRIMARY_YEAR_PAIR,
    RQ3_YEAR_PAIRS,
    STATUS_ORDER,
)

REPO = Path(__file__).resolve().parents[1]
INTERIM_ALPHA = REPO / "data" / "interim" / "alpha"
RAW = REPO / "data" / "raw"
TABLES_OUT = REPO / "manuscript_alpha" / "tables"
REPORTS_ALPHA = REPO / "reports" / "alpha"
LOG_OUT = REPORTS_ALPHA / "40_assemble_tables_tex.log"

SKIP_TA2 = os.environ.get("SKIP_TA2", "").lower() in ("1", "true", "yes")
BAJIO_200MUNI_PARQUET = INTERIM_ALPHA / "rq3_chi2_bajio_200muni.parquet"

BAND_LABEL: dict[str, str] = {
    "community":   "Community",
    "rural":       "Rural",
    "semi_urban":  "Semi-urban",
    "small_city":  "Small city",
    "medium_city": "Medium city",
    "city":        "City",
    "large_city":  "Large city",
}

STATUS_LABEL: dict[str, str] = {
    "not_located":   "Not located",
    "located_alive": "Located alive",
    "located_dead":  "Located dead",
}
STATUS_ID: dict[str, int] = {
    "not_located":   7,
    "located_alive": 2,
    "located_dead":  3,
}

LATEX_SPECIALS: tuple[str, ...] = ("&", "%", "_", "$", "#", "{", "}")


# ---------------------------------------------------------------------------
# formatting helpers
# ---------------------------------------------------------------------------

def latex_escape(s: str) -> str:
    """Escape LaTeX specials in a plain string. Intended for data cells."""
    if s is None:
        return ""
    out = s
    out = out.replace("\\", r"\textbackslash{}")
    for ch in ("&", "%", "_", "$", "#"):
        out = out.replace(ch, "\\" + ch)
    out = out.replace("{", r"\{").replace("}", r"\}")
    return out


def count_escape_hits(s: str) -> int:
    if s is None:
        return 0
    return sum(s.count(ch) for ch in LATEX_SPECIALS)


def fmt_int(x) -> str:
    if x is None or (isinstance(x, float) and math.isnan(x)):
        return "--"
    return f"{int(x):,}"


def fmt_prop(x, nd: int = 3) -> str:
    if x is None or (isinstance(x, float) and math.isnan(x)):
        return "--"
    return f"{x:.{nd}f}"


def fmt_chi2(x) -> str:
    if x is None or (isinstance(x, float) and math.isnan(x)):
        return "--"
    return f"{x:.2f}"


def fmt_p(p) -> str:
    if p is None or (isinstance(p, float) and math.isnan(p)):
        return "--"
    if p < 1e-99:
        return "$<$1e$-$99"
    if p >= 0.001:
        return f"{p:.3f}"
    mantissa, exp = f"{p:.1e}".split("e")
    exp = int(exp)
    return f"{mantissa}e{exp:+d}"


def stars(p) -> str:
    if p is None or (isinstance(p, float) and math.isnan(p)):
        return ""
    if p < 0.001:
        return "***"
    if p < 0.01:
        return "**"
    if p < 0.05:
        return "*"
    return ""


def fmt_p_holm(p) -> str:
    s = fmt_p(p)
    st = stars(p)
    return s + st if st else s


def fmt_rr(rr, lo, hi) -> str:
    """Rate ratio with 95% CI as  2.18 [1.91, 2.48]. NaN / undefined -> --."""
    if rr is None or (isinstance(rr, float) and math.isnan(rr)):
        return "--"
    if lo is None or (isinstance(lo, float) and math.isnan(lo)):
        return f"{rr:.2f} [--, --]"
    return f"{rr:.2f} [{lo:.2f}, {hi:.2f}]"


def fmt_signed(x, nd: int = 3) -> str:
    if x is None or (isinstance(x, float) and math.isnan(x)):
        return "--"
    sign = "+" if x >= 0 else ""
    return f"{sign}{x:.{nd}f}"


def fmt_dof(d) -> str:
    if d is None or (isinstance(d, float) and math.isnan(d)):
        return "MC"
    return f"{int(d)}"


def fmt_test(t: str) -> str:
    return {"chi2": "chi2", "chi2_mc": "chi2 (MC)",
            "fisher_freeman_halton": "FFH"}.get(t, t or "--")


def write_tex(path: Path, body: str) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not body.endswith("\n"):
        body += "\n"
    path.write_text(body, encoding="utf-8")
    return body.count("\n")


# ---------------------------------------------------------------------------
# T1 — dataset summary
# ---------------------------------------------------------------------------

def build_t1() -> tuple[str, dict]:
    raw_paths = {
        "not_located":   RAW / "rnpdno_disappeared_not_located.csv",
        "located_alive": RAW / "rnpdno_located_alive.csv",
        "located_dead":  RAW / "rnpdno_located_dead.csv",
    }
    raw_stats: dict[str, tuple[int, int]] = {}
    sentinel_stats: dict[str, tuple[int, int]] = {}
    for st, p in raw_paths.items():
        df = pl.read_csv(p).with_columns(
            pl.col("cvegeo").cast(pl.Utf8).str.zfill(5)
        )
        raw_stats[st] = (df.height, int(df["total"].sum()))
        is_sentinel = (
            pl.col("cvegeo").str.ends_with("998")
            | pl.col("cvegeo").str.ends_with("999")
        )
        sdf = df.filter(is_sentinel)
        sentinel_stats[st] = (sdf.height, int(sdf["total"].sum()))

    panel = pl.read_parquet(INTERIM_ALPHA / "alpha_panel_long.parquet")
    panel_grp = (
        panel.group_by("status").agg(
            pl.len().alias("rows"),
            pl.col("total").sum().alias("persons"),
        )
    )
    analytical: dict[str, tuple[int, int]] = {}
    for row in panel_grp.iter_rows(named=True):
        analytical[row["status"]] = (int(row["rows"]), int(row["persons"]))

    lines: list[str] = []
    lines.append(r"\begin{tabular}{lrrrrrrr}")
    lines.append(r"\toprule")
    lines.append(
        r"Stratum & ID & Raw rows & Raw persons & Sentinel rows "
        r"& Sentinel persons & Analytical rows & Analytical persons \\"
    )
    lines.append(r"\midrule")
    row_order = ["not_located", "located_alive", "located_dead"]
    raw_rows_sum = raw_persons_sum = 0
    sent_rows_sum = sent_persons_sum = 0
    ana_rows_sum = ana_persons_sum = 0
    for st in row_order:
        rr, rp = raw_stats[st]
        sr, sp = sentinel_stats[st]
        ar, ap = analytical.get(st, (0, 0))
        raw_rows_sum += rr
        raw_persons_sum += rp
        sent_rows_sum += sr
        sent_persons_sum += sp
        ana_rows_sum += ar
        ana_persons_sum += ap
        lines.append(
            f"{STATUS_LABEL[st]} & {STATUS_ID[st]} & {fmt_int(rr)} & {fmt_int(rp)} "
            f"& {fmt_int(sr)} & {fmt_int(sp)} & {fmt_int(ar)} & {fmt_int(ap)} \\\\"
        )
    lines.append(r"\midrule")
    total_df = pl.read_csv(RAW / "rnpdno_total.csv")
    tot_rows = total_df.height
    tot_persons = int(total_df["total"].sum())
    lines.append(
        f"Grand total (ID 0) & 0 & {fmt_int(tot_rows)} & {fmt_int(tot_persons)} "
        r"& -- & -- & -- & -- \\"
    )
    lines.append(
        f"All three outcomes combined & -- & {fmt_int(raw_rows_sum)} "
        f"& {fmt_int(raw_persons_sum)} & {fmt_int(sent_rows_sum)} "
        f"& {fmt_int(sent_persons_sum)} & {fmt_int(ana_rows_sum)} "
        f"& {fmt_int(ana_persons_sum)} \\\\"
    )
    lines.append(r"\bottomrule")
    lines.append(r"\end{tabular}")
    pct_drift = abs(tot_persons - raw_persons_sum) / tot_persons * 100
    note = (
        "%\n"
        "% Note: Grand total (ID 0) is DiB's pre-split aggregate. The three outcome\n"
        f"% strata sum to {raw_persons_sum:,} persons, within {pct_drift:.2f}\\%\n"
        "% of the grand total (documented timing noise from non-atomic scrape).\n"
        "% Analytical universe: 2,478 munis (INEGI MGN via AGEEML 2025-12-12).\n"
        "% Effective sample: 2,475 munis after excluding 3 post-2020 splits without\n"
        "% CONAPO projections (24059 Villa de Pozos, 25019 Eldorado, 25020 Juan Jose Rios).\n"
    )
    body = "\n".join(lines) + "\n" + note
    return body, {"n_rows": 5, "n_cols": 8}


# ---------------------------------------------------------------------------
# T2 — RQ1 sex composition cross-sections
# ---------------------------------------------------------------------------

def build_t2() -> tuple[str, dict]:
    xs = pl.read_parquet(INTERIM_ALPHA / "rq1_sex_cross_sections.parquet")
    tests = pl.read_parquet(INTERIM_ALPHA / "rq1_sex_tests.parquet")

    parity = tests.filter(pl.col("test") == "binom_vs_parity").select([
        "status", "year_a", "p_holm"
    ]).rename({"year_a": "year", "p_holm": "p_holm_parity"})
    parity = parity.with_columns(pl.col("year").cast(pl.Int32))

    delta = tests.filter(pl.col("test") == "prop_2015_vs_2025").select([
        "status", "p_holm",
    ]).rename({"p_holm": "p_holm_delta"})

    xs = xs.join(parity, on=["status", "year"], how="left")
    share_2015 = xs.filter(pl.col("year") == 2015).select([
        "status", pl.col("female_share_of_sexed").alias("fsos_2015")
    ])
    xs = xs.join(share_2015, on="status", how="left").join(
        delta, on="status", how="left"
    )

    lines: list[str] = []
    lines.append(r"\begin{tabular}{llrrrrrccccl}")
    lines.append(r"\toprule")
    lines.append(
        r"Year & Outcome & $n$ & $n_f$ & $n_m$ & $n_u$ & \% undef. & FSoS "
        r"& 95\% CI & $H_0$: $p$=0.5 & 2015$\to$2025 $\Delta$ & \\"
    )
    lines.append(r"\midrule")
    n_rows = 0
    for i, st in enumerate(STATUS_ORDER):
        sub = xs.filter(pl.col("status") == st).sort("year")
        for r in sub.iter_rows(named=True):
            yr = int(r["year"])
            fsos = r["female_share_of_sexed"]
            ci = f"[{r['wilson_lo']:.3f}, {r['wilson_hi']:.3f}]"
            pct_u = r["pct_undefined"] * 100
            p_par = fmt_p_holm(r["p_holm_parity"])
            if yr == 2025:
                d_val = r["female_share_of_sexed"] - r["fsos_2015"]
                d_p = r["p_holm_delta"]
                d_cell = f"{fmt_signed(d_val, 3)}{stars(d_p)}"
            else:
                d_cell = ""
            lines.append(
                f"{yr} & {STATUS_LABEL[st]} & {fmt_int(r['n_total'])} "
                f"& {fmt_int(r['n_female'])} & {fmt_int(r['n_male'])} "
                f"& {fmt_int(r['n_undefined'])} & {pct_u:.2f} "
                f"& {fmt_prop(fsos, 3)} & {ci} & {p_par} & {d_cell} & \\\\"
            )
            n_rows += 1
        if i < len(STATUS_ORDER) - 1:
            lines.append(r"\addlinespace")
    lines.append(r"\bottomrule")
    lines.append(r"\end{tabular}")
    body = "\n".join(lines)
    return body, {"n_rows": n_rows, "n_cols": 11}


# ---------------------------------------------------------------------------
# T3 — RQ2 state typology
# ---------------------------------------------------------------------------

def build_t3() -> tuple[str, dict]:
    clsf = pl.read_parquet(INTERIM_ALPHA / "rq2_state_classification.parquet")
    mets = pl.read_parquet(INTERIM_ALPHA / "rq2_state_metrics.parquet")

    nl_mets = mets.filter(pl.col("status") == "not_located").select([
        "cve_ent", "baseline", "current", "sen_slope_per_year",
        "sen_ci_lo_yr", "sen_ci_hi_yr", "peak_year",
    ])

    tbl = clsf.join(nl_mets, on="cve_ent", how="left")

    order_names = [
        "Nuevo Leon", "Edo. de Mexico", "Guanajuato", "Jalisco",
        "Veracruz", "Coahuila", "Nayarit", "Tabasco",
    ]
    known = {n for (_c, n, _r) in CED_STATES}
    for nm in order_names:
        if nm not in known:
            raise ValueError(f"T3 order name {nm!r} not in CED_STATES")

    audit = 0

    lines: list[str] = []
    lines.append(r"\begin{tabular}{llllrrrrrlr}")
    lines.append(r"\toprule")
    lines.append(
        r"State & Region & Class & Fem.-anom. & Mean mo. NL & 2015 baseline "
        r"& 2025 current & Curr/Base & NL $\tau$ "
        r"& Sen slope/yr [95\% CI] & Peak yr \\"
    )
    lines.append(r"\midrule")
    n_rows = 0
    for nm in order_names:
        r = tbl.filter(pl.col("nom_ent") == nm).row(0, named=True)
        state_cell = latex_escape(r["nom_ent"])
        region_cell = latex_escape(r["region"])
        class_cell = latex_escape(r["trajectory_class"])
        audit += (
            count_escape_hits(r["nom_ent"])
            + count_escape_hits(r["region"])
            + count_escape_hits(r["trajectory_class"])
        )
        fa = r"$\checkmark$" if r["female_anomalous"] else ""
        slope_cell = (
            f"{r['sen_slope_per_year']:.2f} "
            f"[{r['sen_ci_lo_yr']:.2f}, {r['sen_ci_hi_yr']:.2f}]"
        )
        lines.append(
            f"{state_cell} & {region_cell} & {class_cell} & {fa} "
            f"& {r['mean_monthly_nl']:.2f} & {r['baseline']:.2f} "
            f"& {r['current']:.2f} & {r['curr_over_base_nl']:.3f} "
            f"& {fmt_prop(r['mk_tau_nl'], 3)} & {slope_cell} "
            f"& {int(r['peak_year'])} \\\\"
        )
        n_rows += 1
    lines.append(r"\bottomrule")
    lines.append(r"\end{tabular}")
    body = "\n".join(lines)
    return body, {"n_rows": n_rows, "n_cols": 11, "escape_hits": audit}


# ---------------------------------------------------------------------------
# T4 — RQ3 national chi2 + rate ratios (two tabulars in one file)
# ---------------------------------------------------------------------------

def build_t4() -> tuple[str, dict]:
    chi = pl.read_parquet(INTERIM_ALPHA / "rq3_chi2_national.parquet")
    rr = pl.read_parquet(INTERIM_ALPHA / "rq3_rate_ratios_national.parquet")

    yr_a, yr_b = RQ3_PRIMARY_YEAR_PAIR
    chi = chi.filter((pl.col("year_a") == yr_a) & (pl.col("year_b") == yr_b))
    rr = rr.filter((pl.col("year_a") == yr_a) & (pl.col("year_b") == yr_b))

    panel_a: list[str] = []
    panel_a.append(r"% Panel A - Chi-squared tests (2015 vs 2025)")
    panel_a.append(r"\begin{tabular}{lrrrrlrll}")
    panel_a.append(r"\toprule")
    panel_a.append(
        r"Outcome & $n_{2015}$ & $n_{2025}$ & $\chi^2$ & dof "
        r"& $p_\mathrm{Holm}$ & Cramer's $V$ & Size & Test \\"
    )
    panel_a.append(r"\midrule")
    n_rows_a = 0
    for st in STATUS_ORDER:
        r = chi.filter(pl.col("status") == st).row(0, named=True)
        panel_a.append(
            f"{STATUS_LABEL[st]} & {fmt_int(r['n_a'])} & {fmt_int(r['n_b'])} "
            f"& {fmt_chi2(r['chi2'])} & {fmt_dof(r['dof'])} "
            f"& {fmt_p_holm(r['p_holm'])} & {fmt_prop(r['cramer_v'], 3)} "
            f"& {r['cramer_v_interp']} & {fmt_test(r['test_used'])} \\\\"
        )
        n_rows_a += 1
    panel_a.append(r"\bottomrule")
    panel_a.append(r"\end{tabular}")

    panel_b: list[str] = []
    panel_b.append(r"% Panel B - Rate ratios 2015 to 2025 by band")
    panel_b.append(r"\begin{tabular}{lrrr}")
    panel_b.append(r"\toprule")
    panel_b.append(
        r"Band & NL RR [95\% CI] & LA RR [95\% CI] & LD RR [95\% CI] \\"
    )
    panel_b.append(r"\midrule")
    n_rows_b = 0
    for band in BAND_ORDER:
        cells = [BAND_LABEL[band]]
        for st in ("not_located", "located_alive", "located_dead"):
            r = rr.filter(
                (pl.col("status") == st) & (pl.col("band_2020") == band)
            )
            if r.height == 0:
                cells.append("--")
            else:
                rrow = r.row(0, named=True)
                cells.append(
                    fmt_rr(rrow["rate_ratio"], rrow["ci_lo"], rrow["ci_hi"])
                )
        panel_b.append(" & ".join(cells) + r" \\")
        n_rows_b += 1
    panel_b.append(r"\bottomrule")
    panel_b.append(r"\end{tabular}")

    body = "\n".join(panel_a) + "\n\\vspace{0.5em}\n\n" + "\n".join(panel_b) + "\n"
    return body, {"n_rows": n_rows_a + n_rows_b, "n_cols": "9 + 4"}


# ---------------------------------------------------------------------------
# T5 — RQ3 regional heatmap
# ---------------------------------------------------------------------------

def build_t5() -> tuple[str, dict]:
    chi = pl.read_parquet(INTERIM_ALPHA / "rq3_chi2_regional.parquet")
    yr_a, yr_b = RQ3_PRIMARY_YEAR_PAIR
    chi = chi.filter((pl.col("year_a") == yr_a) & (pl.col("year_b") == yr_b))

    lines: list[str] = []
    lines.append(r"\begin{tabular}{lllllll}")
    lines.append(r"\toprule")
    lines.append(
        r"Region & NL $V$ & NL sig. & LA $V$ & LA sig. & LD $V$ & LD sig. \\"
    )
    lines.append(r"\midrule")
    audit = 0
    for region in CESOP_REGIONS:
        cells = [latex_escape(region)]
        audit += count_escape_hits(region)
        for st in ("not_located", "located_alive", "located_dead"):
            sub = chi.filter(
                (pl.col("region") == region) & (pl.col("status") == st)
            )
            if sub.height == 0:
                cells.extend(["--", "--"])
                continue
            r = sub.row(0, named=True)
            v = fmt_prop(r["cramer_v"], 3)
            st_mark = stars(r["p_holm"]) or "(ns)"
            cells.append(v)
            cells.append(st_mark)
        lines.append(" & ".join(cells) + r" \\")
    lines.append(r"\bottomrule")
    lines.append(r"\end{tabular}")
    footer = (
        "%\n"
        r"% Cells with V<0.10 negligible, 0.10-0.30 small, "
        r"0.30-0.50 medium, >0.50 large (Cohen heuristic)."
        "\n"
    )
    body = "\n".join(lines) + "\n" + footer
    return body, {"n_rows": len(CESOP_REGIONS), "n_cols": 7,
                  "escape_hits": audit}


# ---------------------------------------------------------------------------
# T6 — RQ3 Bajio-29
# ---------------------------------------------------------------------------

def build_t6() -> tuple[str, dict]:
    chi = pl.read_parquet(INTERIM_ALPHA / "rq3_chi2_bajio.parquet")
    rr = pl.read_parquet(INTERIM_ALPHA / "rq3_rate_ratios_bajio.parquet")

    lines: list[str] = []
    lines.append(r"\begin{tabular}{llrrrrlll}")
    lines.append(r"\toprule")
    lines.append(
        r"Year pair & Outcome & $n_a$ & $n_b$ & $\chi^2$ & dof "
        r"& $p_\mathrm{Holm}$ & $V$ & Test \\"
    )
    lines.append(r"\midrule")
    n_rows = 0
    for i, (yr_a, yr_b) in enumerate(RQ3_YEAR_PAIRS):
        for st in STATUS_ORDER:
            sub = chi.filter(
                (pl.col("year_a") == yr_a)
                & (pl.col("year_b") == yr_b)
                & (pl.col("status") == st)
            )
            if sub.height == 0:
                continue
            r = sub.row(0, named=True)
            lines.append(
                f"{yr_a}$\\to${yr_b} & {STATUS_LABEL[st]} "
                f"& {fmt_int(r['n_a'])} & {fmt_int(r['n_b'])} "
                f"& {fmt_chi2(r['chi2'])} & {fmt_dof(r['dof'])} "
                f"& {fmt_p_holm(r['p_holm'])} & {fmt_prop(r['cramer_v'], 3)} "
                f"& {fmt_test(r['test_used'])} \\\\"
            )
            n_rows += 1
        if i < len(RQ3_YEAR_PAIRS) - 1:
            lines.append(r"\addlinespace")
    lines.append(r"\bottomrule")
    lines.append(r"\end{tabular}")

    mc = rr.filter(
        (pl.col("year_a") == 2015)
        & (pl.col("year_b") == 2025)
        & (pl.col("status") == "not_located")
        & (pl.col("band_2020") == "medium_city")
    )
    if mc.height:
        m = mc.row(0, named=True)
        footer = (
            "%\n"
            "% Medium-city NL rate ratio (Bajio-29, "
            f"2015$\\to$2025): {fmt_rr(m['rate_ratio'], m['ci_lo'], m['ci_hi'])}."
            "\n"
        )
    else:
        footer = "%\n% Medium-city NL rate ratio unavailable.\n"

    body = "\n".join(lines) + "\n" + footer
    return body, {"n_rows": n_rows, "n_cols": 9}


# ---------------------------------------------------------------------------
# TA1 — sentinel drops
# ---------------------------------------------------------------------------

def build_ta1() -> tuple[str, dict]:
    paths = {
        "not_located":   RAW / "rnpdno_disappeared_not_located.csv",
        "located_alive": RAW / "rnpdno_located_alive.csv",
        "located_dead":  RAW / "rnpdno_located_dead.csv",
    }
    parts = []
    for st, p in paths.items():
        df = pl.read_csv(p).with_columns(
            pl.col("cvegeo").cast(pl.Utf8).str.zfill(5)
        ).with_columns(pl.lit(st).alias("status"))
        df = df.filter(
            pl.col("cvegeo").str.ends_with("998")
            | pl.col("cvegeo").str.ends_with("999")
        )
        parts.append(df)
    sent = pl.concat(parts, how="vertical_relaxed")

    cat_expr = (
        pl.when(pl.col("cvegeo") == "99998").then(pl.lit("99998"))
          .when(pl.col("cvegeo") == "99999").then(pl.lit("99999"))
          .when(pl.col("cvegeo").str.ends_with("998")).then(pl.lit("XX998"))
          .when(pl.col("cvegeo").str.ends_with("999")).then(pl.lit("XX999"))
          .otherwise(pl.lit("OTHER"))
          .alias("sent_cat")
    )
    sent = sent.with_columns(cat_expr)

    agg = (
        sent.group_by(["sent_cat", "status"])
        .agg(
            pl.len().alias("rows"),
            pl.col("total").sum().alias("persons"),
        )
    )

    meaning = {
        "99998": r"Unknown state (id\_estado=33)",
        "99999": "Unresolved state",
        "XX998": "No municipal reference",
        "XX999": "Municipality unknown",
    }
    cat_order = ["99998", "99999", "XX998", "XX999"]

    lines: list[str] = []
    lines.append(r"\begin{tabular}{llrrrrrrrr}")
    lines.append(r"\toprule")
    lines.append(
        r"Code & Meaning & NL rows & NL persons & LA rows & LA persons "
        r"& LD rows & LD persons & Total rows & Total persons \\"
    )
    lines.append(r"\midrule")
    n_rows = 0
    for cat in cat_order:
        cells = [cat, meaning[cat]]
        tot_r = tot_p = 0
        for st in ("not_located", "located_alive", "located_dead"):
            sub = agg.filter(
                (pl.col("sent_cat") == cat) & (pl.col("status") == st)
            )
            if sub.height == 0:
                rr_c = pp_c = 0
            else:
                r = sub.row(0, named=True)
                rr_c = int(r["rows"])
                pp_c = int(r["persons"])
            cells.extend([fmt_int(rr_c), fmt_int(pp_c)])
            tot_r += rr_c
            tot_p += pp_c
        cells.extend([fmt_int(tot_r), fmt_int(tot_p)])
        lines.append(" & ".join(cells) + r" \\")
        n_rows += 1
    lines.append(r"\bottomrule")
    lines.append(r"\end{tabular}")
    body = "\n".join(lines)
    return body, {"n_rows": n_rows, "n_cols": 10,
                  "source_rows": sent.height}


# ---------------------------------------------------------------------------
# TA2 — 200-muni Bajio robustness (may be skipped)
# ---------------------------------------------------------------------------

def build_ta2():
    if SKIP_TA2 or not BAJIO_200MUNI_PARQUET.exists():
        return None
    chi29 = pl.read_parquet(INTERIM_ALPHA / "rq3_chi2_bajio.parquet")
    chi200 = pl.read_parquet(BAJIO_200MUNI_PARQUET)

    lines: list[str] = []
    lines.append(r"\begin{tabular}{llrrrrl}")
    lines.append(r"\toprule")
    lines.append(
        r"Year pair & Outcome & 29-muni $V$ & 29-muni $p_\mathrm{Holm}$ "
        r"& 200-muni $V$ & 200-muni $p_\mathrm{Holm}$ & $\Delta V$ \\"
    )
    lines.append(r"\midrule")
    n_rows = 0
    for yr_a, yr_b in RQ3_YEAR_PAIRS:
        for st in STATUS_ORDER:
            a = chi29.filter(
                (pl.col("year_a") == yr_a)
                & (pl.col("year_b") == yr_b)
                & (pl.col("status") == st)
            )
            b = chi200.filter(
                (pl.col("year_a") == yr_a)
                & (pl.col("year_b") == yr_b)
                & (pl.col("status") == st)
            )
            if a.height == 0 or b.height == 0:
                continue
            ar = a.row(0, named=True)
            br = b.row(0, named=True)
            dv = ar["cramer_v"] - br["cramer_v"]
            lines.append(
                f"{yr_a}$\\to${yr_b} & {STATUS_LABEL[st]} "
                f"& {fmt_prop(ar['cramer_v'], 3)} & {fmt_p_holm(ar['p_holm'])} "
                f"& {fmt_prop(br['cramer_v'], 3)} & {fmt_p_holm(br['p_holm'])} "
                f"& {fmt_signed(dv, 3)} \\\\"
            )
            n_rows += 1
    lines.append(r"\bottomrule")
    lines.append(r"\end{tabular}")
    body = "\n".join(lines)
    return body, {"n_rows": n_rows, "n_cols": 7}


# ---------------------------------------------------------------------------
# TA3 — band drift
# ---------------------------------------------------------------------------

def build_ta3() -> tuple[str, dict]:
    drift = pl.read_parquet(INTERIM_ALPHA / "band_drift_2015_2025.parquet")
    n_total = drift.height
    n_drifters = drift.filter(pl.col("band_2015") != pl.col("band_2025")).height
    trans = (
        drift.filter(pl.col("band_2015") != pl.col("band_2025"))
        .group_by(["band_2015", "band_2025"])
        .agg(pl.len().alias("n_munis"))
        .with_columns(
            pl.col("band_2015").cast(pl.Utf8),
            pl.col("band_2025").cast(pl.Utf8),
        )
    )
    band_idx = {b: i for i, b in enumerate(BAND_ORDER)}
    rows = trans.to_dicts()
    rows.sort(key=lambda r: (band_idx[r["band_2015"]], band_idx[r["band_2025"]]))

    lines: list[str] = []
    lines.append(r"\begin{tabular}{llr}")
    lines.append(r"\toprule")
    lines.append(r"From band & To band & $n$ munis \\")
    lines.append(r"\midrule")
    for r in rows:
        lines.append(
            f"{BAND_LABEL[r['band_2015']]} & {BAND_LABEL[r['band_2025']]} "
            f"& {fmt_int(r['n_munis'])} \\\\"
        )
    lines.append(r"\bottomrule")
    lines.append(r"\end{tabular}")
    pct = n_drifters / n_total * 100
    note = (
        "%\n"
        f"% {n_drifters:,} of {n_total:,} munis drift band between 2015 and 2025 "
        f"({pct:.1f}\\%); all transitions are between adjacent bands.\n"
    )
    body = "\n".join(lines) + "\n" + note
    return body, {"n_rows": len(rows), "n_cols": 3,
                  "n_drifters": n_drifters, "n_total": n_total}


# ---------------------------------------------------------------------------
# driver
# ---------------------------------------------------------------------------

def main() -> None:
    log_lines: list[str] = []

    def log(msg: str = "") -> None:
        log_lines.append(msg)

    TABLES_OUT.mkdir(parents=True, exist_ok=True)

    log("=" * 72)
    log("[40] assemble_tables_tex - booktabs tabular fragments, QA log")
    log("=" * 72)

    produced: list[str] = []
    skipped: list[str] = []

    def emit(path: Path, body: str, label: str, meta: dict) -> None:
        nline = write_tex(path, body)
        produced.append(label)
        first3 = "\n".join(body.splitlines()[:3])
        log("")
        log(f"-- {label} --> {path.relative_to(REPO)}")
        log(f"   lines = {nline}, rows = {meta.get('n_rows', '?')}, "
            f"cols = {meta.get('n_cols', '?')}")
        log("   first 3 lines:")
        for ln in first3.splitlines():
            log(f"     | {ln}")
        esc = meta.get("escape_hits", 0)
        log(f"   latex-escape hits in data cells: {esc}")

    body, meta = build_t1()
    emit(TABLES_OUT / "TABLE1_dataset_summary.tex", body, "T1", meta)

    body, meta = build_t2()
    emit(TABLES_OUT / "TABLE2_rq1_sex_composition.tex", body, "T2", meta)

    body, meta = build_t3()
    emit(TABLES_OUT / "TABLE3_rq2_state_typology.tex", body, "T3", meta)

    body, meta = build_t4()
    emit(TABLES_OUT / "TABLE4_rq3_national.tex", body, "T4", meta)

    body, meta = build_t5()
    emit(TABLES_OUT / "TABLE5_rq3_regional_heatmap.tex", body, "T5", meta)

    body, meta = build_t6()
    emit(TABLES_OUT / "TABLE6_rq3_bajio29.tex", body, "T6", meta)

    body, meta = build_ta1()
    emit(TABLES_OUT / "TABLE_A1_sentinel_drops.tex", body, "TA1", meta)

    ta2 = build_ta2()
    if ta2 is None:
        log("")
        log("-- TA2 --> SKIPPED: "
            f"{BAJIO_200MUNI_PARQUET.relative_to(REPO)} not present "
            "(SKIP_TA2 honored or 200-muni parquet missing)")
        skipped.append("TA2")
    else:
        body, meta = ta2
        emit(TABLES_OUT / "TABLE_A2_bajio_robustness.tex", body, "TA2", meta)

    body, meta = build_ta3()
    emit(TABLES_OUT / "TABLE_A3_band_drift.tex", body, "TA3", meta)

    log("")
    log("=" * 72)
    log(f"produced: {', '.join(produced)}")
    log(f"skipped:  {', '.join(skipped) if skipped else '(none)'}")
    log("=" * 72)

    REPORTS_ALPHA.mkdir(parents=True, exist_ok=True)
    LOG_OUT.write_text("\n".join(log_lines) + "\n", encoding="utf-8")
    print("\n".join(log_lines))

    n_main = sum(1 for t in produced if not t.startswith("TA"))
    n_appx = sum(1 for t in produced if t.startswith("TA"))
    skip_str = ", ".join(skipped) if skipped else "none"
    print("")
    print(
        f"[40] done. Main tables: {n_main}/6. "
        f"Appendix tables: {n_appx}/3 (skipped: {skip_str}). Awaiting review."
    )


if __name__ == "__main__":
    try:
        main()
    except Exception:
        traceback.print_exc()
        sys.exit(1)
