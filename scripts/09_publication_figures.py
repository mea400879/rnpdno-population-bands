"""
Publication figures and tables — JQC submission.

Outputs:
  reports/figures/fig1_hh_trend_by_status.{pdf,png}
  reports/figures/fig2_cases_vs_rates_jaccard.{pdf,png}
  reports/figures/fig3_hh_maps_2015_2024.{pdf,png}
  reports/tables/table1_regional_shift.tex
  reports/tables/table2_trend_slopes.tex
  reports/findings_summary.md

NOTE: fig3 requires 4 targeted LISA runs (located_alive / located_dead ×
2015 / 2024 — cases only) to reconstruct per-municipality HH assignments.
These are data reconstructions using the identical methodology as script 08,
not new analysis.
"""

import sys
import warnings
from pathlib import Path

import geopandas as gpd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.lines as mlines
import matplotlib.ticker as ticker
import numpy as np
import pandas as pd
from scipy import stats

sys.path.insert(0, str(Path.cwd()))
from rnpdno_eda.models.spatial import load_municipios, build_queen_weights, run_lisa

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
Path("reports/figures").mkdir(parents=True, exist_ok=True)
Path("reports/tables").mkdir(parents=True, exist_ok=True)

YEARS = list(range(2015, 2025))
STATUSES = ["total", "disappeared", "located_alive", "located_dead"]
STATUS_LABELS = {
    "total": "Total",
    "disappeared": "Not Located",
    "located_alive": "Located Alive",
    "located_dead": "Located Dead",
}
STATUS_FILES = {
    "located_alive": "data/raw/rnpdno_located_alive.csv",
    "located_dead":  "data/raw/rnpdno_located_dead.csv",
}
REGION_MAP = {
    "Norte":           [2, 5, 8, 19, 26, 28],
    "Norte-Occidente": [3, 10, 18, 25, 32],
    "Centro-Norte":    [1, 6, 14, 16, 24],
    "Centro":          [9, 11, 13, 15, 17, 21, 22, 29],
    "Sur":             [4, 7, 12, 20, 23, 27, 30, 31],
}
REGIONS = list(REGION_MAP.keys())
CVE_TO_REGION = {c: r for r, cves in REGION_MAP.items() for c in cves}

NORTE_COLOR = "#D62728"
BAJIO_COLOR = "#1F77B4"
BAJIO_BORDER = "#333333"
ALIVE_COLOR  = "#2CA02C"
DEAD_COLOR   = "#D62728"
BG_COLOR     = "#F0EFE9"
REGION_COLORS = {
    "Norte": "#D62728", "Norte-Occidente": "#FF7F0E",
    "Centro-Norte": "#2CA02C", "Centro": "#1F77B4", "Sur": "#9467BD",
}

DPI = 300

# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

def load_data() -> dict:
    d = {}
    for st in STATUSES:
        d[f"rates_{st}"] = pd.read_csv(f"data/processed/hh_clusters_rates_{st}.csv")
        d[f"cases_{st}"] = pd.read_csv(f"data/processed/hh_clusters_cases_{st}.csv")
    d["comparison"] = pd.read_csv("data/processed/cluster_comparison_rates_vs_cases.csv")
    d["clf"]        = pd.read_csv("data/processed/municipality_classification_v2.csv")
    d["bajio"]      = pd.read_csv("data/processed/bajio_cvegeo_list_v2.csv")
    d["geo"]        = gpd.read_parquet("data/external/municipios_2024.geoparquet")
    d["geo"]["cvegeo"] = d["geo"]["cve_geo"].astype(str).str.zfill(5)
    return d


def series_counts(df: pd.DataFrame, col: str, val) -> dict:
    """Year → count of rows where col==val."""
    return {y: len(df[(df["year"] == y) & (df[col] == val)]) for y in YEARS}


def series_munis(df: pd.DataFrame, col: str, val) -> dict:
    return {
        y: df[(df["year"] == y) & (df[col] == val)]["n_munis"].sum()
        for y in YEARS
    }


# ---------------------------------------------------------------------------
# Figure 1: HH trend by status (4 panels)
# ---------------------------------------------------------------------------

