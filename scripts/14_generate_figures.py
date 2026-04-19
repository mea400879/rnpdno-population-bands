"""Phase 3 — Publication figures (8 figures).

Outputs (PDF + PNG) in manuscript/figures/:
  fig1_time_series_by_status   — monthly national counts, 4-panel by status, sex-disaggregated
  fig2_gini_time_series        — Gini time series with OLS slopes, 4 statuses, ref line at 0.90
  fig3_morans_i_time_series    — Global Moran's I over time, 4 statuses
  fig4_lisa_maps_latest        — LISA maps Jun 2025, 2×2 grid by status
  fig5_hh_trend_norte_bajio    — HH municipalities over time, Norte vs Bajío vs Centro, 4-panel
  fig6_lisa_maps_2015_2019_2025 — LISA maps Jun 2015 vs Jun 2019 vs Jun 2025, Located Alive + Dead
  fig7_sex_disaggregation_maps — Male vs female LISA maps Jun 2025, Not Located + Located Dead
  fig8_regional_hh_heatmap     — Regional HH heatmap, 11 June snapshots × 4 statuses

Map PNG outputs: 150 DPI (file-size conscious).
Non-map PNG outputs: 300 DPI.
All PDFs: vector (no DPI limit).
"""

import sys
import logging
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import polars as pl
import geopandas as gpd
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.patches as mpatches
from matplotlib.lines import Line2D
from scipy import stats

matplotlib.rcParams.update({
    "font.family":      "serif",
    "font.size":        11,
    "axes.titlesize":   13,
    "axes.labelsize":   11,
    "xtick.labelsize":  9,
    "ytick.labelsize":  9,
    "legend.fontsize":  9,
    "figure.dpi":       150,
    "savefig.dpi":      150,
    "text.usetex":      False,
})

# ---------------------------------------------------------------------------
# CONFIG
# ---------------------------------------------------------------------------
ROOT      = Path(__file__).resolve().parent.parent
DATA_PROC = ROOT / "data" / "processed"
DATA_EXT  = ROOT / "data" / "external"
OUT_DIR   = ROOT / "manuscript" / "figures"
LOGS_DIR  = ROOT / "logs"

OUT_DIR.mkdir(parents=True, exist_ok=True)

# Statuses
STATUS_IDS    = [0, 7, 2, 3]   # plot order
STATUS_LABELS = {0: "Total", 7: "Not Located", 2: "Located Alive", 3: "Located Dead"}
STATUS_COLORS = {0: "#2c3e50", 7: "#2980b9", 2: "#27ae60", 3: "#c0392b"}

SEX_COLORS  = {"total": "#2c3e50", "male": "#3498db", "female": "#e74c3c"}
SEX_STYLES  = {"total": "-",       "male": "--",       "female": ":"}
SEX_LABELS  = {"total": "Total",   "male": "Male",     "female": "Female"}

LISA_COLORS = {
    "HH": "#c0392b",   # red
    "LL": "#D9D9D9",   # grey (suppressed — LL not interpreted)
    "HL": "#f39c12",   # orange
    "LH": "#85c1e9",   # light blue
    "NS": "#e8e8e8",   # light gray
}
LISA_ORDER  = ["HH", "LL", "HL", "LH", "NS"]
LISA_LABELS = {"HH": "High-High", "LL": "LL (not interpreted)", "HL": "High-Low", "LH": "Low-High", "NS": "Not Sig."}

MAP_DPI       = 150   # for PNG of map figures
NONMAP_DPI    = 300   # for PNG of non-map figures
GEO_TOLERANCE = 1000  # metres, for geometry simplification

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
def save_fig(fig, name: str, is_map: bool = False):
    """Save figure as PDF (vector) and PNG (raster)."""
    dpi = MAP_DPI if is_map else NONMAP_DPI
    pdf_path = OUT_DIR / f"{name}.pdf"
    png_path = OUT_DIR / f"{name}.png"
    fig.savefig(pdf_path, bbox_inches="tight", format="pdf")
    fig.savefig(png_path, bbox_inches="tight", dpi=dpi, format="png")
    log.info(f"  Saved {name}.pdf + .png (PNG DPI={dpi})")
    plt.close(fig)


