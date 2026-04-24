"""Paper alpha — publication figures (FIG1-FIG7).

Each figure is saved as PDF and SVG in manuscript_alpha/figures/. All text
is serif, grayscale-safe, 300 DPI on save.

Inputs are the interim parquets produced by scripts 00/10/20/21/22/23.
No new statistics are computed here — all figures are visualizations of
pre-computed quantities.
"""
from __future__ import annotations

import sys
import traceback
from pathlib import Path

import matplotlib
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
import polars as pl
from matplotlib.ticker import FuncFormatter

_REPO = Path(__file__).resolve().parents[1]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from scripts_alpha._utils import (  # noqa: E402
    BAJIO_29_CVEGEOS,
    BAND_DISPLAY,
    BAND_ORDER,
    CED_STATES,  # noqa: F401 - public contract
    CESOP_REGIONS,  # noqa: F401 - public contract
    FIGURE_DPI,
    FIGURE_FONT_FAMILY,
    OUTCOME_COLOR,
    OUTCOME_DISPLAY,
    RQ3_PRIMARY_YEAR_PAIR,
    STATUS_ORDER,
)

plt.rcParams.update({
    "font.family": FIGURE_FONT_FAMILY,
    "font.size": 9,
    "axes.titlesize": 10,
    "axes.labelsize": 9,
    "xtick.labelsize": 8,
    "ytick.labelsize": 8,
    "legend.fontsize": 8,
    "figure.dpi": 100,
    "savefig.dpi": FIGURE_DPI,
    "savefig.bbox": "tight",
    "savefig.pad_inches": 0.05,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.grid": True,
    "grid.alpha": 0.3,
    "grid.linestyle": "--",
})

REPO = Path(__file__).resolve().parents[1]
INTERIM_ALPHA = REPO / "data" / "interim" / "alpha"
FIGS_OUT = REPO / "manuscript_alpha" / "figures"
REPORTS_ALPHA = REPO / "reports" / "alpha"
LOG_OUT = REPORTS_ALPHA / "30_figures.log"

YEARS = list(range(2015, 2026))
N_MONTHS = len(YEARS) * 12  # 132

# CED temporal windows (from reports/paper1_verification/10_ced_alignment.md).
# Inclusive year bounds of the Article-34 CED declaration window.
CED_WINDOWS: dict[int, tuple[int, int]] = {
    19: (2015, 2025),  # Nuevo Leon
    15: (2015, 2025),  # Edo. de Mexico
    11: (2017, 2025),  # Guanajuato
    14: (2015, 2025),  # Jalisco
    30: (2015, 2016),  # Veracruz
    5:  (2015, 2016),  # Coahuila
    18: (2015, 2017),  # Nayarit
    27: (2024, 2025),  # Tabasco
}

# FIG3 panel order (row-major 4x2).
FIG3_ORDER = [19, 15, 11, 14, 30, 5, 18, 27]

# Discretized viridis palette for 7 bands — shared by FIG4 and FIG7 so
# band identity is visually consistent across figures.
_BAND_CMAP = plt.get_cmap("viridis", len(BAND_ORDER))
BAND_COLOR: dict[str, tuple[float, float, float, float]] = {
    b: _BAND_CMAP(i) for i, b in enumerate(BAND_ORDER)
}


def month_index(year: int, month: int) -> int:
    """0-based month index since Jan 2015."""
    return (year - YEARS[0]) * 12 + (month - 1)


def rolling12(x: np.ndarray) -> np.ndarray:
    """12-month trailing rolling sum. Output length == input length."""
    out = np.empty_like(x, dtype=np.float64)
    cum = np.concatenate(([0.0], np.cumsum(x, dtype=np.float64)))
    for i in range(len(x)):
        lo = max(0, i - 11)
        out[i] = cum[i + 1] - cum[lo]
    return out


def save_both(fig: plt.Figure, stem: str) -> tuple[Path, Path]:
    pdf = FIGS_OUT / f"{stem}.pdf"
    svg = FIGS_OUT / f"{stem}.svg"
    fig.savefig(pdf)
    fig.savefig(svg)
    plt.close(fig)
    return pdf, svg


