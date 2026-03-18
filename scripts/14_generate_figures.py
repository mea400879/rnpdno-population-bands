"""Phase 3 — Publication figures (8 figures).

Outputs (PDF + PNG) in manuscript/figures/:
  fig1_time_series_by_status   — monthly national counts, 4-panel by status, sex-disaggregated
  fig2_gini_time_series        — Gini coefficient over time, 4 statuses
  fig3_lorenz_curves           — Lorenz curves, 4 statuses × 3 time points
  fig4_morans_i_time_series    — Global Moran's I over time, 4 statuses
  fig5_lisa_maps_latest        — LISA maps 2025-12, 2×2 grid by status
  fig6_hh_trend_norte_bajio    — HH municipalities over time, Norte vs Bajío, 4-panel
  fig7_lisa_maps_2015_vs_2024  — LISA maps 2015-12 vs 2024-12, Located Alive + Dead
  fig8_sex_disaggregation_maps — Male vs female LISA maps 2025-12, Not Located + Located Dead

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
    "LL": "#2980b9",   # blue
    "HL": "#f39c12",   # orange
    "LH": "#85c1e9",   # light blue
    "NS": "#e8e8e8",   # light gray
}
LISA_ORDER  = ["HH", "LL", "HL", "LH", "NS"]
LISA_LABELS = {"HH": "High-High", "LL": "Low-Low", "HL": "High-Low", "LH": "Low-High", "NS": "Not Sig."}

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


def lorenz_xy(counts: np.ndarray):
    """Compute Lorenz curve (x, y) where x=cum. share of munis, y=cum. share of cases."""
    v = np.sort(counts[counts >= 0].astype(float))
    n = len(v)
    cum = np.concatenate([[0.0], np.cumsum(v)])
    total = cum[-1]
    x = np.arange(n + 1) / n
    y = cum / total if total > 0 else cum
    return x, y


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
# FIGURE 2: Gini time series
# ---------------------------------------------------------------------------
def make_fig2(conc: pl.DataFrame):
    log.info("Fig 2: Gini time series...")

    df = conc.to_pandas()
    fig, ax = plt.subplots(figsize=(12, 5))

    for sid in STATUS_IDS:
        sub = df[df["status_id"] == sid].sort_values(["year", "month"])
        dates = ym_to_date(sub["year"], sub["month"])
        ax.plot(dates, sub["gini"], color=STATUS_COLORS[sid],
                linewidth=1.6, label=STATUS_LABELS[sid], alpha=0.9)

    ax.set_ylabel("Gini Coefficient")
    ax.set_xlabel("")
    ax.set_title("Geographic Concentration (Gini) by Outcome Status, 2015–2025")
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    ax.xaxis.set_major_locator(mdates.YearLocator(1))
    ax.tick_params(axis="x", rotation=45)
    ax.set_ylim(0.85, 1.0)
    ax.legend(loc="lower right")
    ax.grid(True, alpha=0.3, linestyle="--")
    ax.spines[["top", "right"]].set_visible(False)
    plt.tight_layout()
    save_fig(fig, "fig2_gini_time_series", is_map=False)


# ---------------------------------------------------------------------------
# FIGURE 3: Lorenz curves
# ---------------------------------------------------------------------------
def make_fig3(panel: pl.DataFrame):
    log.info("Fig 3: Lorenz curves...")

    TIME_POINTS = [(2015, 1, "Jan 2015"), (2020, 1, "Jan 2020"), (2025, 12, "Dec 2025")]
    TP_COLORS   = ["#2c3e50", "#8e44ad", "#e67e22"]
    TP_STYLES   = ["-", "--", ":"]

    fig, axes = plt.subplots(2, 2, figsize=(12, 10))
    axes = axes.flatten()

    for i, sid in enumerate(STATUS_IDS):
        ax = axes[i]
        for (y, m, label), color, ls in zip(TIME_POINTS, TP_COLORS, TP_STYLES):
            sub = (
                panel.filter(
                    (pl.col("status_id") == sid) &
                    (pl.col("year") == y) &
                    (pl.col("month") == m)
                )
                .select("total")
                .to_series()
                .to_numpy()
            )
            if sub.sum() == 0:
                continue
            x, yc = lorenz_xy(sub)
            ax.plot(x, yc, color=color, linestyle=ls, linewidth=1.8, label=label)

        # Perfect equality diagonal
        ax.plot([0, 1], [0, 1], color="#bdc3c7", linestyle="--", linewidth=1, label="Perfect equality")

        ax.set_title(STATUS_LABELS[sid], color=STATUS_COLORS[sid], fontweight="bold")
        ax.set_xlabel("Cumulative share of municipalities")
        ax.set_ylabel("Cumulative share of cases")
        ax.set_xlim(0, 1); ax.set_ylim(0, 1)
        ax.set_aspect("equal")
        ax.grid(True, alpha=0.3, linestyle="--")
        ax.spines[["top", "right"]].set_visible(False)
        if i == 0:
            ax.legend(loc="upper left", fontsize=8)

    fig.suptitle("Lorenz Curves of Case Distribution by Outcome Status\nSelected Time Points",
                 fontsize=13)
    plt.tight_layout()
    save_fig(fig, "fig3_lorenz_curves", is_map=False)


# ---------------------------------------------------------------------------
# FIGURE 4: Global Moran's I time series
# ---------------------------------------------------------------------------
def make_fig4(moran: pl.DataFrame):
    log.info("Fig 4: Moran's I time series...")

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
    save_fig(fig, "fig4_morans_i_time_series", is_map=False)


# ---------------------------------------------------------------------------
# FIGURE 5: LISA maps — latest period (2025-12), 4 statuses
# ---------------------------------------------------------------------------
def make_fig5(lisa: pl.DataFrame, gdf: gpd.GeoDataFrame):
    log.info("Fig 5: LISA maps 2025-12...")

    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    axes = axes.flatten()

    for i, sid in enumerate(STATUS_IDS):
        sub = (
            lisa.filter(
                (pl.col("status_id") == sid) &
                (pl.col("year") == 2025) &
                (pl.col("month") == 12) &
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

    fig.suptitle("Local Spatial Autocorrelation (LISA) by Outcome Status\nDecember 2025 (total sex, α = 0.05)",
                 fontsize=13, y=1.00)
    plt.tight_layout()
    save_fig(fig, "fig5_lisa_maps_latest", is_map=True)


# ---------------------------------------------------------------------------
# FIGURE 6: HH trend Norte vs Bajío, 4-panel by status
# ---------------------------------------------------------------------------
def make_fig6(lisa: pl.DataFrame, muni_meta: pl.DataFrame):
    log.info("Fig 6: HH trend Norte vs Bajío...")

    hh_total = (
        lisa.filter(
            (pl.col("sex") == "total") &
            (pl.col("cluster_label") == "HH")
        )
        .select(["status_id", "year", "month", "cvegeo"])
        .join(muni_meta, on="cvegeo", how="left")
    )

    fig, axes = plt.subplots(2, 2, figsize=(14, 10), sharex=True)
    axes = axes.flatten()

    for i, sid in enumerate(STATUS_IDS):
        ax = axes[i]
        sub = hh_total.filter(pl.col("status_id") == sid)

        norte = (
            sub.filter(pl.col("region") == "Norte")
            .group_by(["year", "month"])
            .agg(pl.len().alias("n"))
            .sort(["year", "month"])
            .to_pandas()
        )
        bajio = (
            sub.filter(pl.col("is_bajio") == True)
            .group_by(["year", "month"])
            .agg(pl.len().alias("n"))
            .sort(["year", "month"])
            .to_pandas()
        )

        for df_reg, label, color, ls in [
            (norte, "Norte",  "#c0392b", "-"),
            (bajio, "Bajío",  "#f39c12", "--"),
        ]:
            if len(df_reg) == 0:
                continue
            dates = ym_to_date(df_reg["year"], df_reg["month"])
            y     = df_reg["n"].values
            ax.plot(dates, y, color=color, linestyle=ls, linewidth=1.8, label=label, alpha=0.9)
            # OLS trend line
            if len(y) >= 6:
                sl = ols_trend(y)
                x_num = np.arange(len(y))
                trend = sl.intercept + sl.slope * x_num
                ax.plot(dates, trend, color=color, linestyle=":", linewidth=1.0, alpha=0.6)

        ax.set_title(STATUS_LABELS[sid], color=STATUS_COLORS[sid], fontweight="bold")
        ax.set_ylabel("HH municipalities")
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
        ax.xaxis.set_major_locator(mdates.YearLocator(2))
        ax.tick_params(axis="x", rotation=45)
        ax.grid(True, alpha=0.3, linestyle="--")
        ax.spines[["top", "right"]].set_visible(False)
        if i == 0:
            ax.legend(loc="upper left")

    fig.suptitle("High-High Cluster Municipalities Over Time: Norte vs. Bajío\n(dotted lines = OLS trend)",
                 fontsize=13)
    plt.tight_layout()
    save_fig(fig, "fig6_hh_trend_norte_bajio", is_map=False)


# ---------------------------------------------------------------------------
# FIGURE 7: LISA maps 2015-12 vs 2024-12 — Located Alive + Located Dead
# ---------------------------------------------------------------------------
def make_fig7(lisa: pl.DataFrame, gdf: gpd.GeoDataFrame):
    log.info("Fig 7: LISA maps 2015-12 vs 2024-12...")

    PERIODS  = [(2015, 12, "Dec 2015"), (2025, 12, "Dec 2025")]
    STATUSES = [2, 3]   # located_alive, located_dead
    # Layout: rows = status, cols = year

    fig, axes = plt.subplots(2, 2, figsize=(14, 10))

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

    make_lisa_legend(axes[1][1], loc="lower left")

    fig.suptitle("LISA Cluster Maps: Located Alive vs. Located Dead\nDecember 2015 vs. December 2025 (total sex, α = 0.05)",
                 fontsize=13, y=1.00)
    plt.tight_layout()
    save_fig(fig, "fig7_lisa_maps_2015_vs_2024", is_map=True)


# ---------------------------------------------------------------------------
# FIGURE 8: Male vs female LISA maps — Not Located + Located Dead (2025-12)
# ---------------------------------------------------------------------------
def make_fig8(lisa: pl.DataFrame, gdf: gpd.GeoDataFrame):
    log.info("Fig 8: Male vs female LISA maps 2025-12...")

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
                    (pl.col("month") == 12) &
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

    fig.suptitle("LISA Cluster Maps by Sex: Not Located vs. Located Dead\nDecember 2025 (α = 0.05)",
                 fontsize=13, y=1.00)
    plt.tight_layout()
    save_fig(fig, "fig8_sex_disaggregation_maps", is_map=True)


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
    make_fig3(panel)
    make_fig4(moran)
    make_fig5(lisa, gdf_map)
    make_fig6(lisa, muni_meta)
    make_fig7(lisa, gdf_map)
    make_fig8(lisa, gdf_map)

    log.info("=== Phase 3 complete. All 8 figures saved to manuscript/figures/ ===")

    # List outputs
    for f in sorted(OUT_DIR.glob("fig*.pdf")):
        png = f.with_suffix(".png")
        pdf_kb = f.stat().st_size // 1024
        png_kb = png.stat().st_size // 1024 if png.exists() else 0
        log.info(f"  {f.name}: {pdf_kb} KB PDF + {png_kb} KB PNG")


if __name__ == "__main__":
    main()