def ym_to_date(year_arr, month_arr):
    """Convert parallel year/month arrays to list of pd.Timestamp."""
    return [pd.Timestamp(y, m, 1) for y, m in zip(year_arr, month_arr)]


def ols_trend(y: np.ndarray):
    """Return (slope, intercept) of OLS fit of y ~ [0,1,...,n-1]."""
    x = np.arange(len(y), dtype=float)
    return stats.linregress(x, y)


def plot_lisa_map(ax, gdf_merged, title):
    """Plot LISA cluster map on ax from a GeoDataFrame with 'cluster_label' column."""
    for label in LISA_ORDER:
        subset = gdf_merged[gdf_merged["cluster_label"] == label]
        if len(subset) > 0:
            subset.plot(
                ax=ax,
                color=LISA_COLORS[label],
                linewidth=0.08,
                edgecolor="white",
            )
    ax.set_axis_off()
    ax.set_title(title, fontsize=11, pad=4)


def make_lisa_legend(ax, loc="lower left"):
    patches = [
        mpatches.Patch(facecolor=LISA_COLORS[l], label=LISA_LABELS[l], linewidth=0)
        for l in LISA_ORDER
    ]
    ax.legend(handles=patches, loc=loc, fontsize=7, framealpha=0.85,
              edgecolor="#cccccc", handlelength=1.2)


# ---------------------------------------------------------------------------
# FIGURE 1: Monthly time series by status, sex-disaggregated
# ---------------------------------------------------------------------------
def make_fig1(panel: pl.DataFrame):
    log.info("Fig 1: time series by status...")

    nat = (
        panel.group_by(["status_id", "year", "month"])
        .agg(
            pl.col("total").sum().alias("total"),
            pl.col("male").sum().alias("male"),
            pl.col("female").sum().alias("female"),
        )
        .sort(["status_id", "year", "month"])
    ).to_pandas()

    fig, axes = plt.subplots(2, 2, figsize=(14, 10), sharex=True)
    axes = axes.flatten()

    for i, sid in enumerate(STATUS_IDS):
        ax = axes[i]
        sub = nat[nat["status_id"] == sid].copy()
        dates = ym_to_date(sub["year"], sub["month"])
        for sx in ["male", "female", "total"]:
            lw = 1.2 if sx == "total" else 1.5
            ax.plot(dates, sub[sx], color=SEX_COLORS[sx],
                    linestyle=SEX_STYLES[sx], linewidth=lw, label=SEX_LABELS[sx], alpha=0.9)
        ax.set_title(STATUS_LABELS[sid], color=STATUS_COLORS[sid], fontweight="bold")
        ax.set_ylabel("Registered persons")
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
        ax.xaxis.set_major_locator(mdates.YearLocator(2))
        ax.tick_params(axis="x", rotation=45)
        ax.grid(True, alpha=0.3, linestyle="--")
        ax.spines[["top", "right"]].set_visible(False)
        if i == 0:
            ax.legend(loc="upper left")

    fig.suptitle(
        "Monthly Registered Persons by Outcome Status, 2015–2025\nMexico (Municipal Level, Aggregated Nationally)",
        fontsize=13, y=1.01
    )
    plt.tight_layout()
    save_fig(fig, "fig1_time_series_by_status", is_map=False)