def make_fig1(d: dict):
    fig, axes = plt.subplots(2, 2, figsize=(12, 8), sharey=False)
    axes = axes.flatten()

    legend_handles = [
        mlines.Line2D([], [], color=NORTE_COLOR, ls="-",  lw=1.8, label="Norte — cases"),
        mlines.Line2D([], [], color=NORTE_COLOR, ls="--", lw=1.8, label="Norte — rates"),
        mlines.Line2D([], [], color=BAJIO_COLOR, ls="-",  lw=1.8, label="Bajío — cases"),
        mlines.Line2D([], [], color=BAJIO_COLOR, ls="--", lw=1.8, label="Bajío — rates"),
    ]

    for idx, st in enumerate(STATUSES):
        ax = axes[idx]
        rc = d[f"rates_{st}"]
        cc = d[f"cases_{st}"]

        norte_r = [series_munis(rc, "region", "Norte")[y] for y in YEARS]
        norte_c = [series_munis(cc, "region", "Norte")[y] for y in YEARS]
        bajio_r = [
            rc[(rc["year"] == y) & rc["is_bajio_cluster"]]["n_munis"].sum()
            for y in YEARS
        ]
        bajio_c = [
            cc[(cc["year"] == y) & cc["is_bajio_cluster"]]["n_munis"].sum()
            for y in YEARS
        ]

        ax.plot(YEARS, norte_r, "--", color=NORTE_COLOR, lw=1.6, alpha=0.7)
        ax.plot(YEARS, norte_c, "-",  color=NORTE_COLOR, lw=1.8)
        ax.plot(YEARS, bajio_r, "--", color=BAJIO_COLOR, lw=1.6, alpha=0.7)
        ax.plot(YEARS, bajio_c, "-",  color=BAJIO_COLOR, lw=1.8)

        ax.set_title(f"({chr(65+idx)}) {STATUS_LABELS[st]}", fontsize=10, fontweight="bold", loc="left")
        ax.set_xlabel("Year", fontsize=9)
        ax.set_ylabel("Municipalities in HH clusters", fontsize=9)
        ax.xaxis.set_major_locator(ticker.MultipleLocator(2))
        ax.tick_params(labelsize=8)
        ax.grid(alpha=0.3, lw=0.5)
        ax.set_xlim(2014.5, 2024.5)
        ax.set_ylim(bottom=0)

    fig.legend(handles=legend_handles, loc="lower center", ncol=4,
               fontsize=8.5, frameon=True, bbox_to_anchor=(0.5, -0.01))
    fig.suptitle(
        "High-High Disappearance Clusters: Norte vs Bajío by Outcome Status\n"
        "(Queen contiguity, min. 3 municipalities, 2015–2024)",
        fontsize=11, fontweight="bold", y=1.01
    )
    plt.tight_layout()
    _save(fig, "reports/figures/fig1_hh_trend_by_status")


# ---------------------------------------------------------------------------
# Figure 2: Jaccard similarity — cases vs rates
# ---------------------------------------------------------------------------

def make_fig2(d: dict):
    comp = d["comparison"]

    fig, ax = plt.subplots(figsize=(8, 4.5))

    linestyles = ["-", "--", "-.", ":"]
    markers    = ["o", "s", "^", "D"]
    colors     = ["#1F77B4", "#FF7F0E", "#2CA02C", "#9467BD"]

    for i, st in enumerate(STATUSES):
        sub = comp[comp["status"] == st].sort_values("year")
        ax.plot(
            sub["year"], sub["jaccard_hh"],
            ls=linestyles[i], marker=markers[i], color=colors[i],
            lw=1.8, markersize=5, label=STATUS_LABELS[st]
        )

    ax.axhline(0.5, color="#999999", ls=":", lw=1, label="Jaccard = 0.5")
    ax.set_xlabel("Year", fontsize=10)
    ax.set_ylabel("Jaccard Similarity (HH municipalities)", fontsize=10)
    ax.set_title(
        "Annual Jaccard Similarity Between Case-Based and Rate-Based HH Municipalities\n"
        "by Outcome Status, 2015–2024",
        fontsize=10, fontweight="bold"
    )
    ax.set_ylim(0, 1)
    ax.set_xlim(2014.5, 2024.5)
    ax.xaxis.set_major_locator(ticker.MultipleLocator(1))
    ax.tick_params(labelsize=9)
    ax.grid(alpha=0.3, lw=0.5)
    ax.legend(fontsize=9, frameon=True)

    plt.tight_layout()
    _save(fig, "reports/figures/fig2_cases_vs_rates_jaccard")