def year_gridlines(ax) -> None:
    for y_idx in range(1, len(YEARS)):
        ax.axvline(y_idx * 12, color="gray", lw=0.4, alpha=0.5)


def year_ticks(ax) -> None:
    ticks = [i * 12 for i in range(len(YEARS))]
    labels = [str(y) for y in YEARS]
    ax.set_xticks(ticks)
    ax.set_xticklabels(labels)


# ---------------------------------------------------------------------------
# FIG1
# ---------------------------------------------------------------------------

def fig1() -> tuple[Path, Path, dict]:
    panel = pl.read_parquet(INTERIM_ALPHA / "alpha_panel_long.parquet")
    agg = (
        panel.group_by(["year", "month", "status"])
        .agg(pl.col("total").sum().alias("n"))
        .sort(["status", "year", "month"])
    )

    fig, ax = plt.subplots(figsize=(7, 4))
    year_gridlines(ax)
    for st in STATUS_ORDER:
        sub = agg.filter(pl.col("status") == st).sort(["year", "month"])
        x = np.array([month_index(r["year"], r["month"])
                      for r in sub.iter_rows(named=True)])
        y = sub["n"].to_numpy()
        ax.plot(x, y, color=OUTCOME_COLOR[st],
                label=OUTCOME_DISPLAY[st], lw=1.3)

    year_ticks(ax)
    ax.set_xlabel("Month")
    ax.set_ylabel("Monthly registrations")
    ax.set_xlim(-1, N_MONTHS)
    ax.legend(loc="upper left", frameon=False)
    ax.set_title(
        "Figure 1. National monthly RNPDNO registrations by outcome, 2015-2025."
    )

    # Data-integrity: annual totals should equal rq3_band_counts_national sums.
    cs = pl.read_parquet(INTERIM_ALPHA / "rq3_band_counts_national.parquet")
    checks: list[dict] = []
    for yr in (2015, 2019, 2025):
        for st in STATUS_ORDER:
            a = int(agg.filter(
                (pl.col("year") == yr) & (pl.col("status") == st)
            )["n"].sum())
            b = int(cs.filter(
                (pl.col("year") == yr) & (pl.col("status") == st)
            )["n_cases"].sum())
            checks.append({"year": yr, "status": st,
                           "fig1_sum": a, "cross_section": b, "ok": a == b})

    pdf, svg = save_both(fig, "FIG1_national_monthly")
    return pdf, svg, {"dims": (7, 4), "subplots": 1, "checks": checks}


# ---------------------------------------------------------------------------
# FIG2
# ---------------------------------------------------------------------------

def fig2() -> tuple[Path, Path, dict]:
    monthly = pl.read_parquet(INTERIM_ALPHA / "rq1_sex_monthly.parquet")
    la = monthly.filter(pl.col("status") == "located_alive") \
        .sort(["year", "month"])
    x = np.arange(la.height)
    y = la["female_share_of_sexed"].to_numpy()
    pad = np.concatenate((np.full(11, np.nan), y))
    roll = np.array([np.nanmean(pad[i:i + 12]) for i in range(len(y))])

    xs = pl.read_parquet(INTERIM_ALPHA / "rq1_sex_cross_sections.parquet")
    la_xs = xs.filter(pl.col("status") == "located_alive").sort("year")
    annot = {int(r["year"]): float(r["female_share_of_sexed"])
             for r in la_xs.iter_rows(named=True)}

    fig, ax = plt.subplots(figsize=(7, 4))
    year_gridlines(ax)
    ax.plot(x, y, color=OUTCOME_COLOR["located_alive"], lw=0.9, alpha=0.55,
            label="Monthly FSoS")
    ax.plot(x, roll, color=OUTCOME_COLOR["located_alive"], lw=2.0,
            label="12-month rolling mean")
    ax.axhline(0.5, color="gray", lw=1.0, alpha=0.9, label="Parity (0.50)")

    for yr in (2015, 2019, 2025):
        if yr in annot:
            xi = month_index(yr, 1)
            ax.axvline(xi, color="black", lw=0.8, ls="--", alpha=0.6)
            ax.annotate(
                f"{yr}: FSoS = {annot[yr]:.3f}",
                xy=(xi, 0.68), xytext=(xi + 1, 0.68),
                ha="left", va="top", fontsize=7,
            )

    year_ticks(ax)
    ax.set_xlabel("Month")
    ax.set_ylabel("Female share (female / (female + male))")
    ax.set_ylim(0.30, 0.70)
    ax.set_xlim(-1, N_MONTHS)
    ax.legend(loc="lower left", frameon=False)
    ax.set_title(
        "Figure 2. Female share of sexed Located-Alive registrations, "
        "monthly and 12-mo rolling mean, 2015-2025."
    )
    pdf, svg = save_both(fig, "FIG2_la_parity_crossing")
    return pdf, svg, {"dims": (7, 4), "subplots": 1, "fsos_annot": annot}