# ---------------------------------------------------------------------------
# FIGURE 2: Gini time series with OLS slopes
# ---------------------------------------------------------------------------
def make_fig2(conc: pl.DataFrame):
    log.info("Fig 2: Gini time series with OLS slopes...")

    df = conc.to_pandas()
    fig, ax = plt.subplots(figsize=(12, 5))

    for sid in STATUS_IDS:
        sub = df[df["status_id"] == sid].sort_values(["year", "month"])
        dates = ym_to_date(sub["year"], sub["month"])
        y = sub["gini"].values
        ax.plot(dates, y, color=STATUS_COLORS[sid],
                linewidth=1.6, label=STATUS_LABELS[sid], alpha=0.9)

        # OLS trend annotation (slope per decade = slope_per_month * 120)
        if len(y) >= 6:
            sl = ols_trend(y)
            slope_decade = sl.slope * 120
            p_str = "p<0.001" if sl.pvalue < 0.001 else f"p={sl.pvalue:.3f}"
            sig = "*" if sl.pvalue < 0.05 else ""
            label_txt = f"{STATUS_LABELS[sid]}: {slope_decade:+.4f}/dec {sig}({p_str})"
            # Place annotation in the plot area
            ax.annotate(label_txt, xy=(dates[-1], y[-1]),
                        xytext=(8, 0), textcoords="offset points",
                        fontsize=7.5, color=STATUS_COLORS[sid], va="center")

    ax.axhline(0.90, color="#7f8c8d", linestyle="--", linewidth=1.0, alpha=0.7,
               label="Reference (Gini = 0.90)")
    ax.set_ylabel("Gini Coefficient")
    ax.set_xlabel("")
    ax.set_title("Geographic Concentration (Gini) by Outcome Status, 2015–2025\n"
                 "with OLS Trend Slopes (per decade)")
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    ax.xaxis.set_major_locator(mdates.YearLocator(1))
    ax.tick_params(axis="x", rotation=45)
    ax.set_ylim(0.85, 1.0)
    ax.legend(loc="lower left", fontsize=8)
    ax.grid(True, alpha=0.3, linestyle="--")
    ax.spines[["top", "right"]].set_visible(False)
    plt.tight_layout()
    save_fig(fig, "fig2_gini_time_series", is_map=False)


# ---------------------------------------------------------------------------
# FIGURE 3: Global Moran's I time series
# ---------------------------------------------------------------------------
def make_fig3(moran: pl.DataFrame):
    log.info("Fig 3: Moran's I time series...")

    df = moran.to_pandas()
    fig, ax = plt.subplots(figsize=(12, 5))

    for sid in STATUS_IDS:
        sub = df[df["status_id"] == sid].sort_values(["year", "month"])
        dates  = ym_to_date(sub["year"], sub["month"])
        sig    = sub["p_value"] < 0.05
        # Plot significant periods as solid, non-significant as dotted
        y = sub["morans_i"].values
        ax.plot(dates, y, color=STATUS_COLORS[sid],
                linewidth=1.5, label=STATUS_LABELS[sid], alpha=0.9)
        # Mark non-significant months with open circles
        nonsig_dates = [d for d, s in zip(dates, sig) if not s]
        nonsig_y     = y[~sig.values]
        if len(nonsig_dates) > 0:
            ax.scatter(nonsig_dates, nonsig_y, color=STATUS_COLORS[sid],
                       s=18, marker="o", facecolors="white", zorder=5, linewidths=0.8)

    ax.axhline(0, color="#7f8c8d", linestyle="--", linewidth=0.8, alpha=0.6)
    ax.set_ylabel("Moran's $I$")
    ax.set_title("Global Spatial Autocorrelation (Moran's $I$) by Outcome Status, 2015–2025\n"
                 "(open circles = p ≥ 0.05)")
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    ax.xaxis.set_major_locator(mdates.YearLocator(1))
    ax.tick_params(axis="x", rotation=45)
    ax.legend(loc="upper left")
    ax.grid(True, alpha=0.3, linestyle="--")
    ax.spines[["top", "right"]].set_visible(False)
    plt.tight_layout()
    save_fig(fig, "fig3_morans_i_time_series", is_map=False)