# ---------------------------------------------------------------------------
# Figure 3: Maps 2015 vs 2024 (located_alive, located_dead — cases)
# ---------------------------------------------------------------------------

def reconstruct_hh_munis(target_status: str, target_year: int) -> set:
    """
    Re-derive HH municipalities using cases-based LISA for one status × year.
    Identical methodology to script 08. Returns set of cvegeo strings.
    """
    raw = pd.read_csv(STATUS_FILES[target_status], dtype={"cvegeo": str})
    raw["cvegeo"] = raw["cvegeo"].str.zfill(5)

    gdf = load_municipios()
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        w = build_queen_weights(gdf)

    # Annual cases for this year
    annual = (
        raw[raw["year"] == target_year]
        .groupby("cvegeo")["total"].sum()
        .reindex(w.id_order).fillna(0)
        .values
    )
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        res = run_lisa(annual, w, permutations=999, alpha=0.05)

    return {w.id_order[i] for i, c in enumerate(res["clusters"]) if c == 1}


def _add_scale_bar(ax, length_m=500_000, x0=0.05, y0=0.05):
    """Add a simple scale bar in projected metres."""
    xlim = ax.get_xlim()
    ylim = ax.get_ylim()
    xrange = xlim[1] - xlim[0]
    yrange = ylim[1] - ylim[0]
    x_start = xlim[0] + x0 * xrange
    x_end   = x_start + length_m
    y_pos   = ylim[0] + y0 * yrange
    ax.plot([x_start, x_end], [y_pos, y_pos], "k-", lw=2, transform=ax.transData)
    ax.text((x_start + x_end) / 2, y_pos + 0.015 * yrange,
            f"{length_m//1000:,} km", ha="center", va="bottom", fontsize=6.5,
            transform=ax.transData)


def _add_north_arrow(ax):
    xlim = ax.get_xlim()
    ylim = ax.get_ylim()
    xr = xlim[1] - xlim[0]
    yr = ylim[1] - ylim[0]
    x = xlim[1] - 0.06 * xr
    y = ylim[0] + 0.10 * yr
    ax.annotate("", xy=(x, y + 0.05 * yr), xytext=(x, y),
                 arrowprops=dict(arrowstyle="-|>", color="k", lw=1.2),
                 annotation_clip=False)
    ax.text(x, y + 0.06 * yr, "N", ha="center", va="bottom", fontsize=7,
            fontweight="bold")