# ---------------------------------------------------------------------------
# FIG3
# ---------------------------------------------------------------------------

def fig3() -> tuple[Path, Path, dict]:
    monthly = pl.read_parquet(INTERIM_ALPHA / "rq2_state_monthly_8ced.parquet")
    nl = monthly.filter(pl.col("status") == "not_located")
    clsf = pl.read_parquet(INTERIM_ALPHA / "rq2_state_classification.parquet")
    mets = pl.read_parquet(INTERIM_ALPHA / "rq2_state_metrics.parquet") \
        .filter(pl.col("status") == "not_located")

    clsf_by = {int(r["cve_ent"]): r for r in clsf.iter_rows(named=True)}
    peak_by = {int(r["cve_ent"]): (int(r["peak_year"]), int(r["peak_month"]))
               for r in mets.iter_rows(named=True)}

    fig, axes = plt.subplots(4, 2, figsize=(9, 7), sharex=True)
    panel_titles: list[str] = []
    for idx, cve_ent in enumerate(FIG3_ORDER):
        ax = axes[idx // 2, idx % 2]
        sub = nl.filter(pl.col("cve_ent") == cve_ent).sort(["year", "month"])
        x = np.arange(sub.height)
        y12 = rolling12(sub["total"].to_numpy().astype(np.float64))
        ax.plot(x, y12, color=OUTCOME_COLOR["not_located"], lw=1.4)

        meta = clsf_by[cve_ent]
        fa_marker = " *" if meta["female_anomalous"] else ""
        title = f"{meta['nom_ent']}: {meta['trajectory_class']}{fa_marker}"
        panel_titles.append(title)
        ax.set_title(title, loc="left")

        y0, y1 = CED_WINDOWS[cve_ent]
        x_lo = month_index(y0, 1)
        x_hi = month_index(y1, 12)
        ax.axvspan(x_lo, x_hi, color="gray", alpha=0.15, lw=0)

        py, pm = peak_by[cve_ent]
        xi = month_index(py, pm)
        ax.axvline(xi, color="black", lw=0.7, ls=":", alpha=0.7)
        ax.annotate(f"peak {py}",
                    xy=(xi, 0.95), xycoords=("data", "axes fraction"),
                    xytext=(3, -2), textcoords="offset points",
                    va="top", ha="left", fontsize=7)

    for ax in axes[-1, :]:
        year_ticks(ax)
        ax.set_xlabel("Month")
    for ax in axes[:, 0]:
        ax.set_ylabel("NL cases (12-mo sum)")

    fig.suptitle(
        "Figure 3. State-level Not-Located trajectories for the 8 CED "
        "Article-34 states, 12-month rolling sum, 2015-2025.",
        fontsize=10,
    )
    handles = [
        mpatches.Patch(color="gray", alpha=0.15,
                       label="CED declaration window"),
        plt.Line2D([0], [0], color="black", ls=":", lw=0.7,
                   label="peak month"),
    ]
    fig.legend(handles=handles, loc="lower center",
               bbox_to_anchor=(0.5, -0.03), ncol=2, frameon=False)
    fig.subplots_adjust(hspace=0.55, wspace=0.25, top=0.92, bottom=0.10)

    pdf, svg = save_both(fig, "FIG3_state_trajectories")
    return pdf, svg, {"dims": (9, 7), "subplots": 8,
                      "panel_titles": panel_titles}


# ---------------------------------------------------------------------------
# FIG4
# ---------------------------------------------------------------------------

def fig4() -> tuple[Path, Path, dict]:
    counts = pl.read_parquet(INTERIM_ALPHA / "rq3_band_counts_national.parquet")
    totals = (
        counts.group_by(["year", "status"])
        .agg(pl.col("n_cases").sum().alias("grand_total"))
    )
    counts = counts.join(totals, on=["year", "status"], how="left") \
        .with_columns((pl.col("n_cases") / pl.col("grand_total")).alias("share"))

    fig, axes = plt.subplots(1, 3, figsize=(9, 4), sharey=True)
    years = [2015, 2025]
    for i, st in enumerate(STATUS_ORDER):
        ax = axes[i]
        y_positions = [1, 0]
        for yi, yr in enumerate(years):
            left = 0.0
            for band in BAND_ORDER:
                r = counts.filter(
                    (pl.col("year") == yr)
                    & (pl.col("status") == st)
                    & (pl.col("band_2020") == band)
                )
                share = float(r["share"][0]) if r.height else 0.0
                ax.barh(y_positions[yi], share, left=left,
                        color=BAND_COLOR[band], edgecolor="white", lw=0.5)
                left += share
        ax.set_yticks([1, 0])
        ax.set_yticklabels(["2015", "2025"])
        ax.set_xlim(0, 1)
        ax.set_xlabel("Share of registrations")
        ax.set_title(OUTCOME_DISPLAY[st])
        ax.grid(False, axis="y")

    handles = [mpatches.Patch(color=BAND_COLOR[b], label=BAND_DISPLAY[b])
               for b in BAND_ORDER]
    fig.legend(handles=handles, loc="lower center",
               bbox_to_anchor=(0.5, -0.08), ncol=4, frameon=False)
    fig.suptitle(
        "Figure 4. Population-band composition of RNPDNO registrations, "
        "2015 vs 2025.",
        fontsize=10,
    )
    fig.subplots_adjust(top=0.85, bottom=0.28)

    pdf, svg = save_both(fig, "FIG4_band_composition")
    return pdf, svg, {"dims": (9, 4), "subplots": 3}


# ---------------------------------------------------------------------------
# FIG5
# ---------------------------------------------------------------------------

def fig5() -> tuple[Path, Path, dict]:
    rr = pl.read_parquet(INTERIM_ALPHA / "rq3_rate_ratios_national.parquet")
    yr_a, yr_b = RQ3_PRIMARY_YEAR_PAIR
    rr = rr.filter((pl.col("year_a") == yr_a) & (pl.col("year_b") == yr_b))

    outcome_order = ["located_dead", "located_alive", "not_located"]

    y_positions: dict[tuple[str, str], int] = {}
    ytick_positions: list[int] = []
    labels: list[str] = []
    outcome_centers: list[tuple[float, str]] = []

    cur_y = 0
    for st in outcome_order:
        start_y = cur_y
        for band in BAND_ORDER:
            y_positions[(st, band)] = cur_y
            labels.append(BAND_DISPLAY[band])
            ytick_positions.append(cur_y)
            cur_y -= 1
        end_y = cur_y + 1
        outcome_centers.append(((start_y + end_y) / 2, OUTCOME_DISPLAY[st]))
        cur_y -= 1  # 1-slot gap between outcome groups

    fig, ax = plt.subplots(figsize=(8, 6))
    ax.axvline(1.0, color="gray", lw=1.0, alpha=0.7)

    for st in outcome_order:
        for band in BAND_ORDER:
            sub = rr.filter(
                (pl.col("status") == st) & (pl.col("band_2020") == band)
            )
            if sub.height == 0:
                continue
            r = sub.row(0, named=True)
            y = y_positions[(st, band)]
            if not r["rate_ratio_defined"]:
                ax.text(1.0, y, "n.a.", ha="center", va="center", fontsize=7,
                        color="gray")
                continue
            ax.errorbar(
                r["rate_ratio"], y,
                xerr=[[max(1e-3, r["rate_ratio"] - r["ci_lo"])],
                      [max(1e-3, r["ci_hi"] - r["rate_ratio"])]],
                fmt="o", color=OUTCOME_COLOR[st],
                ecolor=OUTCOME_COLOR[st], elinewidth=1.2, capsize=2,
                markersize=4,
            )

    for i in range(len(outcome_order) - 1):
        # separator halfway through each 1-slot gap
        sep_y = -(i + 1) * 8 + 0.5
        ax.axhline(sep_y, color="black", lw=0.3, alpha=0.4)

    ax.set_xscale("log")
    ax.set_xlim(0.1, 10)
    ax.set_xticks([0.1, 0.5, 1, 2, 5, 10])
    ax.get_xaxis().set_major_formatter(FuncFormatter(lambda v, _: f"{v:g}"))
    ax.set_yticks(ytick_positions)
    ax.set_yticklabels(labels)
    ax.set_ylim(cur_y + 1 - 0.5, 0.5)
    ax.set_xlabel("Rate ratio 2015 -> 2025 (log scale)")
    ax.grid(True, axis="x", alpha=0.3, ls="--")
    ax.grid(False, axis="y")

    secax = ax.twinx()
    secax.set_ylim(ax.get_ylim())
    secax.set_yticks([c for c, _ in outcome_centers])
    secax.set_yticklabels([t for _, t in outcome_centers])
    secax.tick_params(axis="y", length=0, pad=2)
    secax.spines["right"].set_visible(False)
    secax.spines["top"].set_visible(False)
    secax.grid(False)

    ax.set_title(
        "Figure 5. Rate-ratio 2015->2025 by population band and outcome, "
        "with 95% Poisson CIs."
    )
    pdf, svg = save_both(fig, "FIG5_rate_ratio_forest")
    return pdf, svg, {"dims": (8, 6), "subplots": 1}


# ---------------------------------------------------------------------------
# FIG6
# ---------------------------------------------------------------------------

def fig6() -> tuple[Path, Path, dict]:
    chi = pl.read_parquet(INTERIM_ALPHA / "rq3_chi2_regional.parquet")
    yr_a, yr_b = RQ3_PRIMARY_YEAR_PAIR
    chi = chi.filter((pl.col("year_a") == yr_a) & (pl.col("year_b") == yr_b))

    regions = ["Norte", "Norte-Occidente", "Centro-Norte", "Centro", "Sur"]
    outcomes = ["not_located", "located_alive", "located_dead"]
    V = np.full((len(regions), len(outcomes)), np.nan)
    P = np.full((len(regions), len(outcomes)), np.nan)
    for i, reg in enumerate(regions):
        for j, st in enumerate(outcomes):
            sub = chi.filter(
                (pl.col("region") == reg) & (pl.col("status") == st)
            )
            if sub.height:
                V[i, j] = float(sub["cramer_v"][0])
                P[i, j] = float(sub["p_holm"][0])

    fig, ax = plt.subplots(figsize=(5, 4))
    ax.grid(False)
    im = ax.imshow(V, cmap="viridis", vmin=0.0, vmax=0.5, aspect="auto")
    ax.set_xticks(range(len(outcomes)))
    ax.set_xticklabels([OUTCOME_DISPLAY[s] for s in outcomes])
    ax.set_yticks(range(len(regions)))
    ax.set_yticklabels(regions)
    ax.set_xlabel("Outcome")
    ax.set_ylabel("CESOP region")

    for i in range(len(regions)):
        for j in range(len(outcomes)):
            v = V[i, j]
            p = P[i, j]
            if np.isnan(v):
                continue
            if p < 0.001:
                suffix = "***"
            elif p < 0.01:
                suffix = "**"
            elif p < 0.05:
                suffix = "*"
            else:
                suffix = " (ns)"
            txt_color = "white" if v > 0.25 else "black"
            ax.text(j, i, f"{v:.3f}{suffix}",
                    ha="center", va="center", color=txt_color, fontsize=8)

    cbar = fig.colorbar(im, ax=ax, shrink=0.85)
    cbar.set_label("Cramer's V")
    ax.set_title(
        "Figure 6. Regional band-composition effect sizes (Cramer's V), "
        "2015 vs 2025, by CESOP region and outcome.",
        fontsize=9,
    )
    pdf, svg = save_both(fig, "FIG6_regional_v_heatmap")
    return pdf, svg, {"dims": (5, 4), "subplots": 1,
                      "V_matrix": V.tolist(), "regions": regions,
                      "outcomes": outcomes}


# ---------------------------------------------------------------------------
# FIG7
# ---------------------------------------------------------------------------

def fig7() -> tuple[Path, Path, dict]:
    panel = pl.read_parquet(INTERIM_ALPHA / "alpha_panel_long.parquet")
    denom = pl.read_parquet(INTERIM_ALPHA / "band_denom.parquet") \
        .select(["cve_geo", "band_2020"]) \
        .with_columns(pl.col("band_2020").cast(pl.Utf8))

    bajio = panel.filter(
        pl.col("cve_geo").is_in(BAJIO_29_CVEGEOS)
        & (pl.col("status") == "not_located")
    ).join(denom, on="cve_geo", how="left")
    agg = (
        bajio.group_by(["year", "month", "band_2020"])
        .agg(pl.col("total").sum().alias("n"))
        .sort(["band_2020", "year", "month"])
    )

    fig, ax = plt.subplots(figsize=(8, 5))
    year_gridlines(ax)
    bands_plot = ["medium_city", "city", "large_city"]
    for band in bands_plot:
        sub = agg.filter(pl.col("band_2020") == band).sort(["year", "month"])
        grid = (
            pl.DataFrame({"year": YEARS}, schema={"year": pl.Int64})
            .join(pl.DataFrame({"month": list(range(1, 13))},
                               schema={"month": pl.Int64}), how="cross")
            .join(sub.select(["year", "month", "n"]),
                  on=["year", "month"], how="left")
            .with_columns(pl.col("n").fill_null(0))
            .sort(["year", "month"])
        )
        y = rolling12(grid["n"].to_numpy().astype(np.float64))
        x = np.arange(len(y))
        ax.plot(x, y, color=BAND_COLOR[band], lw=1.6,
                label=BAND_DISPLAY[band])

    rr = pl.read_parquet(INTERIM_ALPHA / "rq3_rate_ratios_bajio.parquet")
    mc = rr.filter(
        (pl.col("year_a") == 2015)
        & (pl.col("year_b") == 2025)
        & (pl.col("status") == "not_located")
        & (pl.col("band_2020") == "medium_city")
    )
    if mc.height:
        m = mc.row(0, named=True)
        txt = (f"Medium-city NL RR(2015->2025) = {m['rate_ratio']:.2f} "
               f"[{m['ci_lo']:.2f}, {m['ci_hi']:.2f}]")
        ax.text(0.02, 0.03, txt, transform=ax.transAxes, fontsize=8,
                va="bottom", ha="left",
                bbox=dict(facecolor="white", edgecolor="gray", alpha=0.85,
                          pad=4))

    year_ticks(ax)
    ax.set_xlabel("Month")
    ax.set_ylabel("NL cases (12-mo rolling sum)")
    ax.set_xlim(-1, N_MONTHS)
    ax.legend(loc="upper left", frameon=False)
    ax.set_title(
        "Figure 7. Bajio-29 industrial corridor: monthly Not-Located "
        "registrations by urban band, 12-mo rolling sum, 2015-2025."
    )
    pdf, svg = save_both(fig, "FIG7_bajio29_band_trajectories")
    return pdf, svg, {"dims": (8, 5), "subplots": 1}


# ---------------------------------------------------------------------------
# driver
# ---------------------------------------------------------------------------

def main() -> None:
    FIGS_OUT.mkdir(parents=True, exist_ok=True)
    REPORTS_ALPHA.mkdir(parents=True, exist_ok=True)

    log_lines: list[str] = []

    def log(msg: str = "") -> None:
        log_lines.append(msg)

    log("=" * 72)
    log("[30] figures - 7 publication figures, QA log")
    log("=" * 72)

    from matplotlib.font_manager import findfont, FontProperties
    actual_font = findfont(FontProperties(family=FIGURE_FONT_FAMILY))
    log("")
    log(f"(c) requested font family: {FIGURE_FONT_FAMILY}")
    log(f"    resolved to: {actual_font}")
    log(f"    matplotlib: {matplotlib.__version__}, "
        f"savefig DPI: {FIGURE_DPI}")

    outputs: list[tuple[str, Path, Path, dict]] = []
    for name, fn in [
        ("FIG1", fig1), ("FIG2", fig2), ("FIG3", fig3), ("FIG4", fig4),
        ("FIG5", fig5), ("FIG6", fig6), ("FIG7", fig7),
    ]:
        pdf, svg, meta = fn()
        outputs.append((name, pdf, svg, meta))

    log("")
    log("(a) file listing")
    for name, pdf, svg, meta in outputs:
        pdf_kb = pdf.stat().st_size / 1024
        svg_kb = svg.stat().st_size / 1024
        w, h = meta["dims"]
        log(f"    {name}: {w}\" x {h}\", {meta['subplots']} subplot(s)")
        log(f"        PDF: {pdf.relative_to(REPO)} ({pdf_kb:.1f} KB)")
        log(f"        SVG: {svg.relative_to(REPO)} ({svg_kb:.1f} KB)")

    checks = next(m for n, _, _, m in outputs if n == "FIG1")["checks"]
    mismatches = [c for c in checks if not c["ok"]]
    log("")
    log("(b) data-integrity: FIG1 annual sums vs rq3_band_counts_national")
    for c in checks:
        marker = "OK" if c["ok"] else "MISMATCH"
        log(f"    {marker}  {c['year']} {c['status']}: "
            f"fig1={c['fig1_sum']:,} vs cs={c['cross_section']:,}")
    integrity_pass = len(mismatches) == 0
    log(f"    -> {'PASS' if integrity_pass else 'FAIL'} "
        f"({len(checks) - len(mismatches)}/{len(checks)})")

    fig3_meta = next(m for n, _, _, m in outputs if n == "FIG3")
    log("")
    log("(d) FIG3 panel titles (row-major 4x2 order)")
    for i, t in enumerate(fig3_meta["panel_titles"]):
        log(f"    [{i // 2}, {i % 2}] {t}")

    fig6_meta = next(m for n, _, _, m in outputs if n == "FIG6")
    V = fig6_meta["V_matrix"]
    regions = fig6_meta["regions"]
    outcomes = fig6_meta["outcomes"]
    log("")
    log("(e) FIG6 Cramer's V matrix (5 x 3)")
    header = "    " + " " * 18 + "  ".join(
        f"{OUTCOME_DISPLAY[s]:<14}" for s in outcomes
    )
    log(header)
    for i, reg in enumerate(regions):
        row = "  ".join(
            f"{V[i][j]:<14.3f}" if V[i][j] is not None
            and not (isinstance(V[i][j], float) and np.isnan(V[i][j]))
            else "na".ljust(14)
            for j in range(len(outcomes))
        )
        log(f"    {reg:<18} {row}")

    log("")
    log("=" * 72)
    log(f"figures produced: {len(outputs)}")
    log(f"integrity check:  {'pass' if integrity_pass else 'fail'}")
    log("=" * 72)

    LOG_OUT.write_text("\n".join(log_lines) + "\n", encoding="utf-8")
    print("\n".join(log_lines))

    print("")
    print(
        f"[30] done. {len(outputs)} figures x 2 formats = "
        f"{len(outputs) * 2} files. "
        f"Data-integrity check: {'pass' if integrity_pass else 'fail'}. "
        "Awaiting review."
    )


if __name__ == "__main__":
    try:
        main()
    except Exception:
        traceback.print_exc()
        sys.exit(1)