# ---------------------------------------------------------------------------
# FIGURE 4: LISA maps — latest period (Jun 2025), 4 statuses
# ---------------------------------------------------------------------------
def make_fig4(lisa: pl.DataFrame, gdf: gpd.GeoDataFrame):
    log.info("Fig 4: LISA maps Jun 2025...")

    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    axes = axes.flatten()

    for i, sid in enumerate(STATUS_IDS):
        sub = (
            lisa.filter(
                (pl.col("status_id") == sid) &
                (pl.col("year") == 2025) &
                (pl.col("month") == 6) &
                (pl.col("sex") == "total")
            )
            .select(["cvegeo", "cluster_label"])
            .to_pandas()
            .set_index("cvegeo")
        )
        gdf_m = gdf.join(sub, how="left")
        gdf_m["cluster_label"] = gdf_m["cluster_label"].fillna("NS")
        plot_lisa_map(axes[i], gdf_m, STATUS_LABELS[sid])
        if i == 3:
            make_lisa_legend(axes[i])

    fig.suptitle("Local Spatial Autocorrelation (LISA) by Outcome Status\nJune 2025 (total sex, α = 0.05)",
                 fontsize=13, y=1.00)
    plt.tight_layout()
    save_fig(fig, "fig4_lisa_maps_latest", is_map=True)


# ---------------------------------------------------------------------------
# FIGURE 5: HH trend Norte vs Bajío vs Centro, 4-panel by status
# ---------------------------------------------------------------------------
def make_fig5(lisa: pl.DataFrame, muni_meta: pl.DataFrame):
    log.info("Fig 5: HH trend Norte vs Centro (proportional)...")

    # Proportional slopes and HAC p-values from WP6_table5_proportions.csv
    PROP_ANNOT = pd.read_csv(
        ROOT / "audit" / "outputs" / "WP6_table5_proportions.csv"
    )

    REGION_SPECS = [
        ("Norte",  "region", "Norte",  "#c0392b", "-",  278),
        ("Centro", "region", "Centro", "#2ca02c", "-",  602),
    ]
    STATUS_MAP = {0: "total", 7: "nl", 2: "la", 3: "ld"}

    hh_total = (
        lisa.filter(
            (pl.col("sex") == "total") &
            (pl.col("cluster_label") == "HH")
        )
        .select(["status_id", "year", "month", "cvegeo"])
        .join(muni_meta, on="cvegeo", how="left")
    )

    fig, axes = plt.subplots(2, 2, figsize=(16, 11), sharex=True)
    axes = axes.flatten()

    # Full month grid for consistent OLS (include zero-count months)
    all_ym = pd.DataFrame(
        [(y, m) for y in range(2015, 2026) for m in range(1, 13)],
        columns=["year", "month"],
    )

    for i, sid in enumerate(STATUS_IDS):
        ax = axes[i]
        sub = hh_total.filter(pl.col("status_id") == sid)
        annotations = []

        for label, col, val, color, ls, denom in REGION_SPECS:
            df_reg = (
                sub.filter(pl.col(col) == val)
                .group_by(["year", "month"])
                .agg(pl.len().alias("n"))
                .sort(["year", "month"])
                .to_pandas()
            )
            df_full = all_ym.merge(df_reg, on=["year", "month"], how="left").fillna(0)
            df_full["n"] = df_full["n"].astype(int)
            df_full["pct"] = df_full["n"] / denom * 100
            dates_full = ym_to_date(df_full["year"], df_full["month"])
            ax.plot(dates_full, df_full["pct"], color=color, linestyle=ls,
                    linewidth=2.0, label=label, alpha=0.9)

            # OLS trend line (on proportions)
            y_full = df_full["pct"].values
            if len(y_full) >= 6:
                sl = ols_trend(y_full)
                x_num = np.arange(len(y_full))
                trend = sl.intercept + sl.slope * x_num
                ax.plot(dates_full, trend, color=color, linestyle=":", linewidth=1.0, alpha=0.6)

            # Annotation from WP6 table (HAC slope + HAC p-value)
            status_key = STATUS_MAP[sid]
            row = PROP_ANNOT[
                (PROP_ANNOT["region"] == label) & (PROP_ANNOT["status"] == status_key)
            ]
            if len(row) == 1:
                slope_pct = row["slope_pct_yr"].values[0]
                hac_p = row["hac_p"].values[0]
                hac_stars = row["hac_stars"].values[0]
                p_str = "p<0.001" if hac_p < 0.001 else f"p={hac_p:.3f}"
                annotations.append(
                    f"{label}: {slope_pct:+.3f} pp/yr {hac_stars}({p_str}, HAC)"
                )

        if annotations:
            txt = "\n".join(annotations)
            ax.text(0.97, 0.97, txt, transform=ax.transAxes, fontsize=11,
                    va="top", ha="right", family="monospace",
                    bbox=dict(boxstyle="round,pad=0.3", facecolor="white", alpha=0.8))

        ax.set_title(STATUS_LABELS[sid], color=STATUS_COLORS[sid], fontweight="bold")
        ax.set_ylabel("HH municipalities (% of region)")
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
        ax.xaxis.set_major_locator(mdates.YearLocator(2))
        ax.tick_params(axis="x", rotation=45)
        ax.grid(True, alpha=0.3, linestyle="--")
        ax.spines[["top", "right"]].set_visible(False)
        if i == 0:
            ax.legend(loc="upper left")

    fig.suptitle("Proportion of Regional Municipalities Classified High-High: Norte vs. Centro\n"
                 "(dotted lines = OLS trend; annotations = HAC-robust slopes)",
                 fontsize=13)
    plt.tight_layout()
    save_fig(fig, "fig5_hh_trend_norte_bajio", is_map=False)