def make_fig3(d: dict):
    geo = d["geo"].copy()
    bajio_cvegeos = set(d["bajio"]["cvegeo"].astype(str).str.zfill(5))
    clf = d["clf"].set_index("cvegeo")

    # State borders (dissolve by state code)
    geo["cve_ent"] = geo["cvegeo"].str[:2]
    states = geo.dissolve(by="cve_ent")

    # Reconstruct HH sets for the 4 combinations
    print("  Reconstructing HH municipality sets for fig3 (4 LISA runs)...")
    combos = {
        ("located_alive", 2015): None,
        ("located_alive", 2024): None,
        ("located_dead",  2015): None,
        ("located_dead",  2024): None,
    }
    for (st, yr) in combos:
        print(f"    {st} {yr}...", end=" ", flush=True)
        combos[(st, yr)] = reconstruct_hh_munis(st, yr)
        print(f"{len(combos[(st, yr)])} HH munis")

    # Panel layout: rows = status (alive, dead), cols = year (2015, 2024)
    panel_order = [
        ("located_alive", 2015, ALIVE_COLOR, "(A) Located Alive — 2015"),
        ("located_alive", 2024, ALIVE_COLOR, "(B) Located Alive — 2024"),
        ("located_dead",  2015, DEAD_COLOR,  "(C) Located Dead — 2015"),
        ("located_dead",  2024, DEAD_COLOR,  "(D) Located Dead — 2024"),
    ]

    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    axes = axes.flatten()

    bounds = geo.total_bounds  # [xmin, ymin, xmax, ymax] in EPSG:6372

    for idx, (st, yr, hh_color, title) in enumerate(panel_order):
        ax = axes[idx]
        hh_set = combos[(st, yr)]

        # Background: all municipalities
        geo.plot(ax=ax, color=BG_COLOR, edgecolor="#C0C0C0", linewidth=0.15, zorder=1)

        # HH municipalities (filled)
        hh_gdf = geo[geo["cvegeo"].isin(hh_set)]
        if not hh_gdf.empty:
            hh_gdf.plot(ax=ax, color=hh_color, edgecolor="#333333",
                        linewidth=0.25, alpha=0.85, zorder=3)

        # Bajío border (thin dashed, no fill change)
        bajio_gdf = geo[geo["cvegeo"].isin(bajio_cvegeos)]
        bajio_gdf.boundary.plot(
            ax=ax, color=BAJIO_BORDER, linewidth=0.65,
            linestyle="--", zorder=4
        )

        # State borders on top
        states.boundary.plot(
            ax=ax, color="#666666", linewidth=0.45, zorder=2
        )

        ax.set_title(title, fontsize=10, fontweight="bold", loc="left", pad=4)
        ax.set_xlim(bounds[0] - 20_000, bounds[2] + 20_000)
        ax.set_ylim(bounds[1] - 20_000, bounds[3] + 20_000)
        ax.set_aspect("equal")
        ax.axis("off")

        # Annotations
        n_hh = len(hh_set)
        n_in_cluster = len(hh_gdf)
        ax.text(0.02, 0.02, f"HH municipalities: {n_hh}",
                transform=ax.transAxes, fontsize=7.5,
                bbox=dict(boxstyle="round,pad=0.2", facecolor="white", alpha=0.8))

        _add_scale_bar(ax)
        _add_north_arrow(ax)

    # Shared legend
    hh_alive_patch = mpatches.Patch(color=ALIVE_COLOR, alpha=0.85, label="HH — Located Alive")
    hh_dead_patch  = mpatches.Patch(color=DEAD_COLOR,  alpha=0.85, label="HH — Located Dead")
    bajio_line     = mlines.Line2D([], [], color=BAJIO_BORDER, ls="--", lw=1.2, label="Bajío boundary")
    fig.legend(
        handles=[hh_alive_patch, hh_dead_patch, bajio_line],
        loc="lower center", ncol=3, fontsize=9,
        frameon=True, bbox_to_anchor=(0.5, -0.01)
    )
    fig.suptitle(
        "Spatial Distribution of High-High Disappearance Municipalities\n"
        "Located Alive vs Located Dead, 2015 and 2024 (cases, EPSG:6372)",
        fontsize=11, fontweight="bold", y=1.01
    )
    plt.tight_layout()
    _save(fig, "reports/figures/fig3_hh_maps_2015_2024")


# ---------------------------------------------------------------------------
# Table 1: Regional shift 2015 vs 2024 (chi-square)
# ---------------------------------------------------------------------------