# ---------------------------------------------------------------------------
# FIGURE 6: LISA maps Jun 2015 vs Jun 2019 vs Jun 2025 — Located Alive + Located Dead
# ---------------------------------------------------------------------------
def make_fig6(lisa: pl.DataFrame, gdf: gpd.GeoDataFrame):
    log.info("Fig 6: LISA maps Jun 2015 vs Jun 2019 vs Jun 2025...")

    PERIODS  = [(2015, 6, "Jun 2015"), (2019, 6, "Jun 2019"), (2025, 6, "Jun 2025")]
    STATUSES = [2, 3]   # located_alive, located_dead
    # Layout: rows = status, cols = year

    fig, axes = plt.subplots(2, 3, figsize=(18, 10))

    for row, sid in enumerate(STATUSES):
        for col, (y, m, period_label) in enumerate(PERIODS):
            ax = axes[row][col]
            sub = (
                lisa.filter(
                    (pl.col("status_id") == sid) &
                    (pl.col("year") == y) &
                    (pl.col("month") == m) &
                    (pl.col("sex") == "total")
                )
                .select(["cvegeo", "cluster_label"])
                .to_pandas()
                .set_index("cvegeo")
            )
            gdf_m = gdf.join(sub, how="left")
            gdf_m["cluster_label"] = gdf_m["cluster_label"].fillna("NS")
            title = f"{STATUS_LABELS[sid]}\n{period_label}"
            plot_lisa_map(ax, gdf_m, title)

    make_lisa_legend(axes[1][2], loc="lower left")

    fig.suptitle("LISA Cluster Maps: Located Alive vs. Located Dead\nJune 2015 vs. June 2019 vs. June 2025 (total sex, α = 0.05)",
                 fontsize=13, y=1.00)
    plt.tight_layout()
    save_fig(fig, "fig6_lisa_maps_2015_2019_2025", is_map=True)