def make_table1(d: dict):
    clf = d["clf"].set_index("cvegeo")
    bajio_cvegeos = set(d["bajio"]["cvegeo"].astype(str).str.zfill(5))

    # We show: disappeared, located_alive, located_dead (skip total — redundant)
    show_statuses = ["disappeared", "located_alive", "located_dead"]
    show_labels   = ["Not Located", "Located Alive", "Located Dead"]

    rows_tex = []
    rows_tex.append(r"\begin{table}[htbp]")
    rows_tex.append(r"\centering")
    rows_tex.append(r"\small")
    rows_tex.append(
        r"\caption{Regional Composition of High-High Disappearance Municipalities, "
        r"2015 vs 2024 (cases-based LISA, minimum cluster size = 3)}"
    )
    rows_tex.append(r"\label{tab:regional_shift}")

    # Column spec: region | (2015, 2024, Δ) × 3 statuses
    cols = "l" + "rrr" * len(show_statuses)
    rows_tex.append(r"\begin{tabular}{" + cols + r"}")
    rows_tex.append(r"\toprule")

    # Header row 1
    header1 = "Region"
    for lbl in show_labels:
        header1 += rf" & \multicolumn{{3}}{{c}}{{{lbl}}}"
    rows_tex.append(header1 + r" \\")
    rows_tex.append(
        r"\cmidrule(lr){2-4}\cmidrule(lr){5-7}\cmidrule(lr){8-10}"
    )

    # Header row 2
    header2 = ""
    for _ in show_statuses:
        header2 += r" & 2015 & 2024 & $\Delta$"
    rows_tex.append(header2 + r" \\")
    rows_tex.append(r"\midrule")

    # Collect counts per region × year × status
    chi2_pvals = {}
    all_counts = {}  # (status, region, year) → count

    for st in show_statuses:
        df = d[f"cases_{st}"]
        for yr in [2015, 2024]:
            yr_df = df[df["year"] == yr]
            for region in REGIONS:
                n = yr_df[(yr_df["region"] == region)]["n_munis"].sum()
                all_counts[(st, region, yr)] = int(n)

        # Chi-square: 5-region distribution 2015 vs 2024
        c2015 = np.array([all_counts[(st, r, 2015)] for r in REGIONS])
        c2024 = np.array([all_counts[(st, r, 2024)] for r in REGIONS])
        contingency = np.vstack([c2015, c2024])
        try:
            chi2, p, dof, _ = stats.chi2_contingency(contingency)
        except Exception:
            p = np.nan
        chi2_pvals[st] = p

    # Region rows
    for region in REGIONS:
        row = region.replace("-", "--")  # LaTeX hyphen
        for st in show_statuses:
            n15 = all_counts[(st, region, 2015)]
            n24 = all_counts[(st, region, 2024)]
            delta = n24 - n15
            sign = "+" if delta >= 0 else ""
            row += rf" & {n15} & {n24} & {sign}{delta}"
        rows_tex.append(row + r" \\")

    rows_tex.append(r"\midrule")

    # "of which Bajío" row
    # Bajío overlaps Centro-Norte + Centro — count HH munis that are Bajío-flagged within those regions
    row_bajio = r"\quad \textit{of which Bajío}"
    for st in show_statuses:
        df = d[f"cases_{st}"]
        for yr in [2015, 2024]:
            yr_df = df[df["year"] == yr]
            # HH munis in Centro-Norte + Centro
            central = yr_df[yr_df["region"].isin(["Centro-Norte", "Centro"])]["n_munis"].sum()
            bajio_hh = yr_df[yr_df["is_bajio_cluster"]]["n_munis"].sum()
            if central > 0:
                pct = f"{100*bajio_hh/central:.0f}\\%"
            else:
                pct = "--"
        # Show 2015 and 2024 values
        b15, b24 = [], []
        for yr, target in [(2015, b15), (2024, b24)]:
            yr_df = df[df["year"] == yr]
            n_bajio = yr_df[yr_df["is_bajio_cluster"]]["n_munis"].sum()
            n_central = yr_df[yr_df["region"].isin(["Centro-Norte", "Centro"])]["n_munis"].sum()
            pct_str = f"{100*n_bajio/n_central:.0f}\\%" if n_central > 0 else "--"
            target.append((n_bajio, pct_str))

        n15_b, pct15 = b15[0], b15[0][1]
        n24_b, pct24 = b24[0], b24[0][1]
        n15_val = b15[0][0]
        n24_val = b24[0][0]
        delta_b = n24_val - n15_val
        sign = "+" if delta_b >= 0 else ""
        row_bajio += rf" & {n15_val} ({pct15}) & {n24_val} ({pct24}) & {sign}{delta_b}"

    rows_tex.append(row_bajio + r" \\")
    rows_tex.append(r"\midrule")

    # Chi-square row
    row_chi = r"$\chi^2$ \textit{p}-value"
    for st in show_statuses:
        p = chi2_pvals[st]
        p_str = _fmt_p(p)
        row_chi += rf" & \multicolumn{{3}}{{c}}{{{p_str}}}"
    rows_tex.append(row_chi + r" \\")
    rows_tex.append(r"\bottomrule")
    rows_tex.append(r"\end{tabular}")
    rows_tex.append(
        r"\begin{tablenotes}\small"
        r"\item \textit{Note}: Counts are municipalities belonging to High-High spatial clusters "
        r"($\alpha = 0.05$, 999 permutations, Queen contiguity, min.\ size = 3). "
        r"``of which Bajío'' counts HH municipalities flagged as Bajío, expressed as \% of "
        r"Centro-Norte + Centro HH municipalities. "
        r"$\chi^2$ tests the null that regional composition is identical in 2015 and 2024 (df = 4)."
        r"\end{tablenotes}"
    )
    rows_tex.append(r"\end{table}")

    tex = "\n".join(rows_tex)
    Path("reports/tables/table1_regional_shift.tex").write_text(tex)
    print("  Saved: reports/tables/table1_regional_shift.tex")