# ---------------------------------------------------------------------------
# FIGURE 7: Male vs female LISA maps — Not Located + Located Dead (Jun 2025)
# ---------------------------------------------------------------------------
def make_fig7(lisa: pl.DataFrame, gdf: gpd.GeoDataFrame):
    log.info("Fig 7: Male vs female LISA maps Jun 2025...")

    SEX_CATS = ["male", "female"]
    STATUSES = [7, 3]   # not_located, located_dead
    # Layout: rows = status, cols = sex

    fig, axes = plt.subplots(2, 2, figsize=(14, 10))

    for row, sid in enumerate(STATUSES):
        for col, sx in enumerate(SEX_CATS):
            ax = axes[row][col]
            sub = (
                lisa.filter(
                    (pl.col("status_id") == sid) &
                    (pl.col("year") == 2025) &
                    (pl.col("month") == 6) &
                    (pl.col("sex") == sx)
                )
                .select(["cvegeo", "cluster_label"])
                .to_pandas()
                .set_index("cvegeo")
            )
            gdf_m = gdf.join(sub, how="left")
            gdf_m["cluster_label"] = gdf_m["cluster_label"].fillna("NS")
            title = f"{STATUS_LABELS[sid]} — {sx.capitalize()}"
            plot_lisa_map(ax, gdf_m, title)

    make_lisa_legend(axes[1][1], loc="lower left")

    fig.suptitle("LISA Cluster Maps by Sex: Not Located vs. Located Dead\nJune 2025 (α = 0.05)",
                 fontsize=13, y=1.00)
    plt.tight_layout()
    save_fig(fig, "fig7_sex_disaggregation_maps", is_map=True)


# ---------------------------------------------------------------------------
# FIGURE 8: Regional HH heatmap — 11 June snapshots × 4 statuses
# ---------------------------------------------------------------------------
def make_fig8(lisa: pl.DataFrame, muni_meta: pl.DataFrame):
    log.info("Fig 8: Regional HH heatmap...")

    # Load new 29-municipality Bajío corridor (Medina-Fernández et al. 2023)
    bajio_csv = pl.read_csv(
        DATA_EXT / "bajio_corridor_municipalities.csv",
        schema_overrides={"cvegeo": pl.Utf8},
    )
    bajio_cvs = set(bajio_csv["cvegeo"].str.zfill(5).to_list())

    REGIONS_ORDER = ["Norte", "Norte-Occidente", "Centro-Norte", "Centro", "Sur", "Bajío"]
    YEARS = list(range(2015, 2026))

    # Get HH municipalities per (year, region, status), June only
    hh_june = (
        lisa.filter(
            (pl.col("sex") == "total") &
            (pl.col("cluster_label") == "HH") &
            (pl.col("month") == 6)
        )
        .select(["status_id", "year", "cvegeo"])
        .join(muni_meta, on="cvegeo", how="left")
    )

    def count_hh(sub, region):
        if region == "Bajío":
            return sub.filter(pl.col("cvegeo").is_in(list(bajio_cvs)))
        return sub.filter(pl.col("region") == region)

    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    axes = axes.flatten()

    for i, sid in enumerate(STATUS_IDS):
        ax = axes[i]
        sub_sid = hh_june.filter(pl.col("status_id") == sid)

        # Build matrix: rows=regions, cols=years
        matrix = np.zeros((len(REGIONS_ORDER), len(YEARS)), dtype=int)
        for ri, reg in enumerate(REGIONS_ORDER):
            for ci, yr in enumerate(YEARS):
                sub_yr = sub_sid.filter(pl.col("year") == yr)
                matrix[ri, ci] = len(count_hh(sub_yr, reg))

        im = ax.imshow(matrix, aspect="auto", cmap="YlOrRd", interpolation="nearest")

        # Annotate cells
        for ri in range(len(REGIONS_ORDER)):
            for ci in range(len(YEARS)):
                val = matrix[ri, ci]
                color = "white" if val > matrix.max() * 0.6 else "black"
                ax.text(ci, ri, str(val), ha="center", va="center",
                        fontsize=7, color=color, fontweight="bold")

        ax.set_xticks(range(len(YEARS)))
        ax.set_xticklabels(YEARS, rotation=45, fontsize=8)
        ax.set_yticks(range(len(REGIONS_ORDER)))
        ax.set_yticklabels(REGIONS_ORDER, fontsize=9)
        ax.set_title(STATUS_LABELS[sid], color=STATUS_COLORS[sid], fontweight="bold")

        # Chi-squared bookend test (Jun 2015 vs Jun 2025, 5 standard regions)
        regs_std = ["Norte", "Norte-Occidente", "Centro-Norte", "Centro", "Sur"]
        obs_2015 = [matrix[REGIONS_ORDER.index(r), 0] for r in regs_std]
        obs_2025 = [matrix[REGIONS_ORDER.index(r), -1] for r in regs_std]
        contingency = np.array([obs_2015, obs_2025])
        if contingency.sum() >= 10 and (contingency > 0).sum() >= 4:
            try:
                chi2, p, _, _ = stats.chi2_contingency(contingency)
                p_str = f"p<0.001" if p < 0.001 else f"p={p:.3f}"
                ax.set_xlabel(f"χ² 2015 vs 2025: {chi2:.1f}, {p_str}", fontsize=8)
            except Exception:
                pass

    fig.suptitle(
        "High-High Municipalities by Region: June Snapshots 2015–2025\n"
        "(cell value = number of HH municipalities)",
        fontsize=13
    )
    plt.tight_layout()
    save_fig(fig, "fig8_regional_hh_heatmap", is_map=False)