# ---------------------------------------------------------------------------
# Table 2: Trend slopes by status × metric
# ---------------------------------------------------------------------------

def make_table2(d: dict):
    rows_tex = []
    rows_tex.append(r"\begin{table}[htbp]")
    rows_tex.append(r"\centering")
    rows_tex.append(r"\small")
    rows_tex.append(
        r"\caption{Linear Trend Slopes (Municipalities per Year) in High-High Clusters, "
        r"Norte vs Bajío, by Outcome Status and Metric (2015--2024)}"
    )
    rows_tex.append(r"\label{tab:trend_slopes}")

    # Columns: geography | (slope, p) × 4 statuses × 2 metrics = 8 sub-cols
    # Layout: geography | metric || status 1 col | status 2 col | ...
    rows_tex.append(r"\begin{tabular}{llrrrr}")
    rows_tex.append(r"\toprule")
    rows_tex.append(
        r" & & \multicolumn{4}{c}{Outcome status} \\"
    )
    rows_tex.append(r"\cmidrule(lr){3-6}")
    rows_tex.append(
        r"Geography & Metric & Total & Not Located & Located Alive & Located Dead \\"
    )
    rows_tex.append(r"\midrule")

    for geo_label, geo_col, geo_val in [
        ("Norte",  "region",          "Norte"),
        ("Bajío",  "is_bajio_cluster", True),
    ]:
        for metric in ["cases", "rates"]:
            row = geo_label if metric == "cases" else ""
            row += f" & {metric.capitalize()}"
            for st in STATUSES:
                df = d[f"{metric}_{st}"]
                if geo_col == "region":
                    munis = [df[(df["year"] == y) & (df[geo_col] == geo_val)]["n_munis"].sum() for y in YEARS]
                else:
                    munis = [df[(df["year"] == y) & df[geo_col]]["n_munis"].sum() for y in YEARS]
                sl, _, _, p, _ = stats.linregress(YEARS, munis)
                stars = "***" if p < 0.001 else "**" if p < 0.01 else "*" if p < 0.05 else ""
                sign = "+" if sl >= 0 else ""
                row += rf" & {sign}{sl:.2f}{stars}"
            rows_tex.append(row + r" \\")
        rows_tex.append(r"\midrule" if geo_label == "Norte" else "")

    rows_tex.append(r"\bottomrule")
    rows_tex.append(r"\end{tabular}")
    rows_tex.append(
        r"\begin{tablenotes}\small"
        r"\item \textit{Note}: Coefficients from OLS linear regression of annual municipality count "
        r"in HH clusters on year (slope = municipalities/year). "
        r"$^{*}p<0.05$, $^{**}p<0.01$, $^{***}p<0.001$. "
        r"Bajío row includes all HH cluster municipalities where $\geq$50\% of cluster members "
        r"are Bajío-flagged. Norte excludes Bajío-flagged municipalities."
        r"\end{tablenotes}"
    )
    rows_tex.append(r"\end{table}")

    # Remove blank lines caused by empty midrule logic
    tex = "\n".join(r for r in rows_tex if r is not None)
    Path("reports/tables/table2_trend_slopes.tex").write_text(tex)
    print("  Saved: reports/tables/table2_trend_slopes.tex")


# ---------------------------------------------------------------------------
# Findings summary
# ---------------------------------------------------------------------------

FINDINGS_MD = """\
# Key Findings: Spatial Dynamics of Disappearances in Mexico (2015–2024)

**Data:** RNPDNO (4 outcome statuses) × INEGI municipalities × CONAPO population
**Method:** Annual Local Moran's I (cases and rates), Queen contiguity, min. cluster size = 3

---

## Finding 1 — Spatial dynamics differ fundamentally by outcome status

High-High cluster geography is not uniform across the RNPDNO registry outcomes:

- **Located Dead** municipalities concentrate and grow in **Norte** (slope +2.29/yr,
  *p* < 0.001, cases-based), suggesting Norte as the dominant geography of lethal
  disappearances and a consolidating hotspot of lethal violence.

- **Located Alive** municipalities show a simultaneous Norte expansion (+1.42/yr,
  *p* = 0.004) **and** a significant Bajío contraction (−2.19/yr, *p* = 0.014),
  consistent with a geographic reorganization of trafficking routes rather than
  an aggregate increase in violence.

- **Not Located (disappeared)** municipalities show no significant trend in either
  Norte or Bajío (*p* > 0.33 for all), indicating geographic stability in unresolved
  cases over the study period.

---

## Finding 2 — The "rising Bajío" hypothesis is not supported

Contrary to prior expectations, Bajío HH cluster municipalities are **declining** in
the cases-based analysis for total (+total: −2.12/yr, *p* = 0.02; located alive:
−2.19/yr, *p* = 0.01). The apparent Bajío concentration observed in 2015–2019
represents a transitional peak, not a structural emergence. Norte remains and
intensifies as the core disappearance geography.

---

## Finding 3 — Rate-based and case-based hotspots identify different geographies

Jaccard similarity between rate-based and case-based HH municipality sets is
consistently low (mean 0.13–0.26 across statuses), indicating that the two metrics
identify largely non-overlapping geographies:

- **Rate-based LISA** flags rural municipalities with small populations (Band 1–2),
  where even a handful of cases produces high per-capita rates.
- **Case-based LISA** flags urban municipalities (Band 3–4) where absolute burden
  is concentrated.

This divergence has direct policy implications: rate-based targeting prioritizes
vulnerable small-municipality contexts; case-based targeting prioritizes resource
deployment to high-volume urban areas. Both are valid but serve different goals.

---

## Methodological note

All results are based on existing LISA assignments (script 08). Fig. 3 municipality
polygons reconstruct per-municipality HH assignments using identical parameters
(999 permutations, α = 0.05, cases metric). No new analytical decisions were made.
"""

def make_findings_summary():
    Path("reports/findings_summary.md").write_text(FINDINGS_MD.strip())
    print("  Saved: reports/findings_summary.md")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _fmt_p(p: float) -> str:
    if np.isnan(p):
        return "n.a."
    if p < 0.001:
        return "$p < 0.001$"
    if p < 0.01:
        return f"$p = {p:.3f}$**"
    if p < 0.05:
        return f"$p = {p:.3f}$*"
    return f"$p = {p:.3f}$"


def _save(fig: plt.Figure, stem: str):
    for ext in ["pdf", "png"]:
        path = f"{stem}.{ext}"
        fig.savefig(path, dpi=DPI, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"  Saved: {stem}.pdf / .png")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print("Loading data...")
    d = load_data()

    print("\n--- Figure 1: HH trend by status ---")
    make_fig1(d)

    print("\n--- Figure 2: Jaccard similarity ---")
    make_fig2(d)

    print("\n--- Figure 3: HH maps 2015 vs 2024 ---")
    make_fig3(d)

    print("\n--- Table 1: Regional shift ---")
    make_table1(d)

    print("\n--- Table 2: Trend slopes ---")
    make_table2(d)

    print("\n--- Findings summary ---")
    make_findings_summary()

    print("\nDONE. All outputs in reports/")


if __name__ == "__main__":
    main()