# ---------------------------------------------------------------------------
# FIGURE 9: CED state-level HH small-multiples (8 panels, 3 status lines)
# ---------------------------------------------------------------------------
def make_fig9_ced_states():
    log.info("Fig 9: CED state-level HH trajectories...")

    ced = pd.read_csv(DATA_PROC / "ced_state_hh_timeseries.csv")

    # 8 CED states in display order (2×4 grid)
    CED_STATES = [
        "Jalisco", "Guanajuato", "Coahuila", "Veracruz",
        "Nayarit", "Tabasco", "Nuevo Leon", "Estado de Mexico",
    ]

    # Shaded CED claim periods (clipped to data start Jan 2015)
    CED_WINDOWS = {
        "Jalisco":          (2015, 1, 2025, 6),
        "Guanajuato":       (2017, 1, 2025, 6),
        "Coahuila":         (2015, 1, 2016, 12),
        "Veracruz":         (2015, 1, 2016, 12),
        "Nayarit":          (2015, 1, 2017, 12),
        "Tabasco":          (2024, 1, 2025, 6),
        "Nuevo Leon":       (2015, 1, 2025, 6),
        "Estado de Mexico": (2015, 1, 2025, 6),
    }

    # Three statuses only — no Total (0)
    PLOT_SIDS = [7, 2, 3]

    # Full monthly grid 2015-01 to 2025-06
    all_ym = pd.DataFrame(
        [(y, m) for y in range(2015, 2026) for m in range(1, 13)
         if not (y == 2025 and m > 6)],
        columns=["year", "month"],
    )

    fig, axes = plt.subplots(2, 4, figsize=(18, 8), sharex=True)
    axes = axes.flatten()

    for i, state in enumerate(CED_STATES):
        ax = axes[i]

        # Shade CED temporal window
        if state in CED_WINDOWS:
            y0, m0, y1, m1 = CED_WINDOWS[state]
            ax.axvspan(
                pd.Timestamp(y0, m0, 1),
                pd.Timestamp(y1, m1, 1),
                color="#f0e68c", alpha=0.3, zorder=0,
            )

        for sid in PLOT_SIDS:
            sub = ced[(ced["state"] == state) & (ced["status_id"] == sid)][
                ["year", "month", "n_hh_munis"]
            ]
            merged = all_ym.merge(sub, on=["year", "month"], how="left").fillna(0)
            merged["n_hh_munis"] = merged["n_hh_munis"].astype(int)
            dates = ym_to_date(merged["year"], merged["month"])
            ax.plot(
                dates, merged["n_hh_munis"],
                color=STATUS_COLORS[sid],
                linewidth=1.4,
                label=STATUS_LABELS[sid],
                alpha=0.9,
            )

        ax.set_title(state, fontweight="bold", fontsize=11)
        ax.set_ylabel("HH municipalities" if i % 4 == 0 else "")
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
        ax.xaxis.set_major_locator(mdates.YearLocator(2))
        ax.tick_params(axis="x", rotation=45)
        ax.grid(True, alpha=0.3, linestyle="--")
        ax.spines[["top", "right"]].set_visible(False)
        if i == 0:
            ax.legend(loc="upper left", fontsize=7)

    fig.suptitle(
        "High-High Cluster Municipalities: CED-Named States\n"
        "(shaded = CED claim period; total sex, \u03b1 = 0.05)",
        fontsize=13,
    )
    plt.tight_layout()
    save_fig(fig, "fig9_ced_states", is_map=False)


# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------
def main():
    log.info("=== Phase 3: Figure generation ===")

    # --- Load data ---
    log.info("Loading panel_monthly_counts.parquet...")
    panel = pl.read_parquet(DATA_PROC / "panel_monthly_counts.parquet")

    log.info("Loading concentration_monthly.csv...")
    conc  = pl.read_csv(DATA_PROC / "concentration_monthly.csv")

    log.info("Loading morans_i_monthly.csv...")
    moran = pl.read_csv(DATA_PROC / "morans_i_monthly.csv")

    log.info("Loading lisa_monthly_results.parquet...")
    lisa  = pl.read_parquet(DATA_PROC / "lisa_monthly_results.parquet")

    # Municipality metadata from panel
    muni_meta = panel.select(["cvegeo", "region", "is_bajio"]).unique("cvegeo")

    # --- Load and prepare geometry ---
    log.info("Loading municipality geometry...")
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        gdf = gpd.read_parquet((DATA_EXT / "municipios_2024.geoparquet").resolve())

    if gdf.crs is None or gdf.crs.to_epsg() != 6372:
        gdf = gdf.to_crs(epsg=6372)

    # Standardise cvegeo column name
    cve_col = next((c for c in gdf.columns if "cve_geo" in c.lower() or "cvegeo" in c.lower()), None)
    if cve_col is None:
        raise ValueError(f"No cvegeo column found in geometry. Columns: {gdf.columns.tolist()}")
    gdf["cvegeo"] = gdf[cve_col].astype(str).str.zfill(5)
    gdf = gdf.set_index("cvegeo")

    # Simplify for maps
    log.info(f"Simplifying geometry (tolerance={GEO_TOLERANCE} m)...")
    gdf_map = gdf.copy()
    gdf_map["geometry"] = gdf_map["geometry"].simplify(GEO_TOLERANCE, preserve_topology=True)
    # Keep only geometry column for mapping
    gdf_map = gdf_map[["geometry"]]

    # --- Generate figures ---
    make_fig1(panel)
    make_fig2(conc)
    make_fig3(moran)
    make_fig4(lisa, gdf_map)
    make_fig5(lisa, muni_meta)
    make_fig6(lisa, gdf_map)
    make_fig7(lisa, gdf_map)
    make_fig8(lisa, muni_meta)
    make_fig9_ced_states()

    log.info("=== Phase 3 complete. All 9 figures saved to manuscript/figures/ ===")

    # List outputs
    for f in sorted(OUT_DIR.glob("fig*.pdf")):
        png = f.with_suffix(".png")
        pdf_kb = f.stat().st_size // 1024
        png_kb = png.stat().st_size // 1024 if png.exists() else 0
        log.info(f"  {f.name}: {pdf_kb} KB PDF + {png_kb} KB PNG")


if __name__ == "__main__":
    main()
